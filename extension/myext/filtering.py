"""
myext/filtering.py

Knowledge-component (KC) filtering for the dialogue-KT experiment.

The filter decides which KCs to keep using TRAINING-SPLIT statistics only,
then applies that keep-set to any split (train or test). This separation is
deliberate: deciding the keep-set from test data would leak information from
the held-out set into preprocessing.

Two criteria, combined:
  - drop_no_variation: remove KCs that are all-correct or all-incorrect in
    train (no label variation). These are un-estimable for BKT and cause the
    EM initial-state estimate to divide by zero. This is the primary,
    model-theoretically justified filter.
  - min_count k: remove KCs observed fewer than k times in train. With k=1
    this criterion is inactive (every observed KC has count >= 1), so the
    degenerate-only filter is the call drop_no_variation=True, min_count=1.

The same function powers the later sensitivity sweep: call it with
min_count in {2, 3, 5, 10} to filter more aggressively, reporting that the
conclusions do not depend on the threshold. The threshold is never selected
by performance.

Separately, drop_failed_annotations removes dialogues whose GPT-4o annotation
failed (recorded as an error dict with no usable turns), at the raw-dataframe
level before flattening. This matches the original work, which removed
dialogues where the annotation of correctness and KCs failed. It is a data
provenance step, not a modelling filter: these dialogues have no labels at all
and cannot be used by any KT model.
"""

from __future__ import annotations

from ast import literal_eval
from dataclasses import dataclass, field
from typing import Set, List, Tuple

import pandas as pd


# ---------------------------------------------------------------------------
# Annotation-failure removal (raw-dataframe level, before flattening)
# ---------------------------------------------------------------------------

def _usable_annotation(ann) -> bool:
    """True if the annotation has at least one turn with both 'correct' and
    'kcs'. GPT-4o annotation failures are recorded as an error dict, e.g.
    {'error': 'Different number of standard and correctness output turns'},
    which has no such turn and returns False.
    """
    if isinstance(ann, str):
        try:
            ann = literal_eval(ann)
        except Exception:
            return False
    if not isinstance(ann, dict) or len(ann) == 0:
        return False
    return any(
        isinstance(info, dict) and "correct" in info and "kcs" in info
        for info in ann.values()
    )


def drop_failed_annotations(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Remove dialogues whose annotation failed (no usable labelled turns).

    Operates on the raw released dataframe (with an 'annotation' column),
    before flattening to the long format. Returns (filtered_df, n_removed).
    Matches the original work's removal of failed-annotation dialogues, so the
    dialogue counts align (e.g. 2253 -> 2235 on the MathDial train split).
    """
    mask = df["annotation"].apply(_usable_annotation)
    n_removed = int((~mask).sum())
    return df[mask].reset_index(drop=True), n_removed


# ---------------------------------------------------------------------------
# The long-format observation table this module operates on has one row per
# (dialogue, turn, KC) with columns: dialogue_idx, turn, correct, kc.
# (This is the flattened view produced by the EDA's turn_table helper.)
# ---------------------------------------------------------------------------


@dataclass
class FilterResult:
    """Outcome of a filtering operation, for reporting."""

    keep_kcs: Set[str]
    dropped_kcs: List[str] = field(default_factory=list)
    n_kcs_before: int = 0
    n_kcs_after: int = 0
    n_obs_before: int = 0
    n_obs_after: int = 0
    reason_counts: dict = field(default_factory=dict)

    def summary(self) -> str:
        pct = (
            100.0 * (self.n_obs_before - self.n_obs_after) / self.n_obs_before
            if self.n_obs_before
            else 0.0
        )
        lines = [
            f"KCs: {self.n_kcs_before} -> {self.n_kcs_after} "
            f"(dropped {self.n_kcs_before - self.n_kcs_after})",
            f"observations: {self.n_obs_before} -> {self.n_obs_after} "
            f"(removed {self.n_obs_before - self.n_obs_after}, {pct:.2f}%)",
        ]
        if self.reason_counts:
            reasons = ", ".join(f"{k}={v}" for k, v in self.reason_counts.items())
            lines.append(f"drop reasons: {reasons}")
        return "\n".join(lines)


def determine_keep_set(
    train_long: pd.DataFrame,
    drop_no_variation: bool = True,
    min_count: int = 1,
) -> FilterResult:
    """Determine which KCs to keep, using TRAIN statistics only.

    Parameters
    ----------
    train_long : DataFrame
        Long-format training observations (one row per (dialogue, turn, kc)),
        with at least columns 'kc' and 'correct'.
    drop_no_variation : bool
        If True, drop KCs that are all-correct or all-incorrect in train.
    min_count : int
        Drop KCs observed fewer than this many times in train. k=1 is a no-op.

    Returns
    -------
    FilterResult with the keep-set and reporting fields.
    """
    stats = train_long.groupby("kc")["correct"].agg(n="count", n_correct="sum")

    no_variation = (stats["n_correct"] == 0) | (stats["n_correct"] == stats["n"])
    below_count = stats["n"] < min_count

    drop_mask = below_count.copy()
    if drop_no_variation:
        drop_mask = drop_mask | no_variation

    dropped = sorted(stats.index[drop_mask].tolist())
    keep = set(stats.index[~drop_mask].tolist())

    reason_counts = {}
    if drop_no_variation:
        reason_counts["no_variation"] = int(no_variation.sum())
    if min_count > 1:
        reason_counts["below_min_count"] = int(below_count.sum())

    return FilterResult(
        keep_kcs=keep,
        dropped_kcs=dropped,
        n_kcs_before=int(stats.shape[0]),
        n_kcs_after=len(keep),
        n_obs_before=int(stats["n"].sum()),
        n_obs_after=int(stats.loc[list(keep), "n"].sum()) if keep else 0,
        reason_counts=reason_counts,
    )


def apply_keep_set(long_df: pd.DataFrame, keep_kcs: Set[str]) -> pd.DataFrame:
    """Filter a long-format observation table to a keep-set of KCs.

    Applied identically to train and test. Test turns whose KC is not in the
    keep-set are removed from the per-KC observations here; the model's
    handling of such turns at prediction time (the unseen-KC fallback) is the
    responsibility of the model module, not the filter.
    """
    return long_df[long_df["kc"].isin(keep_kcs)].copy()


def filter_splits(
    train_long: pd.DataFrame,
    test_long: pd.DataFrame,
    drop_no_variation: bool = True,
    min_count: int = 1,
):
    """Convenience: determine keep-set from train, apply to both splits.

    Returns (train_filtered, test_filtered, FilterResult). The FilterResult's
    observation counts refer to the TRAIN split (where the keep-set is
    decided). The number of test observations dropped is reported separately
    by the caller if needed, since those become unseen-KC turns at test time.
    """
    result = determine_keep_set(
        train_long, drop_no_variation=drop_no_variation, min_count=min_count
    )
    train_f = apply_keep_set(train_long, result.keep_kcs)
    test_f = apply_keep_set(test_long, result.keep_kcs)
    return train_f, test_f, result