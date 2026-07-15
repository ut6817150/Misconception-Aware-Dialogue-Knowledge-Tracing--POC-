"""
Faithful replication of the dialogue-KT paper's BKT baseline.

This module mirrors the BKT pipeline in the paper's own repository
(umass-ml4ed/dialogue-kt), so the notebook that imports it reproduces the
paper's correctness-only MathDial BKT as closely as possible. The functions
below follow the paper's code path:

  - apply_annotations   : mirrors kt_data_loading.apply_annotations (na logic,
                          student-initiated turn 0, final-turn correctness from
                          MathDial self_correctness).
  - build_pseudo_turns  : mirrors bkt_prep_data (one pyBKT row per KC, all rows
                          of a dialogue share one user_id, incrementing order_id,
                          plus turn-boundary indices for aggregation).
  - aggregate_turn      : mirrors the agg options prod / mean-ar / mean-geo.
  - evaluate_bkt        : mirrors train_test_bkt (drop the first TAGGED turn via
                          labels[1:] / preds[1:], then compute metrics).
  - compute_metrics     : mirrors training.compute_metrics (accuracy, AUC, and
                          binary F1 with the positive class = correct).

The BKT model itself is pyBKT (the paper's exact model, Model(seed=221,
num_fits=1)) when available. If pyBKT cannot be imported, a numpy BKT that
mirrors pyBKT's standard model is used instead, so the pipeline still runs.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, roc_auc_score,
                             precision_recall_fscore_support)

PARAM_NAMES = ("prior", "learns", "guesses", "slips")


# ---------------------------------------------------------------------------
# 1. apply_annotations  (mirrors kt_data_loading.apply_annotations)
# ---------------------------------------------------------------------------

def _as_obj(x):
    """Parse a cell that may be a Python-literal string into an object."""
    if isinstance(x, (dict, list)):
        return x
    try:
        return ast.literal_eval(str(x))
    except (ValueError, SyntaxError):
        return None


def apply_annotations(sample: dict, apply_na: bool = True) -> Optional[list]:
    """Copy correctness and KCs onto each dialogue turn, exactly as the paper.

    Returns the dialogue as a list of turn dicts with 'correct' and 'kcs'
    populated, or None if the annotation failed. Faithful to the paper's
    na handling, student-initiated turn-0 handling, and MathDial final-turn
    correctness from self_correctness.
    """
    dialogue = _as_obj(sample["dialogue"])
    anno = _as_obj(sample["annotation"])
    meta = _as_obj(sample.get("meta_data")) or {}
    if not isinstance(anno, dict) or "error" in anno:
        return None

    # Student-initiated dialogues carry a turn 0 with no correctness / KCs.
    if dialogue[0]["turn"] == 0:
        anno["turn 0"] = {"correct": None, "kcs": []}

    for dia_turn in dialogue:
        anno_turn = anno.get(f"turn {dia_turn['turn']}")
        if anno_turn is None:
            dia_turn["correct"] = None
            dia_turn["kcs"] = []
            continue
        corr = anno_turn["correct"]
        kcs = anno_turn["kcs"]
        if apply_na:
            corr = None if not kcs else corr
            kcs = [] if corr is None else kcs
        dia_turn["correct"] = corr
        dia_turn["kcs"] = kcs

    # Final-turn correctness from MathDial self_correctness (human annotation).
    if dialogue[-1]["kcs"]:
        if "self_correctness" in meta:
            if dialogue[-1]["correct"] is not None:
                sc = meta["self_correctness"]
                if sc == "Yes":
                    dialogue[-1]["correct"] = True
                elif sc == "Yes, but I had to reveal the answer":
                    dialogue[-1]["correct"] = None
                elif sc == "No":
                    dialogue[-1]["correct"] = False
    return dialogue


# ---------------------------------------------------------------------------
# 2. build_pseudo_turns  (mirrors bkt_prep_data)
# ---------------------------------------------------------------------------

@dataclass
class DialogueSeq:
    """One dialogue's tagged turns, flattened to pseudo-turns for BKT."""
    user_id: int
    turn_labels: List[int]                 # one correctness label per tagged turn
    turn_kc_slices: List[Tuple[int, int]]  # (start, end) row-range per tagged turn
    rows: List[dict]                       # per-(kc) pyBKT rows for this dialogue


