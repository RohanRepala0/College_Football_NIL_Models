import pytest

from nilmodel import csc, dashboard

REAL = sorted(csc.ARCHIVE_DIR.glob("*_2026-10-30_*.json.gz"))


@pytest.mark.skipif(len(REAL) != 2, reason="the 2026-10-30 releases are not on disk")
def test_dashboard_files_from_the_first_release(con):
    csc.ingest_archive(con, csc.ARCHIVE_DIR)
    data = dashboard.build(con)
    assert {k: len(v) for k, v in data.items()} == {"cohorts": 246, "curves": 195, "validation": 15, "releases": 2}
    ids = [r["id"] for r in data["cohorts"]]
    assert len(set(ids)) == len(ids)                                    # the dashboard's row key
    qb = next(r for r in data["cohorts"] if r["id"] == "revenue_share|men|Football|Quarterback|A4|paid")
    assert (qb["p50"], qb["n"], qb["population_label"]) == (230000.0, 257, "Paid athletes")
    everyone = next(c for c in data["curves"] if c["id"] == "revenue_share|men|Football|Quarterback|A4|all_rostered")
    assert len(everyone["values"]) == 99 and everyone["values"][19] == 0          # 20th percentile: unpaid
    assert everyone["zero_pct"] == pytest.approx(100 * (1 - 257 / 367), abs=0.01)
    assert everyone["values"][49] == pytest.approx(75000)                          # the published median
