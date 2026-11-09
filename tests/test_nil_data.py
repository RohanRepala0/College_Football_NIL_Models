from datetime import date, datetime, timezone

import duckdb
import pytest

from nilmodel import nil_data as nd
from nilmodel import triangulate as tri

PAGE = """<html><body><h1>NIL Data Report (September 1 &#8211; October 31, 2026)</h1>
<p>All data below current as of <strong>Nov 1, 2026, at 12:01am Eastern</strong></p>
<div><span>51,368</span> <span>Student-Athlete Users</span></div>
<table><tr><th></th><th>Cleared</th><th>Not Cleared <sup>1</sup></th></tr>
<tr><th></th><th>Deals</th><th>Deal Value</th><th>Deals</th><th>Deal Value</th></tr>
<tr><td>Launch &#8211; Dec. 31, 2025</td><td>17,321</td><td>$127.21M</td><td>524</td><td>$14.94M</td></tr>
<tr><td>Sept. 1 &#8211; Oct. 31, 2026</td><td>10,092</td><td>$192.62M</td><td>581</td><td>$20.21M</td></tr>
<tr><td>Total</td><td>27,413</td><td>$319.83M</td><td>1,105</td><td>$35.15M</td></tr></table>
<table><tr><th></th><th>Cleared: Associated</th><th>Cleared: Non-Associated <sup>2</sup></th></tr>
<tr><th></th><th>Deals</th><th>Deal Value</th><th>Deals</th><th>Deal Value</th></tr>
<tr><td>Sept. 1 &#8211; Oct. 31, 2026</td><td>6,599</td><td>$140.53M</td><td>3,493</td><td>$52.09M</td></tr></table>
</body></html>"""


def test_parse_report_reads_both_tables():
    r = nd.parse_report(PAGE)
    assert r["as_of"] == "2026-11-01" and r["users"] == {"student_athletes": 51368}
    assert [p["start"] for p in r["periods"]] == ["2025-06-11", "2026-09-01"]        # launch, then Sep 1; no total row
    sep = r["periods"][1]
    assert (sep["cleared_deals"], sep["cleared_value"], sep["not_cleared_value"]) == (10092, 192.62e6, 20.21e6)
    assert (sep["associated_value"], sep["non_associated_deals"]) == (140.53e6, 3493)


def test_period_dates_and_money():
    assert nd.period_dates("Mar. 1 – April 30, 2026") == (date(2026, 3, 1), date(2026, 4, 30))
    assert nd.period_dates("Nov. 1 – Jan. 31, 2026") == (date(2025, 11, 1), date(2026, 1, 31))
    assert nd.period_dates("Launch – Dec. 31, 2025") == (nd.LAUNCH, date(2025, 12, 31))
    assert (nd.money("$1.2B"), nd.money("$950K"), nd.money("$127.21M")) == (1.2e9, 950e3, 127.21e6)


def test_store_versions_content_and_latest_periods(tmp_path):
    con = duckdb.connect()
    url = "https://www.collegesportscommission.org/nil-data-report/test/"
    when = datetime(2026, 11, 9, tzinfo=timezone.utc)
    first = nd.store(con, url, nd.parse_report(PAGE), when, tmp_path)
    again = nd.store(con, url, nd.parse_report(PAGE), when, tmp_path)
    assert first["new"] and not again["new"] and len(list(tmp_path.glob("*.json.gz"))) == 1
    revised = nd.parse_report(PAGE.replace("$192.62M", "$193.00M"))
    assert nd.store(con, url, revised, when, tmp_path)["new"] and len(list(tmp_path.glob("*.json.gz"))) == 2


def test_nil_go_cleared_prorates_a_straddling_period(tmp_path):
    csv = tmp_path / "periods.csv"
    csv.write_text("period,period_start,period_end,cleared_value,as_of\n"
                   "Jul-Aug,2026-07-01,2026-08-31,227250000,2026-11-01\n"
                   "Sep-Oct,2026-09-01,2026-10-31,192620000,2026-11-01\n")
    total, note = tri.nil_go_cleared(date(2026, 1, 1), date(2026, 9, 30), csv)
    assert total == pytest.approx(227.25e6 + 192.62e6 * 30 / 61)
    assert "30 of the 61 days" in note