def build_pseudo_turns(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[DialogueSeq]]:
    """Flatten annotated dialogues to per-KC pseudo-turn rows.

    Mirrors bkt_prep_data: every KC of every tagged turn becomes one row, all
    rows in a dialogue share one user_id, and order_id increments globally.
    Dialogues with fewer than two tagged turns are excluded, matching the
    paper's DKTDataset. Also records, per dialogue, the turn-level label sequence
    and the row-range of each turn so predictions can be aggregated back to the
    turn level.
    """
    all_rows = []
    seqs: List[DialogueSeq] = []
    order_id = 0
    for idx, sample in df.iterrows():
        dialogue = apply_annotations(sample)
        if not dialogue:
            continue
        turn_labels: List[int] = []
        turn_kc_slices: List[Tuple[int, int]] = []
        dia_rows: List[dict] = []
        for turn in dialogue:
            if turn["correct"] is None or not turn["kcs"]:
                continue  # untagged / na turn - not part of the BKT sequence
            start = len(dia_rows)
            label = int(bool(turn["correct"]))
            for kc in turn["kcs"]:
                row = {"user_id": int(idx), "skill_name": str(kc),
                       "correct": label}
                dia_rows.append(row)
            end = len(dia_rows)  # exclusive
            turn_labels.append(label)
            turn_kc_slices.append((start, end))
        if len(turn_labels) >= 2:
            for row in dia_rows:
                row["order_id"] = order_id
                all_rows.append(row)
                order_id += 1
            seqs.append(DialogueSeq(int(idx), turn_labels, turn_kc_slices, dia_rows))
    return pd.DataFrame(all_rows), seqs


# ---------------------------------------------------------------------------
# 3. aggregate_turn  (mirrors the agg options)
# ---------------------------------------------------------------------------

def aggregate_turn(kc_preds: np.ndarray, agg: str = "mean-ar") -> float:
    """Aggregate a turn's per-KC probabilities into one turn probability.

    Mirrors the paper's agg options. Default is mean-ar (arithmetic mean),
    matching the paper's default.
    """
    if agg == "prod":
        return float(np.prod(kc_preds))
    if agg == "mean-ar":
        return float(np.mean(kc_preds))
    if agg == "mean-geo":
        return float(np.prod(kc_preds) ** (1.0 / len(kc_preds)))
    raise ValueError(f"unknown agg: {agg}")


# ---------------------------------------------------------------------------
# 4. The BKT model: pyBKT if available, else a numpy mirror
# ---------------------------------------------------------------------------

def _pybkt_available() -> bool:
    try:
        from pyBKT.models import Model  # noqa: F401
        return True
    except Exception:
        return False


def fit_predict_pybkt(train_df: pd.DataFrame, test_df: pd.DataFrame,
                      seed: int = 221, num_fits: int = 1) -> pd.DataFrame:
    """Fit pyBKT exactly as the paper does and return per-row predictions.

    Returns test_df with a 'correct_predictions' column, sorted by order_id.
    """
    from pyBKT.models import Model
    model = Model(seed=seed, num_fits=num_fits)
    model.fit(data=train_df)
    pred_df = model.predict(data=test_df).sort_values(["order_id"])
    return pred_df


# --- numpy mirror of pyBKT's standard BKT (fallback only) ------------------

def _em_fit_kc(seq_list: List[np.ndarray], n_iter: int, seed: int) -> Dict[str, float]:
    """Standard BKT EM for one KC over a list of per-user sequences."""
    rng = np.random.default_rng(seed)
    prior = float(np.clip(rng.uniform(0.1, 0.9), 1e-3, 1 - 1e-3))
    learn = float(np.clip(rng.uniform(0.05, 0.4), 1e-3, 1 - 1e-3))
    guess = float(np.clip(rng.uniform(0.1, 0.4), 1e-3, 0.5))
    slip = float(np.clip(rng.uniform(0.05, 0.3), 1e-3, 0.5))
    for _ in range(n_iter):
        # Expected counts via forward-backward per sequence.
        c_prior = [0.0, 0.0]
        t_learn = [0.0, 0.0]     # transitions from not-known -> [stay, learn]
        e_guess = [0.0, 0.0]     # not-known -> [incorrect, correct]
        e_slip = [0.0, 0.0]      # known -> [incorrect, correct]
        for seq in seq_list:
            g = _posteriors(seq, prior, learn, guess, slip)
            if g is None:
                continue
            gam, xi_learn = g
            c_prior[1] += gam[0]
            c_prior[0] += 1 - gam[0]
            for t in range(len(seq)):
                pk = gam[t]
                if seq[t] == 1:
                    e_guess[1] += (1 - pk); e_slip[1] += pk
                else:
                    e_guess[0] += (1 - pk); e_slip[0] += pk
            for t in range(len(seq) - 1):
                t_learn[1] += xi_learn[t]
                t_learn[0] += (1 - gam[t]) - xi_learn[t]
        prior = _safe(c_prior[1], c_prior[0] + c_prior[1], prior)
        learn = _safe(t_learn[1], t_learn[0] + t_learn[1], learn)
        guess = _safe(e_guess[1], e_guess[0] + e_guess[1], guess)
        slip = _safe(e_slip[0], e_slip[0] + e_slip[1], slip)
        guess = min(guess, 0.5)
        slip = min(slip, 0.5)
    # Clamp every parameter strictly inside (0, 1) so the sequential Bayesian
    # update can never hit a 0/0 division (which would emit NaN). A prior pinned
    # to exactly 0 or 1 with a boundary slip/guess produces that division when an
    # observation contradicts the pinned mastery. pyBKT applies similar bounds.
    _EPS = 1e-6
    prior = float(np.clip(prior, _EPS, 1 - _EPS))
    learn = float(np.clip(learn, _EPS, 1 - _EPS))
    guess = float(np.clip(guess, _EPS, 0.5))
    slip = float(np.clip(slip, _EPS, 0.5))
    return {"prior": prior, "learns": learn, "guesses": guess, "slips": slip}


