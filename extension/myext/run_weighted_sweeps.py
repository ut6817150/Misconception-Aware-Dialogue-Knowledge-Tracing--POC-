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
from myext import bkt_design6 as d6
from myext import bkt_design7 as d7

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
    """Design 5 sweep: tempered POOLED emission (correctness vs misconception)."""
    splits = splits or d5.DEFAULT_SPLITS
    records = []
    baseline_auc = {}
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
                design="D5 tempered pooled", granularity=gran, split=f"{sp[0]}-{sp[1]}",
                corr_weight=sp[0], misc_weight=sp[1], w_c=f.w_c, w_m=f.w_m, auc=a,
                delta_vs_baseline=a - baseline_auc[gran]))
    return pd.DataFrame.from_records(records)


def run_sweep_d6(train_long, test_long, splits=None,
                 granularities=("binary", "trinary"),
                 n_restarts: int = 4, seed: int = 221) -> pd.DataFrame:
    """Design 6 sweep: tempered FAMILY-CONDITIONED emission (correctness vs
    misconception, with family-specific mu). Same axis as D5, family-specific."""
    splits = splits or d6.DEFAULT_SPLITS
    records = []
    baseline_auc = {}
    for gran in granularities:
        f = d6.fit_design6(train_long, gran, split=(100, 0),
                           n_restarts=n_restarts, seed=seed, verbose=False)
        baseline_auc[gran] = auc_of(f.predict_long(test_long))
    for gran in granularities:
        for sp in splits:
            f = d6.fit_design6(train_long, gran, split=sp,
                               n_restarts=n_restarts, seed=seed, verbose=False)
            a = auc_of(f.predict_long(test_long))
            records.append(dict(
                design="D6 tempered family", granularity=gran, split=f"{sp[0]}-{sp[1]}",
                corr_weight=sp[0], misc_weight=sp[1], w_c=f.w_c, w_m=f.w_m, auc=a,
                delta_vs_baseline=a - baseline_auc[gran]))
    return pd.DataFrame.from_records(records)


def run_sweep_d7(train_long, test_long, lambdas=None,
                 granularities=("binary", "trinary"),
                 n_restarts: int = 4, seed: int = 221) -> pd.DataFrame:
    """Design 7 sweep: PARTIAL POOLING (pooled D1 emission <-> family-specific
    D2a emission) at FIXED correctness-vs-misconception balance. Different axis
    from D5/D6: holds the channel at full strength, varies family-specificity."""
    lambdas = lambdas if lambdas is not None else d7.DEFAULT_LAMBDAS
    records = []
    for gran in granularities:
        fitted = d7.fit_design7(train_long, gran, n_restarts=n_restarts,
                                seed=seed, verbose=False)
        sweep = fitted.evaluate_sweep(test_long, lambdas=lambdas)
        base = sweep[sweep["lambda"] == 0.0]["AUC"].iloc[0]
        for _, r in sweep.iterrows():
            records.append(dict(
                design="D7 partial pooling", granularity=gran,
                lam=float(r["lambda"]), auc=float(r["AUC"]),
                delta_vs_pooled=float(r["AUC"]) - base))
    return pd.DataFrame.from_records(records)


def main():
    train_long, test_long = load_long_frames()

    df5 = run_sweep(train_long, test_long)
    df6 = run_sweep_d6(train_long, test_long)
    df7 = run_sweep_d7(train_long, test_long)

    # ---- D5 and D6 share the correctness-vs-misconception axis ----
    for name, df in [("D5 tempered pooled", df5), ("D6 tempered family", df6)]:
        print(f"\n=== {name} (correctness-vs-misconception split) ===")
        for gran in df["granularity"].unique():
            sub = df[df["granularity"] == gran].sort_values("misc_weight")
            print(f"  -- {gran} --")
            print(sub[["split", "w_c", "w_m", "auc", "delta_vs_baseline"]]
                  .to_string(index=False, float_format=lambda x: f"{x:.4f}"))

    # ---- D7 is the partial-pooling axis ----
    print("\n=== D7 partial pooling (pooled emission <-> family-specific) ===")
    for gran in df7["granularity"].unique():
        sub = df7[df7["granularity"] == gran].sort_values("lam")
        print(f"  -- {gran} --")
        print(sub[["lam", "auc", "delta_vs_pooled"]]
              .to_string(index=False, float_format=lambda x: f"{x:.4f}"))

    df5.to_csv("design5_sweep.csv", index=False)
    df6.to_csv("design6_sweep.csv", index=False)
    df7.to_csv("design7_sweep.csv", index=False)
    print("\nwrote design5_sweep.csv, design6_sweep.csv, design7_sweep.csv")

    # plots
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        # D5 and D6 on the misconception-weight axis
        fig, ax = plt.subplots(figsize=(7, 4.5))
        for df, lab, mk in [(df5, "D5 pooled", "o"), (df6, "D6 family", "s")]:
            for gran in df["granularity"].unique():
                sub = df[df["granularity"] == gran].sort_values("misc_weight")
                ax.plot(sub["misc_weight"], sub["auc"], marker=mk,
                        label=f"{lab} ({gran})")
        ax.set_xlabel("misconception weight (%)  [0 = correctness only]")
        ax.set_ylabel("next-turn AUC")
        ax.set_title("Tempered emission sweeps (D5 pooled, D6 family-conditioned)")
        ax.legend(fontsize=8); fig.tight_layout()
        fig.savefig("design56_sweep.png", dpi=140)

        # D7 on the lambda axis
        fig2, ax2 = plt.subplots(figsize=(7, 4.5))
        for gran in df7["granularity"].unique():
            sub = df7[df7["granularity"] == gran].sort_values("lam")
            ax2.plot(sub["lam"], sub["auc"], marker="o", label=gran)
        ax2.set_xlabel("lambda  [0 = pooled (D1 emission), 1 = family-specific (D2a)]")
        ax2.set_ylabel("next-turn AUC")
        ax2.set_title("Design 7: partial-pooling sweep")
        ax2.legend(); fig2.tight_layout()
        fig2.savefig("design7_sweep.png", dpi=140)
        print("wrote design56_sweep.png, design7_sweep.png")
    except Exception as e:
        print(f"(plots skipped: {e})")


if __name__ == "__main__":
    main()
