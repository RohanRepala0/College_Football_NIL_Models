import base64
import copy
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from nilmodel import config, csc, pipeline
from nilmodel.fetch import Snapshot

REAL = sorted(csc.ARCHIVE_DIR.glob("*_2026-10-30_*.json.gz"))
pytestmark = pytest.mark.skipif(len(REAL) != 2, reason="the 2026-10-30 releases are not on disk")


def _script(js: str) -> str:
    return f'<script src="data:text/javascript;base64,{base64.b64encode(js.encode()).decode()}"></script>'


def page(report: str, payload: dict) -> str:
    """A page shaped like the real one: the payload in a base64 data script among others."""
    if report == "nil_go":
        js = f'(function(){{var B64="{base64.b64encode(json.dumps(payload).encode()).decode()}";}})();'
    else:
        js = "(function(){" + "".join(f"const {k}={json.dumps(payload[k])};"
                                      for k in ("TABLE_SVGS", "sportsData", "tablesData")) + "})();"
    return "<html>" + _script("window.dataLayer=[];") + _script(js) + "</html>"


class FakeFetcher:
    def __init__(self, pages: dict[str, str], when: datetime):
        self.pages, self.when = pages, when

    def fetch(self, source, url, fresh=False, ext="txt"):
        return Snapshot(self.pages[url].encode(), self.when, Path("fake"), url)


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    archive = tmp_path / "releases"
    archive.mkdir()
    for p in REAL:
        shutil.copy(p, archive)
    monkeypatch.setattr(config, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(config, "REPORTS_DIR", tmp_path / "reports")
    payloads = {csc.read_archive(p)["report"]: csc.read_archive(p)["payload"] for p in REAL}
    return archive, payloads


def _pages(payloads):
    return {csc.REPORTS[r]: page(r, p) for r, p in payloads.items()}


def test_a_day_with_no_change_writes_nothing(con, workspace):
    archive, payloads = workspace
    when = datetime(2026, 10, 31, 13, 17, tzinfo=timezone.utc)
    out = pipeline.refresh(con, FakeFetcher(_pages(payloads), when), archive)
    assert [r["new"] for r in out["fetched"]] == [False, False]
    assert out["new"] == [] and out["files"] == [] and out["issues"] == []
    assert len(list(archive.glob("*.json.gz"))) == 2
    assert con.execute("SELECT max(last_seen_at) FROM csc_releases").fetchone()[0] == when
    assert con.execute("SELECT count(*) FROM benchmark_fits").fetchone()[0] == 192


def test_a_revision_becomes_a_new_release(con, workspace):
    archive, payloads = workspace
    revised = copy.deepcopy(payloads)
    qb = revised["nil_go"]["sports"][0]["horizons"][0]["bands"][0]["rows"][0]
    assert qb["label"] == "Quarterback"
    qb["values"][2] = 70000.0
    when = datetime(2026, 11, 2, 13, 17, tzinfo=timezone.utc)
    out = pipeline.refresh(con, FakeFetcher(_pages(revised), when), archive)

    assert [r["report"] for r in out["new"]] == ["nil_go"] and out["issues"] == []
    assert len(list(archive.glob("nil_go_2026-11-02_*.json.gz"))) == 1
    assert all(Path(f).exists() for f in out["files"]) and len(out["files"]) == 8
    assert Path(out["files"][2]).name == "release_2026-11-02.md"
    assert [Path(f).name for f in out["files"][3:]] == ["cohorts.json", "curves.json", "validation.json", "releases.json",
                                                     "totals.json"]
    median = """SELECT value_usd FROM benchmark_curves WHERE report = 'nil_go' AND sport = 'Football'
                AND position = 'Quarterback' AND cohort = 'A4' AND percentile = 50"""
    assert con.execute(median).fetchone()[0] == pytest.approx(70000)
    again = pipeline.refresh(con, FakeFetcher(_pages(revised), when + timedelta(days=1)), archive)
    assert again["new"] == [] and again["files"] == []


def test_a_page_without_its_payload_fails_loudly(con, workspace):
    archive, payloads = workspace
    pages = _pages(payloads)
    pages[csc.REPORTS["revenue_share"]] = "<html>" + _script("var nothing=1;") + "</html>"
    with pytest.raises(ValueError, match="layout changed"):
        pipeline.refresh(con, FakeFetcher(pages, datetime(2026, 11, 1, tzinfo=timezone.utc)), archive)
