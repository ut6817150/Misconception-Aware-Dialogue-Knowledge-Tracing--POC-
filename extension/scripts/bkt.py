"""
myext/bkt.py

Bayesian Knowledge Tracing (BKT) for the dialogue-KT experiment, implemented
in pure Python / numpy (no compiled dependency such as pyBKT). This makes the
model run identically on any platform and removes the Apple-Silicon build
failure that pyBKT's compiled E-step exhibits.

The model is the classic Corbett and Anderson two-state BKT with no forgetting,
fit per knowledge component (KC) by Expectation-Maximisation over the
forward-backward algorithm, with multiple random restarts to avoid poor local
optima and the standard identifiability constraint guess, slip < 0.5.

Beyond the standard fit, this module adds:

  1. A weighted-average parameter fallback for degenerate training KCs and KCs
     unseen at test time. Degenerate KCs (all-correct or all-incorrect) are not
     fit individually; they receive the complete parameter vector formed by
     the observation-count-weighted mean across nondegenerate fitted KCs.

  2. Clean separation of fit / fallback / predict so the same machinery
     extends to the misconception emission later.

Data format (long): one row per (dialogue, turn, kc) with columns
  dialogue_idx, turn, correct, kc.
Each dialogue is an independent student; within a dialogue, a KC's turns form
one observation sequence. A KC pools all its per-dialogue sequences when fit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


# Parameter names carried per KC. Standard BKT four (no forgetting).
PARAM_NAMES = ("prior", "learns", "guesses", "slips")


# ---------------------------------------------------------------------------
# Building per-KC sequences from the long-format table
# ---------------------------------------------------------------------------

def kc_sequences(long_df: pd.DataFrame) -> Dict[str, List[np.ndarray]]:
    """Group observations into per-KC lists of per-dialogue correctness
    sequences.

    Returns {kc: [seq, seq, ...]} where each seq is a 1-D int array of 0/1
    correctness for that KC within one dialogue, in turn order.
    """
    df = long_df.copy()
    # order turns within a dialogue by their integer (turn labels like 'turn 3')
    df["_turn_num"] = df["turn"].astype(str).str.extract(r"(\d+)").astype(float)
    df = df.sort_values(["dialogue_idx", "_turn_num"])
    sequences: Dict[str, List[np.ndarray]] = {}
    for (kc, _did), grp in df.groupby(["kc", "dialogue_idx"], sort=False):
        sequences.setdefault(str(kc), []).append(grp["correct"].to_numpy(dtype=int))
    return sequences


# ---------------------------------------------------------------------------
# EM for a single KC (two-state BKT, no forgetting)
# ---------------------------------------------------------------------------

# State 0 = not mastered, State 1 = mastered.

def _forward_backward(
    seq: np.ndarray, prior: float, learn: float, guess: float, slip: float
):
    """Forward-backward for one sequence. Returns posteriors and the soft
    counts needed for the M-step, plus the sequence log-likelihood.

    Emission: P(correct=1 | state0) = guess; P(correct=1 | state1) = 1 - slip.
    Transition: P(0->1) = learn; P(1->1) = 1 (no forgetting).
    """
    T = len(seq)
    # emission probability of the observed correctness in each state
    # b[t, s] = P(obs_t | state s)
    b = np.empty((T, 2))
    p_correct_state = np.array([guess, 1.0 - slip])
    for t in range(T):
        if seq[t] == 1:
            b[t] = p_correct_state
        else:
            b[t] = 1.0 - p_correct_state

    # transition matrix A[i, j] = P(state_t = j | state_{t-1} = i)
    A = np.array([[1.0 - learn, learn], [0.0, 1.0]])
    pi = np.array([1.0 - prior, prior])

    # forward with scaling
    alpha = np.zeros((T, 2))
    scale = np.zeros(T)
    alpha[0] = pi * b[0]
    scale[0] = alpha[0].sum()
    if scale[0] <= 0:
        scale[0] = 1e-300
    alpha[0] /= scale[0]
    for t in range(1, T):
        alpha[t] = (alpha[t - 1] @ A) * b[t]
        scale[t] = alpha[t].sum()
        if scale[t] <= 0:
            scale[t] = 1e-300
        alpha[t] /= scale[t]

    # backward with the same scaling
    beta = np.zeros((T, 2))
    beta[T - 1] = 1.0
    for t in range(T - 2, -1, -1):
        beta[t] = (A @ (b[t + 1] * beta[t + 1])) / scale[t + 1]

    # posteriors
    gamma = alpha * beta
    gamma_sum = gamma.sum(axis=1, keepdims=True)
    gamma_sum[gamma_sum == 0] = 1e-300
    gamma = gamma / gamma_sum

    # pairwise posteriors xi[t, i, j] for t in 0..T-2
    xi = np.zeros((T - 1, 2, 2))
    for t in range(T - 1):
        denom = scale[t + 1]
        for i in range(2):
            for j in range(2):
                xi[t, i, j] = (
                    alpha[t, i] * A[i, j] * b[t + 1, j] * beta[t + 1, j] / denom
                )
        s = xi[t].sum()
        if s > 0:
            xi[t] /= s

    loglike = np.sum(np.log(scale))
    return gamma, xi, loglike


def _em_single_kc(
    sequences: List[np.ndarray],
    n_restarts: int = 5,
    max_iter: int = 100,
    tol: float = 1e-4,
    seed: int = 221,
) -> Dict[str, float]:
    """Fit one KC's BKT parameters by EM with random restarts.

    Returns {prior, learns, guesses, slips}. Guess and slip are constrained
    below 0.5 for identifiability (so 'mastered' always means 'more likely
    correct').
    """
    rng = np.random.default_rng(seed)
    best = None
    best_ll = -np.inf

    for _ in range(n_restarts):
        # random init within sensible ranges
        prior = rng.uniform(0.05, 0.5)
        learn = rng.uniform(0.05, 0.4)
        guess = rng.uniform(0.05, 0.4)
        slip = rng.uniform(0.05, 0.4)

        prev_ll = -np.inf
        for _it in range(max_iter):
            # accumulate soft counts across all sequences
            init0 = init1 = 0.0
            trans_denom = trans_num = 0.0  # for learn: 0->1 transitions / time in 0
            # emission counts: correct/incorrect weighted by state posterior
            g_corr = g_tot = 0.0  # guess: state0
            s_corr = s_tot = 0.0  # slip:  state1 (count incorrect)
            total_ll = 0.0

            for seq in sequences:
                gamma, xi, ll = _forward_backward(seq, prior, learn, guess, slip)
                total_ll += ll
                init0 += gamma[0, 0]
                init1 += gamma[0, 1]
                if len(seq) > 1:
                    # time spent in state0 (excluding last step) drives learn denom
                    trans_denom += gamma[:-1, 0].sum()
                    trans_num += xi[:, 0, 1].sum()
                # emissions
                correct = seq == 1
                g_corr += gamma[correct, 0].sum()
                g_tot += gamma[:, 0].sum()
                s_corr += gamma[~correct, 1].sum()  # incorrect while mastered = slip
                s_tot += gamma[:, 1].sum()

            # M-step with guards
            new_prior = init1 / (init0 + init1) if (init0 + init1) > 0 else prior
            new_learn = trans_num / trans_denom if trans_denom > 0 else learn
            new_guess = g_corr / g_tot if g_tot > 0 else guess
            new_slip = s_corr / s_tot if s_tot > 0 else slip

            # identifiability: keep guess, slip < 0.5; clip into valid range
            new_guess = float(np.clip(new_guess, 1e-3, 0.49))
            new_slip = float(np.clip(new_slip, 1e-3, 0.49))
            new_prior = float(np.clip(new_prior, 1e-3, 1 - 1e-3))
            new_learn = float(np.clip(new_learn, 1e-3, 1 - 1e-3))

            prior, learn, guess, slip = new_prior, new_learn, new_guess, new_slip

            if total_ll - prev_ll < tol:
                break
            prev_ll = total_ll

        if total_ll > best_ll:
            best_ll = total_ll
            best = {
                "prior": prior,
                "learns": learn,
                "guesses": guess,
                "slips": slip,
            }

    return best


# ---------------------------------------------------------------------------
# Weighted-average fallback
# ---------------------------------------------------------------------------

def weighted_average_params(
    params: pd.DataFrame, obs_counts: pd.Series
) -> Dict[str, float]:
    """Observation-count-weighted mean of each BKT parameter across KCs.

    Applied per-parameter, so a KC missing one parameter does not drop the
    others. Arithmetic mean for now (revisit log-odds once the fitted
    distribution is inspected). Guaranteed finite even in pathological cases.
    """
    fallback = {}
    defaults = {"prior": 0.5, "learns": 0.1, "guesses": 0.2, "slips": 0.1}
    for p in PARAM_NAMES:
        col = params[p].dropna()
        w = obs_counts.reindex(col.index).fillna(0.0)
        if len(col) == 0:
            fallback[p] = defaults[p]
        elif w.sum() > 0:
            fallback[p] = float(np.average(col.values, weights=w.values))
        else:
            fallback[p] = float(col.mean())
    return fallback


# ---------------------------------------------------------------------------
# Prediction with pooled fallback
# ---------------------------------------------------------------------------

def _bkt_seq_predict(
    correct_seq: np.ndarray, prior: float, learn: float, guess: float, slip: float
) -> np.ndarray:
    """Forward prediction of P(correct) for each step of one sequence.

    At each step, predict P(correct) from the current mastery belief, then
    update the belief given the observed correctness, then apply the learning
    transition. The prediction at t uses only information before the response
    at t, matching how next-step KT prediction is scored.
    """
    p_known = prior
    preds = np.empty(len(correct_seq), dtype=float)
    for t, c in enumerate(correct_seq):
        p_correct = p_known * (1 - slip) + (1 - p_known) * guess
        preds[t] = p_correct
        if c == 1:
            num = p_known * (1 - slip)
            den = p_correct
        else:
            num = p_known * slip
            den = 1 - p_correct
        p_known_post = num / den if den > 0 else p_known
        p_known = p_known_post + (1 - p_known_post) * learn
    return preds


@dataclass
class FittedBKT:
    """A fitted BKT model plus its fallback, able to predict on any split."""

    per_skill: Dict[str, Dict[str, float]]
    fallback: Dict[str, float]

    def params_for(self, skill: str) -> Dict[str, float]:
        """Parameter set for a skill, patching any missing OR NaN parameter
        (or the whole skill, if unseen) with the fallback.
        """
        base = self.per_skill.get(skill, {})

        def pick(name):
            v = base.get(name, None)
            if v is None or (isinstance(v, float) and np.isnan(v)):
                return self.fallback[name]
            return v

        return {name: pick(name) for name in PARAM_NAMES}

    def predict_long(self, long_df: pd.DataFrame) -> pd.DataFrame:
        """Predict P(correct) for every (dialogue, turn, kc) row, using each
        KC's own parameters where available and the fallback otherwise.
        """
        df = long_df.copy()
        df["_turn_num"] = df["turn"].astype(str).str.extract(r"(\d+)").astype(float)
        df = df.sort_values(["dialogue_idx", "kc", "_turn_num"])
        preds = np.empty(len(df), dtype=float)
        for (_did, skill), grp in df.groupby(["dialogue_idx", "kc"], sort=False):
            pos = df.index.get_indexer(grp.index)
            pr = self.params_for(str(skill))
            preds[pos] = _bkt_seq_predict(
                grp["correct"].to_numpy(dtype=int),
                pr["prior"], pr["learns"], pr["guesses"], pr["slips"],
            )
        out = df.copy()
        out["pred"] = preds
        return out.drop(columns="_turn_num").sort_index()


# ---------------------------------------------------------------------------
# Top-level fit
# ---------------------------------------------------------------------------

def fit_bkt(
    train_long: pd.DataFrame,
    n_restarts: int = 5,
    max_iter: int = 100,
    seed: int = 221,
    verbose: bool = True,
) -> FittedBKT:
    """Fit BKT per nondegenerate KC and build a pooled fallback.

    KCs that are all-correct or all-incorrect are not fit individually because
    their four BKT parameters cannot be separated reliably. Instead, they are
    assigned the complete observation-weighted mean parameter vector estimated
    from nondegenerate KCs. The same vector is used for KCs unseen in training.
    """
    sequences = kc_sequences(train_long)
    stats = train_long.groupby("kc")["correct"].agg(n="count", n_correct="sum")
    degenerate_mask = ((stats["n_correct"] == 0) |
                       (stats["n_correct"] == stats["n"]))
    degenerate_kcs = set(stats.index[degenerate_mask].astype(str))

    rows = {}
    for i, (kc, seqs) in enumerate(sequences.items()):
        if kc in degenerate_kcs:
            continue
        rows[kc] = _em_single_kc(
            seqs, n_restarts=n_restarts, max_iter=max_iter, seed=seed + i
        )
    params = pd.DataFrame.from_dict(
        rows, orient="index", columns=list(PARAM_NAMES)
    )

    # The fallback is learned only from nondegenerate KCs. Observation weighting
    # makes it representative of a typical observation rather than a typical KC.
    nondegenerate_rows = ~train_long["kc"].astype(str).isin(degenerate_kcs)
    obs_counts = train_long[nondegenerate_rows].groupby("kc").size()
    obs_counts.index = obs_counts.index.astype(str)

    n_nan = int(params.isna().any(axis=1).sum())
    if verbose and n_nan:
        print(f"[fit_bkt] {n_nan} of {len(params)} KCs had a NaN parameter; "
              f"these fall back per-parameter.")

    fallback = weighted_average_params(params, obs_counts)
    per_skill = {skill: row.dropna().to_dict() for skill, row in params.iterrows()}
    for kc in degenerate_kcs:
        per_skill[kc] = dict(fallback)

    if verbose and degenerate_kcs:
        print(f"[fit_bkt] {len(degenerate_kcs)} degenerate KCs assigned the "
              "observation-weighted fallback from nondegenerate KCs.")
    return FittedBKT(per_skill=per_skill, fallback=fallback)


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

from sklearn.metrics import roc_auc_score, accuracy_score, brier_score_loss, log_loss


@dataclass
class Metrics:
    n: int
    accuracy: float
    auc: float
    log_likelihood: float
    brier: float

    def __str__(self) -> str:
        return (
            f"n={self.n}  Acc={self.accuracy:.4f}  AUC={self.auc:.4f}  "
            f"LL={self.log_likelihood:.4f}  Brier={self.brier:.4f}"
        )


def compute_metrics(labels: np.ndarray, preds: np.ndarray) -> Metrics:
    """Accuracy, AUC, mean log-likelihood (higher better), and Brier score."""
    labels = np.asarray(labels, dtype=int)
    preds = np.asarray(preds, dtype=float)
    eps = 1e-12
    preds_c = np.clip(preds, eps, 1 - eps)
    acc = accuracy_score(labels, (preds >= 0.5).astype(int))
    auc = roc_auc_score(labels, preds) if len(np.unique(labels)) > 1 else float("nan")
    ll = -log_loss(labels, preds_c, labels=[0, 1])
    brier = brier_score_loss(labels, preds_c)
    return Metrics(n=len(labels), accuracy=acc, auc=auc, log_likelihood=ll, brier=brier)


def evaluate(fitted: FittedBKT, test_long: pd.DataFrame):
    """Predict on test and compute metrics overall and on final turns.

    Returns (overall_metrics, final_turn_metrics, predictions_df).
    """
    pred_df = fitted.predict_long(test_long)
    overall = compute_metrics(pred_df["correct"].to_numpy(), pred_df["pred"].to_numpy())

    pred_df = pred_df.copy()
    pred_df["_turn_num"] = pred_df["turn"].astype(str).str.extract(r"(\d+)").astype(int)
    final_idx = pred_df.groupby("dialogue_idx")["_turn_num"].idxmax()
    final = pred_df.loc[final_idx]
    final_m = compute_metrics(final["correct"].to_numpy(), final["pred"].to_numpy())
    return overall, final_m, pred_df.drop(columns="_turn_num")
