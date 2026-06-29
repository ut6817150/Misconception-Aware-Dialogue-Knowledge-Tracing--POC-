"""
myext/labels_io.py

Persists the extracted misconception labels to a data subfolder and joins them
onto the correctness/KC long table for modelling.

Saved format: one CSV per split at data/misconception/{split}_labels.csv, with
columns dialogue_id, turn, misc, family. Rewritten in full each run (overwrite),
so re-running the extraction notebook refreshes the saved labels.

The family is the misconception family of the dialogue, derived from the
student_profile via the same mapping used in the EDA. Design 2a conditions on
it; Design 1 ignores it.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict

import pandas as pd


MISC_DIR = Path("data/misconception")


# ---------------------------------------------------------------------------
# Family mapping (same six families as the EDA / report)
# ---------------------------------------------------------------------------

def family_of(profile: str) -> str:
    """Map a student_profile sentence to one of six families (A-F), else OTHER.
    Mirrors the mapping established in the EDA.
    """
    t = re.sub(r"^[A-Za-z]+ is a [^.]+\.\s*", "", str(profile).strip()).lower()
    if "what the problem is asking" in t or "what the question is asking" in t:
        return "A"
    if "underlying ideas" in t or "principles" in t or "when to apply" in t:
        return "B"
    if "relevant" in t and "irrelevant" in t:
        return "C"
    if "correct order" in t or "correct operation" in t or "wrong operation" in t:
        return "D"
    if "steps or procedures" in t or "which steps" in t:
        return "E"
    if "recognize the problem type" in t or "recognise the problem type" in t:
        return "F"
    return "OTHER"


# ---------------------------------------------------------------------------
# Saving
# ---------------------------------------------------------------------------

def save_labels(split: str, extracted: Dict[int, dict], df,
                misc_dir: Path = MISC_DIR) -> str:
    """Flatten {dialogue_id: {turn_key: {label,...}}} to a per-turn CSV and
    write it, overwriting any existing file for this split.

    df is the dialogue dataframe (indexed by dialogue id) for the family lookup.
    Dialogues that failed extraction are skipped (and counted in the print).
    """
    rows = []
    n_fail = 0
    for did, labels in extracted.items():
        if "_error" in labels:
            n_fail += 1
            continue
        fam = family_of(df.loc[did, "student_profile"])
        for turn_key, entry in labels.items():
            if not isinstance(entry, dict) or "label" not in entry:
                continue
            rows.append({
                "dialogue_id": did,
                "turn": turn_key,
                "misc": entry["label"],
                "family": fam,
            })
    out = pd.DataFrame(rows)
    misc_dir = Path(misc_dir)
    misc_dir.mkdir(parents=True, exist_ok=True)
    path = misc_dir / f"{split}_labels.csv"
    out.to_csv(path, index=False)       # overwrite
    print(f"saved {len(out)} turn-labels for {split} -> {path}"
          + (f"  ({n_fail} dialogues skipped: extraction failed)" if n_fail else ""))
    return str(path)


# ---------------------------------------------------------------------------
# Loading and joining
# ---------------------------------------------------------------------------

def load_labels(split: str, misc_dir: Path = MISC_DIR) -> pd.DataFrame:
    path = Path(misc_dir) / f"{split}_labels.csv"
    if not path.exists():
        raise FileNotFoundError(f"No saved labels at {path}; run the extraction "
                                f"notebook first.")
    return pd.read_csv(path)


def join_misc(long_df: pd.DataFrame, labels_df: pd.DataFrame) -> pd.DataFrame:
    """Attach misc + family to the correctness/KC long table by (dialogue, turn).

    The misconception label is per-turn, so it broadcasts across the several KC
    rows a turn produces. Turns with no extracted label (should be none if the
    same dialogues were extracted) default to not_evidenced + family from a
    per-dialogue fill.
    """
    merged = long_df.merge(
        labels_df[["dialogue_id", "turn", "misc", "family"]],
        left_on=["dialogue_idx", "turn"], right_on=["dialogue_id", "turn"],
        how="left",
    ).drop(columns=["dialogue_id"])

    # fill family per dialogue where the merge missed (e.g. a turn with no label)
    fam_by_dia = (labels_df.groupby("dialogue_id")["family"].first())
    miss_fam = merged["family"].isna()
    merged.loc[miss_fam, "family"] = merged.loc[miss_fam, "dialogue_idx"].map(fam_by_dia)
    merged["family"] = merged["family"].fillna("OTHER")
    merged["misc"] = merged["misc"].fillna("not_evidenced")
    return merged
