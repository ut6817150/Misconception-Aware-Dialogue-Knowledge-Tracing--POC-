"""Shared MathDial-to-misconception row formatting.

The formatter expands each dialogue into one synthetic ``solution`` row followed
by one row per tutor/student exchange. Development and validation data can keep
the solution KCs blank; full train/test exports can instead use the ordered
union of KCs annotated anywhere in the dialogue.
"""

from __future__ import annotations

import re
from ast import literal_eval
from pathlib import Path
from typing import Iterable, Literal, Sequence

import pandas as pd


FAMILY_ORDER = [
    "comprehension",
    "principles",
    "relevance",
    "wrong-operation",
    "steps",
    "problem-type",
]

MATHDIAL_FIELDS = [
    "qid",
    "scenario",
    "question",
    "ground_truth",
    "student_incorrect_solution",
    "student_profile",
    "teacher_described_confusion",
    "self-correctness",
    "self-typical-confusion",
    "self-typical-interactions",
]

LEAD_COLUMNS = [
    "dialogue_id",
    "turn",
    "student_profile",
    "teacher_described_confusion",
    "question",
    "student_incorrect_solution",
    "dialogue_history",
    "student_turn_text",
    "correct",
    "kcs",
]

TAIL_COLUMNS = [
    "qid",
    "scenario",
    "ground_truth",
    "self-correctness",
    "self-typical-confusion",
    "self-typical-interactions",
    "conversation",
    "family",
]

UNIT_COLUMNS = LEAD_COLUMNS + TAIL_COLUMNS

GOLD_COLUMNS = [
    "comprehension",
    "relevance",
    "principles",
    "wrong_operation",
    "steps",
]
SOURCE_COLUMNS = [f"{column}_src" for column in GOLD_COLUMNS]
ANNOTATION_COLUMNS = GOLD_COLUMNS + SOURCE_COLUMNS + ["dialogue_threads", "note"]
VALIDATION_COLUMNS = UNIT_COLUMNS + ANNOTATION_COLUMNS

SolutionKCs = Literal["blank", "dialogue_union"]


def family_of(profile: object) -> str:
    """Map a native MathDial student profile to its misconception family."""
    text = str(profile).lower()
    if "what the problem is asking" in text:
        return "comprehension"
    if "underlying ideas" in text or "principles" in text:
        return "principles"
    if "relevant" in text and "irrelevant" in text:
        return "relevance"
    if "correct order" in text or "correct operation" in text:
        return "wrong-operation"
    if "steps or procedures" in text:
        return "steps"
    if "problem type" in text:
        return "problem-type"
    return "other"


def _parse_literal(value: object, expected_type: type) -> object:
    if isinstance(value, expected_type):
        return value
    try:
        parsed = literal_eval(str(value))
    except (SyntaxError, ValueError):
        return expected_type()
    return parsed if isinstance(parsed, expected_type) else expected_type()


def load_mathdial(path: str | Path) -> pd.DataFrame:
    """Load an annotated MathDial CSV with dialogue and annotation parsed."""
    converters = {
        "dialogue": lambda value: _parse_literal(value, list),
        "annotation": lambda value: _parse_literal(value, dict),
    }
    return pd.read_csv(path, converters=converters)


def annotations_by_turn(annotation: object) -> dict[int, tuple[object, object]]:
    """Return ``{turn_number: (correct, kcs)}`` from an ATC annotation."""
    annotation = _parse_literal(annotation, dict)
    if "error" in annotation:
        return {}

    result = {}
    for label, values in annotation.items():
        match = re.search(r"\d+", str(label))
        if match and isinstance(values, dict):
            result[int(match.group())] = (
                values.get("correct", ""),
                values.get("kcs", ""),
            )
    return result


def ordered_kc_union(
    dialogue: Sequence[dict],
    annotations: dict[int, tuple[object, object]],
) -> list:
    """Collect unique KCs in dialogue order and first-appearance order."""
    union = []
    seen = set()
    for exchange in dialogue:
        turn = exchange.get("turn")
        if turn is None:
            continue
        _, kcs = annotations.get(int(turn), ("", []))
        if not isinstance(kcs, (list, tuple)):
            continue
        for kc in kcs:
            if kc not in seen:
                seen.add(kc)
                union.append(kc)
    return union


def conversation_prefix(
    question: object,
    solution: object,
    dialogue: Sequence[dict],
    through_turn: int | None = None,
) -> str:
    """Render the problem, turn 0, and optionally dialogue through one turn."""
    lines = [
        f"Tutor: {str(question).strip()}",
        f"Student (turn 0): {str(solution).strip()}",
    ]
    if through_turn is None:
        return "\n".join(lines)

    for exchange in dialogue:
        turn = exchange.get("turn")
        teacher = (exchange.get("teacher") or "").strip()
        student = (exchange.get("student") or "").strip()
        if teacher:
            lines.append(f"Tutor: {teacher}")
        if student:
            label = f"Student (turn {turn})" if turn is not None else "Student"
            lines.append(f"{label}: {student}")
        if turn == through_turn:
            break
    return "\n".join(lines)


def dialogue_history(dialogue: Sequence[dict], through_turn: int) -> str:
    """Render actual dialogue before the current student response."""
    lines = []
    for exchange in dialogue:
        turn = exchange.get("turn")
        teacher = (exchange.get("teacher") or "").strip()
        student = (exchange.get("student") or "").strip()
        if teacher:
            lines.append(f"Tutor: {teacher}")
        if turn == through_turn:
            break
        if student:
            lines.append(f"Student (turn {turn}): {student}")
    return "\n".join(lines)