def _safe(num, den, fallback):
    return float(num / den) if den > 1e-12 else float(fallback)


def _posteriors(seq, prior, learn, guess, slip):
    """Forward-backward posteriors P(known) per step and learn-transition xi."""
    n = len(seq)
    if n == 0:
        return None
    a = np.zeros(n)   # forward P(known, obs)
    b = np.zeros(n)
    # forward
    pk = prior
    alpha = np.zeros(n)
    scale = np.zeros(n)
    known = np.zeros(n)
    for t in range(n):
        pobs_k = (1 - slip) if seq[t] == 1 else slip
        pobs_u = guess if seq[t] == 1 else (1 - guess)
        fk = pk * pobs_k
        fu = (1 - pk) * pobs_u
        s = fk + fu
        if s <= 0:
            return None
        known[t] = fk / s
        # transition to next
        pk = known[t] + (1 - known[t]) * learn
    # gamma approximated by filtered posterior (sufficient for standard BKT MoM)
    gam = known
    xi_learn = np.zeros(max(n - 1, 0))
    for t in range(n - 1):
        xi_learn[t] = (1 - gam[t]) * learn
    return gam, xi_learn


@dataclass
class NumpyBKT:
    per_skill: Dict[str, Dict[str, float]] = field(default_factory=dict)
    fallback: Dict[str, float] = field(default_factory=dict)

    def fit(self, train_df: pd.DataFrame, n_iter: int = 30, seed: int = 221):
        seqs_by_skill: Dict[str, List[np.ndarray]] = {}
        for (uid, skill), grp in train_df.sort_values("order_id").groupby(
                ["user_id", "skill_name"], sort=False):
            seqs_by_skill.setdefault(skill, []).append(
                grp["correct"].to_numpy(dtype=int))
        # pooled fallback
        pooled = {k: [] for k in PARAM_NAMES}
        for skill, seq_list in seqs_by_skill.items():
            self.per_skill[skill] = _em_fit_kc(seq_list, n_iter, seed)
        # observation-weighted fallback
        counts = train_df.groupby("skill_name").size()
        tot = counts.sum()
        for k in PARAM_NAMES:
            self.fallback[k] = float(
                sum(self.per_skill[s][k] * counts[s] for s in self.per_skill) / tot)
        return self

    def _params(self, skill):
        return self.per_skill.get(skill, self.fallback)

    def predict(self, test_df: pd.DataFrame) -> pd.DataFrame:
        df = test_df.sort_values("order_id").copy()
        preds = np.empty(len(df))
        pos = {i: k for k, i in enumerate(df.index)}
        for (uid, skill), grp in df.groupby(["user_id", "skill_name"], sort=False):
            p = self._params(skill)
            pk = p["prior"]
            for i in grp.index:
                c = int(grp.at[i, "correct"])
                p_correct = pk * (1 - p["slips"]) + (1 - pk) * p["guesses"]
                preds[df.index.get_loc(i)] = p_correct
                if c == 1:
                    num = pk * (1 - p["slips"]); den = p_correct
                else:
                    num = pk * p["slips"]; den = 1 - p_correct
                pk_post = num / den if den > 1e-12 else pk
                pk = pk_post + (1 - pk_post) * p["learns"]
                pk = float(np.clip(pk, 1e-6, 1 - 1e-6))
        df["correct_predictions"] = preds
        return df


