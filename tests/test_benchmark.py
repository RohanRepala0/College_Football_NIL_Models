import numpy as np
import pandas as pd
import pytest

from nilmodel import benchmark as bm
from nilmodel import csc


def _rows(report, sport, position, cohort, population, n, values, gender="men"):
    return [{"report": report, "payload_sha256": "sha", "gender": gender, "sport": sport, "position": position,
             "cohort": cohort, "a4": cohort == "A4", "population": population, "n": n, "n_text": None,
             "percentile": p, "value_usd": v, "min_n": None, "window_start": None, "window_end": None, "as_of": None,
             "window_label": "window", "source_ref": "test"} for p, v in zip(csc.PERCENTILES, values)]


# Real values from the 2026-10-30 release (p90, p75, p50, p25, p10).
QB = pd.DataFrame(_rows("revenue_share", "Football", "Quarterback", "A4", "all_rostered", 367,
                        [1266500, 350000, 75000, 0, 0])
                  + _rows("revenue_share", "Football", "Quarterback", "A4", "paid", 257,
                          [1611000, 675000, 230000, 60000, 23500]))
RB_NIL = pd.DataFrame(_rows("nil_go", "Football", "Running Back", "Non-A4", "deal_holders", 137,
                            [7508, 1600, 1500, 1500, 1500]))
PUNTER = pd.DataFrame(_rows("revenue_share", "Football", "Punter", "Non-A4", "paid", 47,
                            [None, None, 10000, None, None]))


def _curve(df, method=bm.METHOD):
    cs, issues = bm.curves(df, method)
    assert issues == [] and len(cs) == 1
    return cs[0]


@pytest.mark.parametrize("method", ["linear", "pchip"])
def test_curve_passes_through_every_published_point(method):
    c = _curve(QB, method)
    qs = np.array([q for q, _, _ in c.knots])
    assert np.allclose(c.quantile(qs), [v for _, v, _ in c.knots], rtol=1e-9)
    grid = c.quantile(np.linspace(0.001, 0.999, 999))
    assert np.all(np.diff(grid) >= 0)


def test_with_zero_table_adds_points_to_the_paid_curve():
    c = _curve(QB)
    z = 1 - 257 / 367
    assert c.zero_share == pytest.approx(z) and c.n_all == 367
    added = [(round(q, 4), v) for q, v, s in c.knots if s == "all_rostered"]
    assert added == [(round((p - z) / (1 - z), 4), v) for p, v in ((0.50, 75000), (0.75, 350000), (0.90, 1266500))]


def test_rank_inverts_quantile():
    c = _curve(QB)
    for q in (0.12, 0.3, 0.5, 0.7, 0.88):
        lo, hi = c.rank(float(c.quantile(q)))
        assert lo == pytest.approx(q, abs=1e-6) and hi == pytest.approx(q, abs=1e-6)


def test_benchmark_reads_both_revenue_share_populations():
    c = _curve(QB)
    paid, everyone = bm.benchmark(c, 400_000)
    assert (paid.population, everyone.population) == ("paid", "all_rostered")
    assert 50 < paid.percentile < 75 and paid.bracket == (50, 75) and not paid.extrapolated
    z = 1 - 257 / 367
    assert everyone.percentile == pytest.approx(100 * z + (1 - z) * paid.percentile)
    assert everyone.bracket == (75, pytest.approx(100 * (z + (1 - z) * 0.75)))
    nothing = bm.benchmark(c, 0)[1]
    assert (nothing.low, nothing.high) == (0, pytest.approx(100 * z)) and nothing.matches == (10, 25)


def test_an_amount_many_athletes_got_is_a_range():
    c = _curve(RB_NIL)
    b = bm.benchmark(c, 1500)[0]
    assert (b.low, b.high) == (pytest.approx(10, abs=0.01), pytest.approx(50, abs=0.01))
    assert b.matches == (10, 25, 50) and b.bracket == (0, 75)
    b = bm.benchmark(c, 1550)[0]
    assert 50 < b.low < 75 and b.high == pytest.approx(b.low)


def test_beyond_the_published_percentiles_is_flagged():
    b = bm.benchmark(_curve(QB), 2_500_000)[0]
    assert b.extrapolated and b.percentile > 90 and b.bracket == (90, 100)


def test_one_published_point_gives_a_bracket_only():
    b = bm.benchmark(_curve(PUNTER), 15_000)[0]
    assert b.percentile is None and b.method == "bracket_only" and b.bracket == (50, 100)


def test_value_at():
    c = _curve(QB)
    assert bm.value_at(c, 20, "all_rostered") == (0.0, False)
    assert bm.value_at(c, 50, "all_rostered")[0] == pytest.approx(75000)
    assert bm.value_at(c, 75, "paid") == (pytest.approx(675000), False)
    assert bm.value_at(c, 95, "paid")[1]


def test_find_asks_rather_than_guesses():
    hoops = pd.DataFrame(_rows("nil_go", "Basketball", "All Positions", "SEC", "deal_holders", 155,
                               [79980, 34850, 10320, 3355, 1235])
                         + _rows("nil_go", "Basketball", "All Positions", "SEC", "deal_holders", 122,
                                 [49575, 18225, 7370, 5000, 1518], gender="women"))
    cs, _ = bm.curves(hoops)
    with pytest.raises(LookupError, match="2 nil_go cohorts"):
        bm.find(cs, "nil_go", "Basketball", cohort="SEC")
    assert bm.find(cs, "nil_go", "basketball", cohort="sec", gender="women").n == 122


def test_validate_holds_out_points():
    errors = bm.validate(QB)
    assert set(errors.method) == set(bm.METHODS)
    assert set(errors.test) == {"loo_interior", "loo_tail", "cross"}
    cross = errors[(errors.test == "cross") & (errors.method == "linear")]
    assert len(cross) == 3 and cross.error.max() < 5


REAL = sorted(csc.ARCHIVE_DIR.glob("*_2026-10-30_*.json.gz"))


@pytest.mark.skipif(len(REAL) != 2, reason="the 2026-10-30 releases are not on disk")
def test_first_real_release(con, tmp_path):
    csc.ingest_archive(con, csc.ARCHIVE_DIR)
    df = con.execute("SELECT * FROM csc_latest").df()
    cs, issues = bm.curves(df)
    assert issues == [] and len(cs) == 192 and sum(c.fitted for c in cs) == 142
    counts = bm.store(con, cs)
    pops = sum(1 + (c.zero_share is not None) for c in cs if c.fitted)
    assert counts == {"benchmark_fits": 192, "benchmark_curves": 99 * pops}
    wide = pd.read_csv(bm.export(con, tmp_path / "curves.csv"))
    assert len(wide) == pops and list(wide.columns[10:12]) == ["p1", "p2"]

    summary = bm.summarize(bm.validate(df)).set_index(["report", "test", "method"])["mean"]
    assert summary["revenue_share", "cross", "linear"] < 2.5              # 1.87 on this release
    assert summary["revenue_share", "loo_interior", "linear"] < 4.5       # 3.38
    assert summary["nil_go", "loo_interior", "linear"] < 9                # 7.36
    for report, test in [("revenue_share", "cross"), ("revenue_share", "loo_interior"), ("nil_go", "loo_interior")]:
        assert summary[report, test, "linear"] < summary[report, test, "lognormal"]
