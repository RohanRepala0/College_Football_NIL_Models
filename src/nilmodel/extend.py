"""Extending the CSC distributions to individual players.

The CSC gives each cohort's pay distribution; a ranker gives each player's place in it. A player's pay
is the cohort's quantile at his rank (one-dimensional optimal transport), so the estimates reproduce the
published distribution exactly, whatever the ranker. Only the ranking is learned:

- claims as anchors: a claimed player is pinned at his (debiased) claim's percentile, and everyone else
  is still ranked by features. Claims cover the stars, so fitting feature weights to them learns what
  separates stars and ranks everyone else worse (selection bias), and cross-validation on held-out
  claims can't see that harm, because the held-out claims are stars too. So weights are learned from
  claims (pairwise ranking loss) only on request, for claims that cover the whole cohort;
- school effects from disclosed school totals, by raking: each disclosed school's scores shift until its
  players' transported pay sums to its total, which is learning from aggregate labels;
- and the uncertainty in a player's rank, from how closely the ranker tracks pay, becomes his interval.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from . import benchmark as bm
from . import triangulate as tri


class Transport:
    """One cohort's pay as a function of rank among everyone rostered: zeros for the unpaid share, then
    the paid curve (with its tail slope scaled by `tail_mult`)."""

    def __init__(self, curve: bm.Curve, tail_mult: float = 1.0):
        self.curve, self.tail_mult = curve, tail_mult
        self.zero = curve.zero_share or 0.0

    def pay_at(self, u) -> np.ndarray:
        u = np.asarray(u, float)
        out = np.zeros_like(u)
        paid = u > self.zero
        q = np.clip((u[paid] - self.zero) / (1 - self.zero), 1e-6, 1 - 1e-6)
        out[paid] = tri.tail_quantile(self.curve, q, self.tail_mult)
        return out

    def rank_of(self, value: float) -> float:
        """Inverse of `pay_at`: the share of the cohort paid at most `value` (the middle of the unpaid share for $0)."""
        if value <= 0:
            return self.zero / 2
        from .claims import cdf

        return self.zero + (1 - self.zero) * cdf(self.curve, value, self.tail_mult)

    def pay(self, scores) -> np.ndarray:
        """Pay at each score's mid-rank in the cohort; tied scores share a rank."""
        scores = np.asarray(scores, float)
        return self.pay_at((rankdata(scores) - 0.5) / len(scores))


def standardize(X: np.ndarray) -> np.ndarray:
    sd = X.std(axis=0)
    return (X - X.mean(axis=0)) / np.where(sd > 0, sd, 1)


def transport_all(scores: np.ndarray, cohort: np.ndarray, transports: dict) -> np.ndarray:
    pay = np.zeros(len(scores))
    for key, t in transports.items():
        m = cohort == key
        if m.any():
            pay[m] = t.pay(scores[m])
    return pay


def fit_weights(Xs: np.ndarray, cohort: np.ndarray, claimed: np.ndarray, value: np.ndarray, prior: np.ndarray,
                l2: float = 1.0, iters: int = 400, lr: float = 0.1) -> np.ndarray:
    """Linear ranking weights from claims (RankNet): for every pair of claimed players in one cohort, the
    logistic loss of the better-paid scoring lower, plus l2 x distance from the prior weights.
    `claimed` indexes rows of the standardized features `Xs`; `value[row]` is that row's (debiased) pay."""
    pairs = []
    for key in np.unique(cohort[claimed]):
        idx = claimed[cohort[claimed] == key]
        vals = value[idx]
        for a in range(len(idx)):
            for b in range(len(idx)):
                if vals[a] > vals[b] * 1.05:            # ignore near-ties: claims are noisy
                    pairs.append((idx[a], idx[b]))
    w = prior.astype(float).copy()
    if not pairs:
        return w
    hi, lo = np.array(pairs).T
    D = Xs[hi] - Xs[lo]
    for _ in range(iters):
        margin = D @ w
        g = -(D * (1 / (1 + np.exp(margin)))[:, None]).mean(axis=0) + 2 * l2 * (w - prior) / len(pairs)
        w -= lr * g
    return w


def pair_accuracy(Xs: np.ndarray, w: np.ndarray, cohort: np.ndarray, rows: np.ndarray, value: np.ndarray) -> float:
    """Share of claimed pairs in one cohort (clearly apart in pay) that the weights order correctly."""
    s = Xs @ w
    good = total = 0
    for key in np.unique(cohort[rows]):
        idx = rows[cohort[rows] == key]
        for a in idx:
            for b in idx:
                if value[a] > value[b] * 1.05:
                    total += 1
                    good += s[a] > s[b]
    return good / total if total else float("nan")


def cv_weights(Xs: np.ndarray, cohort: np.ndarray, claimed: np.ndarray, value: np.ndarray, prior: np.ndarray,
               folds: int = 5, seed: int = 0) -> tuple[np.ndarray, bool]:
    """Weights learned from claims if, on held-out claims, they order pairs better than the prior; else the prior."""
    rng = np.random.default_rng(seed)
    fold = rng.integers(folds, size=len(claimed))
    learned_acc, prior_acc = [], []
    for f in range(folds):
        train, test = claimed[fold != f], claimed[fold == f]
        if len(test) < 2:
            continue
        w = fit_weights(Xs, cohort, train, value, prior)
        learned_acc.append(pair_accuracy(Xs, w, cohort, test, value))
        prior_acc.append(pair_accuracy(Xs, prior, cohort, test, value))
    if np.nanmean(learned_acc or [np.nan]) > np.nanmean(prior_acc or [np.nan]) + 0.02:
        return fit_weights(Xs, cohort, claimed, value, prior), True
    return prior, False