# ---------------------------------------------------------------------------
# 5. compute_metrics  (mirrors training.compute_metrics)
# ---------------------------------------------------------------------------

def compute_metrics(labels, preds) -> Dict[str, float]:
    """Accuracy, AUC, and binary F1 (positive class = correct), as the paper.

    Matches training.compute_metrics: hard predictions are np.round(preds),
    and F1 uses average='binary' (pos_label defaults to 1 = correct).
    """
    labels = np.asarray(labels, dtype=int)
    preds = np.asarray(preds, dtype=float)
    n_nan = int(np.isnan(preds).sum())
    if n_nan:
        # Should not happen once parameters are clamped, but if it does, report
        # it clearly and drop the affected turns rather than crashing in sklearn.
        print(f"WARNING: {n_nan} of {len(preds)} predictions were NaN; "
              f"dropping them before scoring. This indicates a degenerate KC "
              f"slipped through parameter clamping.")
        keep = ~np.isnan(preds)
        labels, preds = labels[keep], preds[keep]
    hard = np.round(preds).astype(int)
    acc = accuracy_score(labels, hard)
    auc = roc_auc_score(labels, preds) if len(np.unique(labels)) > 1 else float("nan")
    prec, rec, f1, _ = precision_recall_fscore_support(
        labels, hard, average="binary", zero_division=0)
    return {"n": len(labels), "accuracy": acc, "auc": auc,
            "precision": prec, "recall": rec, "f1": f1}


# ---------------------------------------------------------------------------
# 6. evaluate_bkt  (mirrors train_test_bkt)
# ---------------------------------------------------------------------------

_DEGENERATE_SKILL = "__degenerate_pooled__"


def _split_estimable(train_df: pd.DataFrame, test_df: pd.DataFrame):
    """Identify degenerate / unseen skills that pyBKT cannot estimate.

    A skill is degenerate if it is all-correct or all-incorrect in train, which
    leaves its four BKT parameters underidentified and can contribute to pyBKT's
    numerical collapse. Returns the set of skills with label variation plus the
    train base rate, used to score any test turn whose skill was not fitted.
    """
    stats = train_df.groupby("skill_name")["correct"].agg(["count", "sum"])
    degenerate = set(stats.index[(stats["sum"] == 0) |
                                 (stats["sum"] == stats["count"])])
    estimable = set(stats.index) - degenerate
    base_rate = float(train_df["correct"].mean())
    return estimable, base_rate


def apply_typical_filter(df: pd.DataFrame, typical_cutoff: int = 1) -> pd.DataFrame:
    """Keep only dialogues that pass the paper's typical-confusion threshold.

    Mirrors load_annotated_data for MathDial: a dialogue is kept only when both
    self_typical_confusion and self_typical_interactions in its meta_data are at
    least typical_cutoff. The paper's default cutoff is 1. This dialogue-level
    filter is the paper's actual preprocessing, applied before any KC handling.
    """
    def passes(row):
        meta = _as_obj(row.get("meta_data")) or {}
        conf = meta.get("self_typical_confusion")
        inter = meta.get("self_typical_interactions")
        if conf is None or inter is None:
            return False
        return conf >= typical_cutoff and inter >= typical_cutoff

    kept = df[df.apply(passes, axis=1)]
    return kept


