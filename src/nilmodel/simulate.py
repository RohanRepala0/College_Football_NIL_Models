"""A synthetic A4 football market with known pay, built on the real CSC curves, to test the methods.

Real individual pay is private, so the methods are validated where the truth is known. Each simulated
market has the CSC's A4 roster counts by position, spread over the 68 programs. A player's latent value
is talent + his school's spending effect + noise, and his true revenue share is his position's quantile
at that value's rank. Every position therefore reproduces the published percentiles, with the tail
calibrated to the cap. The analyst sees only what the real world offers: two noisy features (stand-ins
for recruiting rating and production), a few schools' disclosed totals, and claims from sources with
known biases.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from . import benchmark as bm
from . import claims as cl
from . import extend as ex
from . import triangulate as tri

FEATURES = ["f_rating", "f_production"]
# source: (source type, log bias, log noise, how many of the best-paid players it reports)
SOURCES = {
    "school_records": ("school_record", 0.0, 0.05, 25),
    "outlet_a": ("reporter", math.log(1.3), 0.15, 40),
    "outlet_b": ("reporter", 0.0, 0.30, 40),
    "hype_account": ("other", math.log(2.5), 0.30, 25),
}
SCENARIOS = {"weak features": (0.5, 0.3), "strong features": (0.8, 0.6)}   # each feature's correlation with talent


def football_transports(published: pd.DataFrame, tail_mult: float | None = None) -> dict[str, ex.Transport]:
    """A4 football revenue-share transport per position, tail calibrated to the cap at the central case."""
    if tail_mult is None:
        cal = tri.calibrate(published)
        tail_mult = float(cal[(cal.report == "revenue_share") & (cal.case == "central")].tail_mult.iloc[0])
    return {c.key.position: ex.Transport(c, tail_mult) for c in bm.curves(published)[0]
            if c.key.report == "revenue_share" and c.key.sport == "Football" and c.key.cohort == "A4"
            and c.fitted and c.zero_share is not None}


def market(transports: dict[str, ex.Transport], seed: int = 0, programs: int = tri.A4_FOOTBALL_PROGRAMS,
           feature_corr: tuple[float, float] = (0.7, 0.45), school_sd: float = 0.4, noise_sd: float = 0.5,
           disclosed: int = 10) -> dict:
    rng = np.random.default_rng(seed)
    effect = rng.normal(0, school_sd, programs)
    frames = []
    for pos, t in transports.items():
        n = int(t.curve.n_all)
        school = rng.integers(programs, size=n)
        talent = rng.standard_normal(n)
        value = talent + effect[school] + rng.normal(0, noise_sd, n)
        f = {name: r * talent + math.sqrt(1 - r * r) * rng.standard_normal(n) for name, r in zip(FEATURES, feature_corr)}
        frames.append(pd.DataFrame({"school": school, "cohort": pos, "talent": talent, "value": value, **f,
                                    "pay": t.pay(value)}))
    players = pd.concat(frames, ignore_index=True)
    players.insert(0, "player_id", [f"p{i}" for i in range(len(players))])
    totals = players.groupby("school").pay.sum()
    shown = rng.choice(programs, size=disclosed, replace=False)
    return {"players": players, "totals": totals, "disclosed": {int(s): float(totals[s]) for s in shown},
            "effect": effect}


def make_claims(players: pd.DataFrame, seed: int = 0, sources: dict = SOURCES, top_share: float = 0.05) -> pd.DataFrame:
    """Each source reports some of the best-paid players (the top `top_share` of each position), picked with
    probability proportional to pay, as coverage follows the stars, with its bias and noise."""
    rng = np.random.default_rng(seed + 1000)
    cut = players.groupby("cohort").pay.transform(lambda p: p.quantile(1 - top_share))
    pool = players[(players.pay >= cut) & (players.pay > 0)]
    rows = []
    for name, (stype, bias, noise, k) in sources.items():
        pick = pool.sample(n=min(k, len(pool)), weights=pool.pay, random_state=int(rng.integers(1 << 31)))
        for r in pick.itertuples(index=False):
            rows.append({"claim_id": f"{name}-{r.player_id}", "player": r.player_id, "school": str(r.school),
                         "sport": "Football", "gender": "men", "position": r.cohort, "cohort": "A4",
                         "report": "revenue_share", "amount": r.pay * math.exp(bias + noise * rng.standard_normal()),
                         "years": np.nan, "source_type": stype, "source": name, "url": "", "date": ""})
    return pd.DataFrame(rows)


def debiased(claims: pd.DataFrame) -> pd.DataFrame:
    """One value per player: each claim divided by its source's estimated bias, averaged on the log scale."""
    bias = cl.source_bias(claims).set_index("source").bias
    d = claims.assign(log_value=np.log(claims.amount) - np.log1p(claims.source.map(bias).fillna(0.0)))
    return d.groupby("player", as_index=False).log_value.mean().rename(columns={"player": "player_id"}) \
        .assign(value=lambda x: np.exp(x.log_value))[["player_id", "value"]]