def build_units(
    source: pd.DataFrame,
    dialogue_ids: Iterable[int] | None = None,
    *,
    solution_kcs: SolutionKCs = "blank",
) -> pd.DataFrame:
    """Expand MathDial dialogues into solution and student-turn unit rows."""
    if solution_kcs not in ("blank", "dialogue_union"):
        raise ValueError("solution_kcs must be 'blank' or 'dialogue_union'")

    id_column = "index" if "index" in source.columns else source.columns[0]
    missing = [column for column in MATHDIAL_FIELDS + ["dialogue", "annotation"]
               if column not in source.columns]
    if missing:
        raise KeyError(f"MathDial source is missing required columns: {missing}")
    if source[id_column].duplicated().any():
        raise ValueError(f"{id_column} must uniquely identify dialogues")

    by_id = source.set_index(id_column)
    ids = source[id_column].tolist() if dialogue_ids is None else list(dialogue_ids)
    absent = sorted(set(ids) - set(by_id.index))
    if absent:
        raise KeyError(f"dialogue ids not found in source: {absent[:10]}")

    rows = []
    for dialogue_id in ids:
        record = by_id.loc[dialogue_id]
        dialogue = _parse_literal(record["dialogue"], list)
        annotations = annotations_by_turn(record["annotation"])
        solution_row_kcs = (
            ordered_kc_union(dialogue, annotations)
            if solution_kcs == "dialogue_union"
            else ""
        )

        base = {field: record[field] for field in MATHDIAL_FIELDS}
        base.update(
            dialogue_id=int(dialogue_id),
            family=family_of(record["student_profile"]),
        )
        rows.append({
            **base,
            "turn": "solution",
            "student_turn_text": str(base["student_incorrect_solution"]).strip(),
            "dialogue_history": "",
            "correct": False,
            "kcs": solution_row_kcs,
            "conversation": conversation_prefix(
                base["question"], base["student_incorrect_solution"], dialogue
            ),
        })

        for exchange in dialogue:
            turn = exchange.get("turn")
            if turn is None:
                continue
            correct, kcs = annotations.get(int(turn), ("", ""))
            rows.append({
                **base,
                "turn": f"turn {turn}",
                "student_turn_text": (exchange.get("student") or "").strip(),
                "dialogue_history": dialogue_history(dialogue, turn),
                "correct": correct,
                "kcs": kcs,
                "conversation": conversation_prefix(
                    base["question"],
                    base["student_incorrect_solution"],
                    dialogue,
                    turn,
                ),
            })

    return pd.DataFrame(rows, columns=UNIT_COLUMNS)


def add_annotation_columns(units: pd.DataFrame) -> pd.DataFrame:
    """Return the unit table with the empty validation annotation surface."""
    result = units.copy()
    for column in ANNOTATION_COLUMNS:
        result[column] = ""
    return result[VALIDATION_COLUMNS]


def has_annotations(path: str | Path) -> bool:
    """Whether a saved annotation table contains any nonblank annotation cell."""
    path = Path(path)
    if not path.exists():
        return False
    existing = pd.read_csv(path, keep_default_na=False)
    columns = [column for column in ANNOTATION_COLUMNS
               if column in existing.columns]
    return bool(columns) and bool(
        (existing[columns].astype(str).apply(lambda values: values.str.strip()) != "")
        .any()
        .any()
    )


def validate_units(
    units: pd.DataFrame,
    *,
    solution_kcs: SolutionKCs,
    expected_dialogues: int | None = None,
) -> dict[str, int]:
    """Assert structural invariants and return a compact audit summary."""
    required = VALIDATION_COLUMNS if set(ANNOTATION_COLUMNS) <= set(units.columns) else UNIT_COLUMNS
    if units.columns.tolist() != required:
        raise AssertionError("unexpected unit-table columns or column order")

    solutions = units[units["turn"].eq("solution")]
    dialogue_count = units["dialogue_id"].nunique()
    if len(solutions) != dialogue_count:
        raise AssertionError("every dialogue must have exactly one solution row")
    if expected_dialogues is not None and dialogue_count != expected_dialogues:
        raise AssertionError(
            f"expected {expected_dialogues} dialogues, found {dialogue_count}"
        )
    if not solutions["correct"].eq(False).all():
        raise AssertionError("every solution row must have correct=False")

    first_turns = units.groupby("dialogue_id", sort=False)["turn"].first()
    if not first_turns.eq("solution").all():
        raise AssertionError("the solution row must be first in every dialogue")

    nonempty_solution_kcs = 0
    if solution_kcs == "blank":
        if not solutions["kcs"].eq("").all():
            raise AssertionError("solution KCs must be blank")
    else:
        for _, group in units.groupby("dialogue_id", sort=False):
            solution = group.iloc[0]["kcs"]
            expected = []
            seen = set()
            for kcs in group.iloc[1:]["kcs"]:
                if not isinstance(kcs, (list, tuple)):
                    continue
                for kc in kcs:
                    if kc not in seen:
                        seen.add(kc)
                        expected.append(kc)
            if solution != expected:
                raise AssertionError(
                    f"solution KC union mismatch for dialogue {group.iloc[0]['dialogue_id']}"
                )
            nonempty_solution_kcs += bool(solution)

    return {
        "dialogues": dialogue_count,
        "rows": len(units),
        "solution_rows": len(solutions),
        "solutions_with_kcs": nonempty_solution_kcs,
    }