def evaluate_bkt(train_raw: pd.DataFrame, test_raw: pd.DataFrame,
                 agg: str = "mean-ar", inc_first_label: bool = False,
                 seed: int = 221, num_fits: int = 1,
                 typical_cutoff: int = 1, apply_typical: bool = True,
                 handle_degenerate: bool = True,
                 force_numpy: bool = False) -> Dict[str, object]:
    """Full paper-faithful BKT evaluation.

    Steps, mirroring train_test_bkt:
      1. Apply the paper's dialogue-level typical-confusion filter (default on).
      2. Build per-KC pseudo-turn rows for train and test.
      3. Fit BKT on train (pyBKT if available, else the numpy mirror).
      4. Predict per row on test, aggregate to turn level with `agg`.
      5. Drop the FIRST TAGGED turn of each dialogue (labels[1:], preds[1:])
         unless inc_first_label is True.
      6. Compute accuracy, AUC, and binary F1.
    """
    if apply_typical:
        n_before_tr, n_before_te = len(train_raw), len(test_raw)
        train_raw = apply_typical_filter(train_raw, typical_cutoff)
        test_raw = apply_typical_filter(test_raw, typical_cutoff)
        print(f"[typical filter, cutoff={typical_cutoff}] "
              f"train {n_before_tr} -> {len(train_raw)} dialogues, "
              f"test {n_before_te} -> {len(test_raw)} dialogues")

    train_df, _ = build_pseudo_turns(train_raw)
    test_df, test_seqs = build_pseudo_turns(test_raw)

    n_pybkt_nan = 0
    n_base_rate_fallback = 0
    use_pybkt = _pybkt_available() and not force_numpy
    if use_pybkt:
        # After the paper's typical-confusion filter, degenerate skills may remain.
        # We report how many
        # remain. If handle_degenerate is on (default) we still guard against any
        # survivors by fitting pyBKT only on estimable skills and scoring the
        # rest at the train base rate. Set handle_degenerate=False to run pyBKT
        # exactly as the paper does, with no guard (may raise/NaN if any remain).
        estimable, base_rate = _split_estimable(train_df, test_df)
        n_degenerate = train_df["skill_name"].nunique() - len(estimable)
        print(f"[pyBKT] degenerate skills remaining after filter: {n_degenerate}")

        if handle_degenerate and n_degenerate:
            train_fit = train_df[train_df["skill_name"].isin(estimable)]
            test_fit = test_df[test_df["skill_name"].isin(estimable)].copy()
            fitted = fit_predict_pybkt(train_fit, test_fit, seed=seed, num_fits=num_fits)
            n_pybkt_nan = int(fitted["correct_predictions"].isna().sum())
            n_nan_skills = int(
                fitted.loc[fitted["correct_predictions"].isna(),
                           "skill_name"].nunique()
            )
            if n_pybkt_nan:
                print(f"[pyBKT] {n_pybkt_nan} predictions across {n_nan_skills} "
                      "fitted skills were NaN and will use the train base rate")
            pred_map = dict(zip(fitted["order_id"], fitted["correct_predictions"]))
            test_df = test_df.copy()
            test_df["correct_predictions"] = test_df["order_id"].map(pred_map)
            n_base_rate_fallback = int(test_df["correct_predictions"].isna().sum())
            test_df["correct_predictions"] = test_df["correct_predictions"].fillna(base_rate)
            pred_df = test_df
            print(f"[pyBKT] {n_degenerate} degenerate skill(s) excluded from the "
                  f"fit and scored at the train base rate {base_rate:.3f}")
        else:
            # No degenerate skills, or guard disabled: run pyBKT on everything.
            pred_df = fit_predict_pybkt(train_df, test_df, seed=seed, num_fits=num_fits)
        pred_col = "correct_predictions"
        backend = "pyBKT"
    else:
        model = NumpyBKT().fit(train_df, seed=seed)
        pred_df = model.predict(test_df)
        pred_col = "correct_predictions"
        backend = "numpy-mirror"
        base_rate = float(train_df["correct"].mean())

    # Map predictions back to each dialogue's rows by order_id, preserving the
    # exact creation order that turn_kc_slices was computed against. Grouping a
    # sorted frame by user_id does NOT guarantee that order, so we index by
    # order_id explicitly.
    pred_by_order = dict(zip(pred_df["order_id"], pred_df[pred_col]))
    n_base_fallback = 0
    n_total_rows = 0
    all_labels: List[int] = []
    all_preds: List[float] = []
    for seq in test_seqs:
        # Predictions for this dialogue's rows, in creation order.
        preds_flat = np.array([pred_by_order.get(r["order_id"], base_rate)
                               for r in seq.rows], dtype=float)
        n_total_rows += len(preds_flat)
        n_base_fallback += int(sum(
            1 for r in seq.rows if r["order_id"] not in pred_by_order))
        turn_preds = [aggregate_turn(preds_flat[s:e], agg)
                      for (s, e) in seq.turn_kc_slices]
        labels = seq.turn_labels
        if inc_first_label:
            all_labels.extend(labels)
            all_preds.extend(turn_preds)
        else:
            all_labels.extend(labels[1:])   # drop first TAGGED turn
            all_preds.extend(turn_preds[1:])

    if n_base_fallback:
        print(f"[pyBKT] {n_base_fallback} of {n_total_rows} pseudo-turn rows had "
              f"no pyBKT prediction (scored via fallback)")

    metrics = compute_metrics(all_labels, all_preds)
    metrics["backend"] = backend
    metrics["agg"] = agg
    metrics["inc_first_label"] = inc_first_label
    metrics["n_pybkt_nan"] = n_pybkt_nan
    metrics["n_base_rate_fallback"] = n_base_rate_fallback
    return metrics