def anchor(scores: np.ndarray, cohort: np.ndarray, claimed: np.ndarray, value: np.ndarray, transports: dict) -> np.ndarray:
    """Pin each claimed player at his claim's percentile: his score becomes that quantile of his cohort's scores."""
    out = scores.copy()
    for key, t in transports.items():
        rows = claimed[cohort[claimed] == key]
        if not len(rows):
            continue
        pool = scores[cohort == key]
        for r in rows:
            out[r] = np.quantile(pool, min(max(t.rank_of(value[r]), 0.0), 1.0))
    return out


def rake(scores: np.ndarray, cohort: np.ndarray, school: np.ndarray, transports: dict, totals: dict,
         iters: int = 4, steps: int = 22, span: float = 4.0) -> dict:
    """School effects that make each disclosed school's transported pay sum to its total. One school at a
    time, bisect its shift (its total rises with it), and cycle until the shifts settle. Schools without
    a disclosed total get no effect."""
    gamma = {s: 0.0 for s in totals}
    masks = {s: school == s for s in totals}
    shift = np.zeros(len(scores))

    def total_for(s, g):
        trial = scores + shift
        trial[masks[s]] = scores[masks[s]] + g
        return transport_all(trial, cohort, transports)[masks[s]].sum()

    for _ in range(iters):
        for s, target in totals.items():
            lo, hi = -span, span
            for _ in range(steps):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if total_for(s, mid) < target else (lo, mid)
            gamma[s] = (lo + hi) / 2
            shift[masks[s]] = gamma[s]
    return gamma


def intervals(scores: np.ndarray, cohort: np.ndarray, transports: dict, rho: float, draws: int = 200,
              level: float = 0.8, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Pay intervals from rank uncertainty. If the scores correlate rho with the latent pay ranking, the
    latent is rho x score + sqrt(1 - rho^2) x noise (standardized, per cohort); each draw is ranked and
    transported, and the interval is the draws' central `level`."""
    rng = np.random.default_rng(seed)
    z = np.zeros(len(scores))
    for key in transports:
        m = cohort == key
        if m.sum() > 1:
            z[m] = (scores[m] - scores[m].mean()) / (scores[m].std() or 1)
    sims = np.empty((draws, len(scores)))
    for d in range(draws):
        latent = rho * z + np.sqrt(max(0.0, 1 - rho ** 2)) * rng.standard_normal(len(z))
        sims[d] = transport_all(latent, cohort, transports)
    a = (1 - level) / 2
    return np.quantile(sims, a, axis=0), np.quantile(sims, 1 - a, axis=0)


def rank_corr(scores: np.ndarray, value: np.ndarray, cohort: np.ndarray) -> float:
    """Spearman correlation of scores with values within cohorts, weighted by cohort size."""
    num = den = 0.0
    for key in np.unique(cohort):
        m = cohort == key
        if m.sum() > 2 and np.std(value[m]) > 0:
            r = np.corrcoef(rankdata(scores[m]), rankdata(value[m]))[0, 1]
            num += r * m.sum()
            den += m.sum()
    return num / den if den else float("nan")


def estimate(players: pd.DataFrame, features: list[str], transports: dict, claims: pd.DataFrame | None = None,
             school_totals: dict | None = None, rho: float | None = None, prior: np.ndarray | None = None,
             seed: int = 0, learn: str = "never", claim_sd: float = 0.25) -> pd.DataFrame:
    """Pay estimates for `players` (columns: player_id, school, cohort and `features`).
    `claims`: player_id and value (already debiased); `school_totals`: {school: total}. `rho` is how well
    the scores rank pay; when None it is estimated from the claims before anchoring (or 0.5 without any).
    `learn` is "never" (the default: claims only anchor), "cv" or "always". A claimed player's interval is
    his debiased claim times exp(+-1.28 claim_sd)."""
    Xs = standardize(players[features].to_numpy(float))
    cohort = players.cohort.to_numpy()
    school = players.school.to_numpy()
    w = prior if prior is not None else np.ones(len(features)) / len(features)
    pos = {pid: i for i, pid in enumerate(players.player_id)}
    if claims is not None and len(claims):
        c = claims[claims.player_id.isin(pos)]
        claimed = np.array([pos[p] for p in c.player_id])
        value = np.zeros(len(players))
        value[claimed] = c.value.to_numpy(float)
        if learn == "always":
            w = fit_weights(Xs, cohort, claimed, value, w)
        elif learn == "cv":
            w, _ = cv_weights(Xs, cohort, claimed, value, w, seed=seed)
    scores = Xs @ w
    if school_totals:
        gamma = rake(scores, cohort, school, transports, school_totals)
        scores = scores + np.array([gamma.get(s, 0.0) for s in school])
    has_claims = claims is not None and len(claims) > 0
    if rho is None:
        rho = max(0.05, rank_corr(scores[claimed], value[claimed], cohort[claimed])) if has_claims and len(claimed) > 5 else 0.5
    if has_claims:
        scores = anchor(scores, cohort, claimed, value, transports)
    pay = transport_all(scores, cohort, transports)
    lo, hi = intervals(scores, cohort, transports, rho, seed=seed)
    if has_claims:
        lo[claimed] = value[claimed] * np.exp(-1.2816 * claim_sd)
        hi[claimed] = value[claimed] * np.exp(1.2816 * claim_sd)
    return pd.DataFrame({"player_id": players.player_id, "estimate": pay, "low": lo, "high": hi, "score": scores})
