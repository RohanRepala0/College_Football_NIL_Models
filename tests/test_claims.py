import numpy as np
import pandas as pd
import pytest

from nilmodel import benchmark as bm
from nilmodel import claims as cl
from nilmodel import csc

REAL = sorted(csc.ARCHIVE_DIR.glob("*_2026-10-30_*.json.gz"))
pytestmark = pytest.mark.skipif(len(REAL) != 2, reason="the 2026-10-30 releases are not on disk")


@pytest.fixture
def release(con):
    csc.ingest_archive(con, csc.ARCHIVE_DIR)
    df = con.execute("SELECT * FROM csc_latest").df()
    return df, bm.curves(df)[0]


def _claims(rows):
    base = {"claim_id": "", "player": "", "school": "", "sport": "Football", "gender": "men", "position": "Quarterback",
            "cohort": "A4", "report": "revenue_share", "amount": 0, "years": "", "source_type": "reporter",
            "source": "outlet", "url": "", "date": ""}
    df = pd.DataFrame([{**base, **r} for r in rows]).astype({"amount": str, "years": str})
    return cl.clean(df)


def test_placement_and_packages(release):
    df, curves = release
    claims, issues = _claims([
        {"claim_id": "a", "player": "QB One", "amount": 2_000_000},
        {"claim_id": "b", "player": "QB Two", "amount": 3_000_000, "years": 2},       # $1.5M a year
        {"claim_id": "c", "player": "QB Three", "amount": 4_000_000, "report": "package"},
        {"claim_id": "d", "amount": "", "player": "QB Four"},
    ])
    assert [i["claim_id"] for i in issues] == ["d"]
    placed = cl.place(claims, curves).set_index("claim_id")
    assert placed.loc["a", "pct_low"] > 90 and placed.loc["a", "extrapolated"]
    assert placed.loc["b", "value"] == 1_500_000 and 75 < placed.loc["b", "pct_low"] < 90
    assert not placed.loc["c", "placed"] and placed.loc["c", "why"].startswith("package")


def test_tail_count_proves_a_minimum_number_of_overstatements(release):
    df, curves = release
    # 40 different A4 quarterbacks all claimed above the published 90th ($1,611,000 among 257 paid)
    claims, _ = _claims([{"claim_id": f"q{i}", "player": f"QB {i}", "amount": 1_700_000 + 10_000 * i} for i in range(40)])
    counts = cl.tail_counts(cl.place(claims, curves), df).set_index("percentile")
    assert counts.loc[90, "most_possible"] == 27 and counts.loc[90, "claimed_above"] == 40
    assert counts.loc[90, "excess"] == 13 and counts.loc[50, "excess"] == 0


def test_order_test_flags_the_impossible_not_the_plausible(release):
    df, curves = release
    claims, _ = _claims([{"claim_id": "big", "player": "QB X", "amount": 50_000_000},
                         {"claim_id": "ok", "player": "QB Y", "amount": 700_000}])
    tails = cl.lenient_tails(df)
    assert 0.5 < tails["revenue_share"] < 1 and 0.5 < tails["nil_go"] < 1
    o = cl.order_test(cl.place(claims, curves), curves, tails).set_index("claim_id")
    assert o.loc["big", "flagged"] and not o.loc["ok", "flagged"]
    assert not cl.order_test(cl.place(claims, curves), curves, {"revenue_share": 1.5}).set_index("claim_id").loc["big", "flagged"]


def test_truth_discovery_recovers_source_bias():
    rng = np.random.default_rng(0)
    truth = np.exp(rng.normal(13, 1, 30))
    rows = []
    for i, t in enumerate(truth):
        rows.append({"claim_id": f"r{i}", "player": f"P{i}", "amount": t * 1.3 * np.exp(rng.normal(0, 0.05)),
                     "source": "inflating_outlet"})
        rows.append({"claim_id": f"s{i}", "player": f"P{i}", "amount": t * np.exp(rng.normal(0, 0.05)),
                     "source": "school_docs", "source_type": "school_record"})
        if i % 2:
            rows.append({"claim_id": f"t{i}", "player": f"P{i}", "amount": t * 0.9 * np.exp(rng.normal(0, 0.05)),
                         "source": "agent_leaks", "source_type": "agent"})
    claims, _ = _claims(rows)
    bias = cl.source_bias(claims).set_index("source").bias
    assert bias["school_docs"] == pytest.approx(0, abs=0.01)
    assert bias["inflating_outlet"] == pytest.approx(0.30, abs=0.04)
    assert bias["agent_leaks"] == pytest.approx(-0.10, abs=0.04)