def _metrics(est: pd.DataFrame, players: pd.DataFrame, mask: np.ndarray | None = None) -> dict:
    m = np.ones(len(players), bool) if mask is None else mask
    true, e = players.pay.to_numpy()[m], est.estimate.to_numpy()[m]
    return {"rank_corr": ex.rank_corr(est.score.to_numpy()[m], true, players.cohort.to_numpy()[m]),
            "median_log_error": float(np.median(np.abs(np.log1p(e) - np.log1p(true)))),
            "coverage_80": float(np.mean((true >= est.low.to_numpy()[m] - 1) & (true <= est.high.to_numpy()[m] + 1)))}


def evaluate(transports: dict, seed: int, feature_corr: tuple[float, float]) -> list[dict]:
    world = market(transports, seed=seed, feature_corr=feature_corr)
    players = world["players"]
    claims = make_claims(players, seed)
    clean = debiased(claims)
    disclosed = players.school.isin(world["disclosed"]).to_numpy()
    claimed = players.player_id.isin(clean.player_id).to_numpy()
    runs = {
        "features only": ex.estimate(players, FEATURES, transports, seed=seed),
        "+ claims as training labels": ex.estimate(players, FEATURES, transports, claims=clean, seed=seed, learn="always"),
        "+ claims as anchors": ex.estimate(players, FEATURES, transports, claims=clean, seed=seed),
        "+ anchors + school totals": ex.estimate(players, FEATURES, transports, claims=clean,
                                                 school_totals=world["disclosed"], seed=seed),
    }
    rows = []
    for method, est in runs.items():
        for group, mask in (("all", None), ("unclaimed", ~claimed), ("claimed", claimed), ("disclosed schools", disclosed)):
            rows.append({"seed": seed, "method": method, "players": group, **_metrics(est, players, mask)})
    return rows


def credibility(transports: dict, published: pd.DataFrame, seed: int = 0) -> pd.DataFrame:
    """How the credibility checks score each simulated source, against its true bias."""
    world = market(transports, seed=seed)
    claims, _ = cl.clean(make_claims(world["players"], seed).astype({"amount": str, "years": str}))
    curves = bm.curves(published)[0]
    placed = cl.place(claims, curves)
    ev = cl.evidence(placed, curves, published)
    bias = cl.source_bias(claims).set_index("source").bias
    rows = []
    for name, (stype, true_bias, noise, k) in SOURCES.items():
        o = ev[ev.source == name]
        rows.append({"seed": seed, "source": name, "true_bias": math.exp(true_bias) - 1,
                     "estimated_bias": bias.get(name, np.nan), "claims": int((claims.source == name).sum()),
                     "strong": int(o.strong.sum()), "moderate": int(o.moderate.sum())})
    return pd.DataFrame(rows)


def run(published: pd.DataFrame, seeds: tuple[int, ...] = (0, 1, 2)) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Method comparison over scenarios and seeds, and the credibility checks on one simulated market."""
    transports = football_transports(published)
    rows = []
    for scenario, corr in SCENARIOS.items():
        for seed in seeds:
            rows += [{"scenario": scenario, **r} for r in evaluate(transports, seed, corr)]
    return pd.DataFrame(rows), pd.concat([credibility(transports, published, s) for s in seeds], ignore_index=True)
