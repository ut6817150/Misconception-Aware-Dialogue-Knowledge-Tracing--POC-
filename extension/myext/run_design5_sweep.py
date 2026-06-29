"""
run_design5_sweep.py

Tempered-emission (Design 5) split experiment. Sweeps the correctness vs
misconception weight split and reports next-turn AUC at each split, for both
granularities, against the correctness-only baseline (the 100-0 endpoint).

Run from the extension directory (so `myext` is importable):
    python run_design5_sweep.py

It expects the misconception-labelled long-format train/test frames the other
designs use. Adjust load_long_frames() to point at your data if needed; by
default it mirrors how 04_modelling.ipynb builds train_long / test_long.

Outputs:
  - a printed table of AUC by split and granularity
  - design5_sweep.csv  (split, granularity, auc, delta_vs_baseline, w_c, w_m)
  - design5_sweep.png   (AUC vs misconception weight, one line per granularity)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from myext import bkt_design5 as d5

try:
    from sklearn.metrics import roc_auc_score
except Exception:  # pragma: no cover
    roc_auc_score = None


# ---------------------------------------------------------------------------
# Data loading. Replace the body of this function with however 04_modelling
# constructs train_long / test_long (same frames the other designs consume).
# Required columns: dialogue_idx, turn, correct, kc, misc, family.
# ---------------------------------------------------------------------------
def load_long_frames():
    """Return (train_long, test_long).

    Default implementation reads the cached misconception-labelled frames if
    present; otherwise raises with a clear message so you can wire in the same
    loader 04_modelling uses.
    """
    import os
    candidates = [
        ("artifacts/train_long_mc.parquet", "artifacts/test_long_mc.parquet"),
        ("artifacts/train_long_mc.csv", "artifacts/test_long_mc.csv"),
    ]
    for tr, te in candidates:
        if os.path.exists(tr) and os.path.exists(te):
            rd = pd.read_parquet if tr.endswith(".parquet") else pd.read_csv
            return rd(tr), rd(te)
    raise FileNotFoundError(
        "Could not find cached long frames. Edit load_long_frames() to build "
        "train_long / test_long exactly as 04_modelling.ipynb does (the same "
        "frames passed to fit_design1), then re-run."
    )


def auc_of(pred_df: pd.DataFrame) -> float:
    if roc_auc_score is None:
        raise RuntimeError("scikit-learn is required for AUC.")
    y = pred_df["correct"].to_numpy(dtype=int)
    p = pred_df["pred"].to_numpy(dtype=float)
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc_score(y, p))


def run_sweep(train_long, test_long, splits=None, granularities=("binary", "trinary"),
              n_restarts: int = 4, seed: int = 221) -> pd.DataFrame:
    splits = splits or d5.DEFAULT_SPLITS
    records = []
    baseline_auc = {}

    # baseline = the 100-0 endpoint for each granularity (correctness only)
    for gran in granularities:
        f = d5.fit_design5(train_long, gran, split=(100, 0),
                           n_restarts=n_restarts, seed=seed, verbose=False)
        baseline_auc[gran] = auc_of(f.predict_long(test_long))

    for gran in granularities:
        for sp in splits:
            f = d5.fit_design5(train_long, gran, split=sp,
                               n_restarts=n_restarts, seed=seed, verbose=False)
            a = auc_of(f.predict_long(test_long))
            records.append(dict(
                granularity=gran, split=f"{sp[0]}-{sp[1]}",
                corr_weight=sp[0], misc_weight=sp[1],
                w_c=f.w_c, w_m=f.w_m, auc=a,
                delta_vs_baseline=a - baseline_auc[gran],
            ))
    return pd.DataFrame.from_records(records)


def main():
    train_long, test_long = load_long_frames()
    df = run_sweep(train_long, test_long)

    # tidy print
    for gran in df["granularity"].unique():
        sub = df[df["granularity"] == gran].sort_values("misc_weight")
        print(f"\n=== {gran} ===")
        print(sub[["split", "w_c", "w_m", "auc", "delta_vs_baseline"]]
              .to_string(index=False, float_format=lambda x: f"{x:.4f}"))

    df.to_csv("design5_sweep.csv", index=False)
    print("\nwrote design5_sweep.csv")

    # plot
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7, 4.5))
        for gran in df["granularity"].unique():
            sub = df[df["granularity"] == gran].sort_values("misc_weight")
            ax.plot(sub["misc_weight"], sub["auc"], marker="o", label=gran)
        ax.axhline(df[df["split"] == "100-0"]["auc"].iloc[0], ls=":", c="grey",
                   lw=1, label="baseline (100-0)")
        ax.set_xlabel("misconception weight (%)  [0 = correctness only, 100 = misconception only]")
        ax.set_ylabel("next-turn AUC")
        ax.set_title("Design 5: tempered-emission split sweep")
        ax.legend()
        fig.tight_layout()
        fig.savefig("design5_sweep.png", dpi=140)
        print("wrote design5_sweep.png")
    except Exception as e:
        print(f"(plot skipped: {e})")


if __name__ == "__main__":
    main()
