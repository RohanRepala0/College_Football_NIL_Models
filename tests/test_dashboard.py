import pytest

from nilmodel import csc, dashboard

REAL = sorted(csc.ARCHIVE_DIR.glob("*_2026-10-30_*.json.gz"))


@pytest.mark.skipif(len(REAL) != 2, reason="the 2026-10-30 releases are not on disk")
def test_dashboard_files_from_the_first_release(con):
    csc.ingest_archive(con, csc.ARCHIVE_DIR)
    data = dashboard.build(con)
    counts = {k: len(v) for k, v in data.items() if k not in ("rosters", "season_games", "nil_flow")}  # other inputs
    if "nil_flow" in data:                                                # from data/csc/nil_data_periods.csv
        assert all(r["cleared_value"] > 0 and r["months"] > 0 for r in data["nil_flow"])
    releases = len(list(csc.ARCHIVE_DIR.glob("*.json.gz")))              # every release archived so far
    assert counts == {"cohorts": 246, "curves": 195, "validation": 15, "releases": releases, "totals": 1}
    t = data["totals"][0]
    assert t["floor_per_program"] == pytest.approx(11.7e6, rel=0.01) and t["floor_cap_share"] == pytest.approx(0.557, abs=0.005)
    assert t["qb_p90"] == 1611000 and t["qb_p99_fitted"] > t["qb_p99_calibrated"] > t["qb_p90"]
    ids = [r["id"] for r in data["cohorts"]]
    assert len(set(ids)) == len(ids)                                    # the dashboard's row key
    qb = next(r for r in data["cohorts"] if r["id"] == "revenue_share|men|Football|Quarterback|A4|paid")
    assert (qb["p50"], qb["n"], qb["population_label"]) == (230000.0, 257, "Paid athletes")
    everyone = next(c for c in data["curves"] if c["id"] == "revenue_share|men|Football|Quarterback|A4|all_rostered")
    assert len(everyone["values"]) == 99 and everyone["values"][19] == 0          # 20th percentile: unpaid
    assert everyone["zero_pct"] == pytest.approx(100 * (1 - 257 / 367), abs=0.01)
    assert everyone["values"][49] == pytest.approx(75000)                          # the published median
