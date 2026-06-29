"""
myext/validation_set.py

Builds the human annotation instrument for the frozen validation set, and
loads the labels back once filled in.

export_validation_csv writes one row per student turn, with everything an
annotator needs to label it: the problem, the misconception in plain language,
the dialogue history up to and including the turn, and an empty 'label' column.
The annotator fills 'label' with present / absent / not_evidenced from the
codebook, offline, and saves the file.

load_validation_labels reads the filled-in file back into the
{(dialogue_id, turn_key): label} form the agreement module expects, scoring
only the rows that have been labelled (so it works on a partially-labelled
file and grows as labelling proceeds).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


VALID_LABELS = {"present", "absent", "not_evidenced"}


def _history_up_to(dialogue: List[dict], turn_n: int) -> str:
    """Dialogue text up to and including the given student turn."""
    lines = []
    for entry in dialogue:
        t = entry.get("turn")
        if t is None or t > turn_n:
            continue
        teacher = (entry.get("teacher") or "").strip()
        student = (entry.get("student") or "").strip()
        if teacher:
            lines.append(f"Tutor: {teacher}")
        marker = "  <-- LABEL THIS TURN" if t == turn_n else ""
        lines.append(f"Student (turn {t}): {student}{marker}")
    return "\n".join(lines)


def export_validation_csv(df, validation_ids: List[int], path: str) -> str:
    """Write the annotation instrument CSV. One row per student turn in the
    validation dialogues. Returns the path written.
    """
    rows = []
    for did in validation_ids:
        row = df.loc[did]
        profile = str(row["student_profile"]).strip()
        described = str(row["teacher_described_confusion"]).strip()
        problem = str(row["question"]).strip()
        for entry in row["dialogue"]:
            t = entry.get("turn")
            if t is None:
                continue
            rows.append({
                "dialogue_id": did,
                "turn": f"turn {t}",
                "misconception_general": profile,
                "misconception_specific": described,
                "problem": problem,
                "dialogue_history": _history_up_to(row["dialogue"], t),
                "student_turn_text": (entry.get("student") or "").strip(),
                "label": "",          # annotator fills: present/absent/not_evidenced
                "note": "",            # optional annotator note
            })
    out = pd.DataFrame(rows)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(path, index=False)
    return path


def load_validation_labels(path: str) -> Dict[Tuple[int, str], str]:
    """Read filled-in labels back. Only rows with a valid label are returned.
    Raises if any non-empty label is outside the allowed set (a typo guard).
    """
    df = pd.read_csv(path)
    out = {}
    bad = []
    for _, r in df.iterrows():
        lab = str(r.get("label", "")).strip().lower()
        if lab == "" or lab == "nan":
            continue
        if lab not in VALID_LABELS:
            bad.append((r["dialogue_id"], r["turn"], lab))
            continue
        out[(int(r["dialogue_id"]), str(r["turn"]))] = lab
    if bad:
        raise ValueError(f"{len(bad)} rows have invalid labels, e.g. {bad[:3]}. "
                         f"Allowed: {sorted(VALID_LABELS)}")
    return out
