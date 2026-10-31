"""`nil` command line."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
import typer

from . import benchmark as bm
from . import db, pipeline
from .reports import POPULATIONS, benchmark_rows, ordinal

app = typer.Typer(no_args_is_help=True, help="College Sports Commission compensation data and the offer benchmark.")

COHORT_HELP = "A4, Non-A4, or a conference where the report has one (basketball: ACC, Big Ten, Big 12, SEC)."
GENDER_HELP = "men | women, where the sport has both."


def _con(load: bool = True):
    con = db.connect()
    db.init_db(con)
    if load and con.execute("SELECT count(*) FROM csc_releases").fetchone()[0] == 0:
        pipeline.refresh(con)                   # a fresh checkout: load the archived releases
    return con


def _curves(con) -> list[bm.Curve]:
    return bm.curves(con.execute("SELECT * FROM csc_latest").df())[0]


def _table(rows) -> str:
    return pd.DataFrame(rows).to_markdown(index=False, tablefmt="simple")


@app.command()
def refresh(offline: bool = typer.Option(False, help="Use only the archived releases; no network."),
            export: bool = typer.Option(False, help="Rewrite exports and the report even if nothing is new.")):
    """The pipeline: archived releases, both live pages, checks, benchmark, exports when something is new."""
    from .fetch import Fetcher

    con = _con(load=False)
    out = pipeline.refresh(con, None if offline else Fetcher(con), export=export)
    typer.echo(f"{len(out['archived'])} archived releases loaded")
    for r in out["fetched"]:
        typer.echo(f"{r['report']:14s} release {r['release']}  {'NEW' if r['new'] else 'unchanged'}  "
                   f"{r['cohorts']} cohorts")
    for i in out["issues"]:
        typer.echo(f"{i['severity']}: {i['check']} {i['key']}: {i['detail']}")
    for f in out["files"]:
        typer.echo(f"wrote {f}")
    if any(i["severity"] == "error" for i in out["issues"]):
        raise typer.Exit(1)


@app.command()
def benchmark(sport: str = typer.Option(...), position: str = typer.Option("All Positions"),
              cohort: str = typer.Option("A4", help=COHORT_HELP),
              gender: Optional[str] = typer.Option(None, help=GENDER_HELP),
              revenue_share: Optional[float] = typer.Option(None, help="Revenue-share dollars for the window."),
              nil: Optional[float] = typer.Option(None, help="Total contracted value of third-party NIL deals.")):
    """Where an offer sits in its cohort. Each amount is read against its own report only."""
    if revenue_share is None and nil is None:
        raise typer.BadParameter("give --revenue-share, --nil, or both")
    curves = _curves(_con())
    results, windows = [], []
    for report, amount in (("revenue_share", revenue_share), ("nil_go", nil)):
        if amount is None:
            continue
        try:
            curve = bm.find(curves, report, sport, position, cohort, gender)
        except LookupError as e:
            raise typer.BadParameter(str(e))
        results += bm.benchmark(curve, amount)
        windows.append(f"{report}: {curve.key.window_label}")
    typer.echo(_table(benchmark_rows(results)))
    typer.echo("\n" + "\n".join(windows))
    typer.echo("NIL amounts are full contract value, not annualized. The two reports cover different athletes and "
               "windows, so their percentiles are never combined.")


@app.command()
def curve(sport: str = typer.Option(...), position: str = typer.Option("All Positions"),
          cohort: str = typer.Option("A4", help=COHORT_HELP), gender: Optional[str] = typer.Option(None, help=GENDER_HELP),
          report: str = typer.Option("revenue_share", help="revenue_share | nil_go")):
    """What each percentile pays in a cohort. * = published, ~ = extrapolated."""
    try:
        c = bm.find(_curves(_con()), report, sport, position, cohort, gender)
    except LookupError as e:
        raise typer.BadParameter(str(e))
    pops = [c.population] + (["all_rostered"] if c.zero_share is not None else [])
    rows = []
    for p in (5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 75, 80, 85, 90, 95):
        row = {"percentile": ordinal(p)}
        for pop in pops:
            pub = dict(c.published.get(pop, [])).get(p)
            if c.fitted:
                v, extra = bm.value_at(c, p, pop)
                row[POPULATIONS[pop]] = f"${v:,.0f}{' *' if pub is not None else (' ~' if extra else '')}"
            else:
                row[POPULATIONS[pop]] = "" if pub is None else f"${pub:,.0f} *"
        rows.append(row)
    n = f"n={c.n}" + (f", {c.n_all} rostered, {c.zero_share:.0%} unpaid" if c.zero_share is not None else "")
    typer.echo(f"{c.key.label()} ({n})\n{c.key.window_label}\n")
    typer.echo(_table(rows))


@app.command()
def query(sql: str = typer.Argument(..., help="SQL over csc_latest, csc_percentiles, csc_releases, "
                                              "benchmark_curves, benchmark_fits.")):
    """Run SQL against the store."""
    typer.echo(_table(_con().execute(sql).df()))


@app.command()
def triangulate():
    """What the latest release implies about football totals; writes reports/triangulation_<date>.md."""
    from .reports import triangulation_report

    typer.echo(f"wrote {triangulation_report(_con())}")


@app.command()
def claims(path: Path = typer.Argument(..., help="CSV with the columns of data/claims/template.csv.")):
    """Check reported pay claims against the latest release; writes reports/claims_<file>.md."""
    from .reports import claims_report

    typer.echo(f"wrote {claims_report(_con(), path)}")


@app.command("dashboard-data")
def dashboard_data():
    """Write the dashboard's data files to data/dashboard/ from the latest releases."""
    from .dashboard import export

    for path in export(_con()):
        typer.echo(f"wrote {path} ({path.stat().st_size:,} bytes)")


@app.command()
def status():
    """Releases on file and table sizes."""
    con = _con()
    typer.echo(_table(con.execute("""SELECT report, left(payload_sha256, 12) AS release, first_seen_at, last_seen_at,
                                     n_cohorts FROM csc_releases ORDER BY report, first_seen_at""").df()))
    for t in ("csc_percentiles", "benchmark_fits", "benchmark_curves", "raw_snapshots"):
        typer.echo(f"{t:18s} {con.execute(f'SELECT count(*) FROM {t}').fetchone()[0]:>8}")


if __name__ == "__main__":
    app()
