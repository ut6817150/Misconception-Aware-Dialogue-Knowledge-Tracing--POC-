"""Numerical safeguards and auditing for the paper's pyBKT evaluation.

Data preparation, BKT construction, and metric definitions are imported
directly from the paper's ``dialogue_kt`` package by the calling notebook. This
module contains only the additional behavior that is not in the paper:

* exclude all-correct and all-incorrect KCs from the pyBKT fit;
* replace predictions for degenerate, unseen, or numerically invalid KCs with
  the training pseudo-observation correctness rate;
* report the number of affected pseudo-observations.
"""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd
from dialogue_kt.training import compute_metrics as paper_compute_metrics
from pyBKT.models import Model


def _aggregate_turn(kc_predictions: np.ndarray, method: str) -> float:
    """Apply one of the aggregation formulas from paper ``train_test_bkt``."""
    if method == "prod":
        return float(np.prod(kc_predictions))
    if method == "mean-ar":
        return float(np.mean(kc_predictions))
    if method == "mean-geo":
        return float(np.prod(kc_predictions) ** (1 / len(kc_predictions)))
    raise ValueError(f"Unknown aggregation method: {method}")


def evaluate_with_base_rate_guard(
    train_pseudo: pd.DataFrame,
    test_pseudo: pd.DataFrame,
    test_dataset,
    *,
    aggregation: str = "mean-ar",
    include_first_label: bool = False,
    seed: int = 221,
    num_fits: int = 1,
) -> Dict[str, object]:
    """Run the paper's pyBKT model with a fully reported base-rate safeguard.

    ``train_pseudo``, ``test_pseudo``, and ``test_dataset`` must be the direct
    outputs of ``dialogue_kt.training.bkt_prep_data``. Turn reconstruction and
    first-label removal follow ``dialogue_kt.training.train_test_bkt``.
    """
    stats = train_pseudo.groupby("skill_name")["correct"].agg(["count", "sum"])
    degenerate = set(
        stats.index[(stats["sum"] == 0) | (stats["sum"] == stats["count"])]
    )
    estimable = set(stats.index) - degenerate
    base_rate = float(train_pseudo["correct"].mean())

    train_fit = train_pseudo[train_pseudo["skill_name"].isin(estimable)]
    test_fit = test_pseudo[test_pseudo["skill_name"].isin(estimable)]

    print(f"[pyBKT] degenerate skills remaining after filter: {len(degenerate)}")
    model = Model(seed=seed, num_fits=num_fits)
    model.fit(data=train_fit)
    fitted_predictions = model.predict(data=test_fit).sort_values("order_id")

    n_pybkt_nan = int(fitted_predictions["correct_predictions"].isna().sum())
    n_nan_skills = int(
        fitted_predictions.loc[
            fitted_predictions["correct_predictions"].isna(), "skill_name"
        ].nunique()
    )
    if n_pybkt_nan:
        print(
            f"[pyBKT] {n_pybkt_nan} predictions across {n_nan_skills} "
            "fitted skills were NaN and will use the train base rate"
        )

    prediction_by_order = dict(
        zip(
            fitted_predictions["order_id"],
            fitted_predictions["correct_predictions"],
        )
    )
    guarded = test_pseudo.copy()
    guarded["correct_predictions"] = guarded["order_id"].map(prediction_by_order)
    n_base_rate_fallback = int(guarded["correct_predictions"].isna().sum())
    guarded["correct_predictions"] = guarded["correct_predictions"].fillna(
        base_rate
    )

    print(
        f"[pyBKT] {len(degenerate)} degenerate skill(s) excluded from the fit "
        f"and scored at the train base rate {base_rate:.3f}"
    )

    all_labels = []
    all_predictions = []
    for sample in test_dataset:
        user_predictions = (
            guarded.loc[
                guarded["user_id"].eq(sample["dialogue_idx"]),
                "correct_predictions",
            ]
            .to_numpy(dtype=float)
        )
        turn_predictions = []
        previous_end = -1
        for turn_end in sample["turn_end_idxs"]:
            start = previous_end + 1
            turn_predictions.append(
                _aggregate_turn(
                    user_predictions[start : turn_end + 1], aggregation
                )
            )
            previous_end = turn_end

        if include_first_label:
            all_labels.extend(sample["labels"])
            all_predictions.extend(turn_predictions)
        else:
            all_labels.extend(sample["labels"][1:])
            all_predictions.extend(turn_predictions[1:])

    accuracy, auc, precision, recall, f1 = paper_compute_metrics(
        all_labels, all_predictions
    )
    return {
        "n": len(all_labels),
        "accuracy": accuracy / 100,
        "auc": auc / 100,
        "precision": precision / 100,
        "recall": recall / 100,
        "f1": f1 / 100,
        "aggregation": aggregation,
        "include_first_label": include_first_label,
        "n_degenerate_skills": len(degenerate),
        "n_pybkt_nan": n_pybkt_nan,
        "n_base_rate_fallback": n_base_rate_fallback,
        "base_rate": base_rate,
    }
