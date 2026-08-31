"""Apply available misconception-annotation cache records to a dataset.

This module bridges the per-dialogue JSON extraction cache and the row-level
MathDial CSVs. It deliberately supports incremental updates: missing, invalid,
unreadable, or structurally mismatched cache records are reported and skipped,
while every usable record is applied to a copy of the supplied dataframe.

The five family cells receive their P/A/N labels. Their corresponding
``*_src`` cells contain thread identifiers only (``S1`` or ``S1|S2``), and the
complete compact threads JSON is stored once, on the dialogue's ``solution``
row. Saving is atomic: a temporary CSV is reloaded and reconciled before it
replaces the requested path.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Mapping

import pandas as pd

from ..annotation.schema import FAMILIES
from .load_annotation_data import load_dataset


LABELS = {"P", "A", "N"}
SOURCE_COLUMNS = [f"{family}_src" for family in FAMILIES]


def load_available_cache(
    cache_dir: str | Path,
    *,
    split: str,
    model_slug: str,
    prompt: str,
) -> tuple[dict[int, dict], pd.DataFrame, list[str]]:
    """Load all unsuffixed production JSON records from one cache directory.

    Records with unreadable JSON, inconsistent identity/configuration,
    ``valid != True``, or no annotation object are retained in the audit but
    excluded from the returned usable-record dictionary. Files whose stem is
    not an integer (for example ``323_1.json``) are ignored and returned
    separately so experimental retries cannot silently enter a production
    dataset.
    """
    cache_dir = Path(cache_dir)
    usable: dict[int, dict] = {}
    audit_rows: list[dict] = []
    numeric_paths = sorted(
        (path for path in cache_dir.glob("*.json") if path.stem.isdigit()),
        key=lambda path: int(path.stem),
    )
    suffixed_files = sorted(
        path.name
        for path in cache_dir.glob("*.json")
        if not path.stem.isdigit()
    )

    for path in numeric_paths:
        filename_id = int(path.stem)
        try:
            record = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            audit_rows.append(
                {
                    "dialogue_id": filename_id,
                    "status": "unreadable",
                    "detail": str(exc),
                }
            )
            continue

        errors = []
        if record.get("dialogue_id") != filename_id:
            errors.append(
                f"record dialogue_id={record.get('dialogue_id')!r}"
            )
        if record.get("split") != split:
            errors.append(f"record split={record.get('split')!r}")
        if record.get("model") != model_slug:
            errors.append(f"record model={record.get('model')!r}")
        if record.get("prompt") != prompt:
            errors.append(f"record prompt={record.get('prompt')!r}")
        if not record.get("valid"):
            errors.append("record is not marked valid")
        if not isinstance(record.get("annotation"), dict):
            errors.append("annotation is absent or not an object")

        status = "invalid" if errors else "usable"
        audit_rows.append(
            {
                "dialogue_id": filename_id,
                "status": status,
                "detail": "; ".join(errors),
            }
        )
        if not errors:
            usable[filename_id] = record

    audit = pd.DataFrame(
        audit_rows, columns=["dialogue_id", "status", "detail"]
    )
    return usable, audit, suffixed_files


def source_ids(value: object) -> list[str]:
    """Normalize one cache ``srcs`` value to a validated list of IDs.

    The extraction schema uses a string for one source and a list for multiple
    sources. Empty values become an empty list. No quotations or other evidence
    text is accepted here; every value must have the form ``S<integer>``.
    """
    if value in (None, "", []):
        return []
    values = [value] if isinstance(value, str) else value
    if not isinstance(values, list) or not all(
        isinstance(item, str) for item in values
    ):
        raise ValueError(f"invalid source value {value!r}")
    if len(set(values)) != len(values):
        raise ValueError(f"duplicate source identifiers {values!r}")
    invalid = [item for item in values if not re.fullmatch(r"S\d+", item)]
    if invalid:
        raise ValueError(f"invalid source identifiers {invalid!r}")
    return values


def prepare_dialogue(
    record: Mapping,
    dialogue_id: int,
    expected_units: list[str],
) -> tuple[list[dict], str]:
    """Validate and normalize one usable record before dataframe mutation.

    This second validation layer protects the join rather than reassessing the
    annotation semantics. It requires exact ordered unit alignment, P/A/N
    labels, unique ``S#`` thread IDs, and source references that resolve to a
    thread defined by the same cache record.
    """
    annotation = record["annotation"]
    if annotation.get("dialogue_id") != dialogue_id:
        raise ValueError(
            f"annotation dialogue_id={annotation.get('dialogue_id')!r}"
        )

    grid = annotation.get("grid")
    if not isinstance(grid, list) or not all(
        isinstance(row, dict) for row in grid
    ):
        raise ValueError("annotation.grid must be a list of objects")
    grid_units = [row.get("unit") for row in grid]
    if grid_units != expected_units:
        raise ValueError(
            f"unit mismatch: expected {expected_units!r}, "
            f"received {grid_units!r}"
        )

    threads = annotation.get("threads")
    if not isinstance(threads, list) or not all(
        isinstance(thread, dict) for thread in threads
    ):
        raise ValueError("annotation.threads must be a list of objects")
    thread_ids = [thread.get("id") for thread in threads]
    if any(
        not isinstance(thread_id, str)
        or not re.fullmatch(r"S\d+", thread_id)
        for thread_id in thread_ids
    ):
        raise ValueError(f"invalid thread identifiers {thread_ids!r}")
    if len(set(thread_ids)) != len(thread_ids):
        raise ValueError(f"duplicate thread identifiers {thread_ids!r}")
    thread_id_set = set(thread_ids)

    prepared_rows = []
    for row in grid:
        srcs = row.get("srcs", {})
        if not isinstance(srcs, dict):
            raise ValueError(f"{row.get('unit')}: srcs is not an object")
        prepared = {"turn": row["unit"]}
        for family in FAMILIES:
            label = row.get(family)
            if label not in LABELS:
                raise ValueError(
                    f"{row['unit']}/{family}: invalid label {label!r}"
                )
            ids = source_ids(srcs.get(family))
            unknown = [
                source_id
                for source_id in ids
                if source_id not in thread_id_set
            ]
            if unknown:
                raise ValueError(
                    f"{row['unit']}/{family}: unknown thread IDs {unknown!r}"
                )
            prepared[family] = label
            prepared[f"{family}_src"] = "|".join(ids)
        prepared_rows.append(prepared)

    threads_json = json.dumps(
        threads, ensure_ascii=False, separators=(",", ":")
    )
    return prepared_rows, threads_json


def apply_available_cache(
    dataset: pd.DataFrame,
    records: Mapping[int, Mapping],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply all structurally usable records to a dataframe copy.

    Records absent from the dataset or failing :func:`prepare_dialogue` are
    reported as ``skipped`` and leave their rows unchanged. Other dialogues,
    including those with no cache file, retain exactly the values loaded from
    the input dataset. This makes repeated calls incremental and idempotent.
    """
    updated = dataset.copy()
    for column in [*SOURCE_COLUMNS, "dialogue_threads"]:
        if column not in updated.columns:
            updated[column] = ""

    expected_units = {
        int(dialogue_id): group["turn"].tolist()
        for dialogue_id, group in updated.groupby(
            "dialogue_id", sort=False
        )
    }
    keyed = updated.set_index(["dialogue_id", "turn"], drop=False)
    audit_rows = []

    for dialogue_id, record in records.items():
        if dialogue_id not in expected_units:
            audit_rows.append(
                {
                    "dialogue_id": dialogue_id,
                    "status": "skipped",
                    "detail": "dialogue ID is absent from the dataset",
                }
            )
            continue
        try:
            prepared_rows, threads_json = prepare_dialogue(
                record, dialogue_id, expected_units[dialogue_id]
            )
        except (KeyError, TypeError, ValueError) as exc:
            audit_rows.append(
                {
                    "dialogue_id": dialogue_id,
                    "status": "skipped",
                    "detail": str(exc),
                }
            )
            continue

        for row in prepared_rows:
            key = (dialogue_id, row["turn"])
            for family in FAMILIES:
                keyed.at[key, family] = row[family]
                keyed.at[key, f"{family}_src"] = row[f"{family}_src"]
            keyed.at[key, "dialogue_threads"] = ""
        keyed.at[(dialogue_id, "solution"), "dialogue_threads"] = (
            threads_json
        )
        audit_rows.append(
            {
                "dialogue_id": dialogue_id,
                "status": "applied",
                "detail": "",
            }
        )

    updated = keyed.reset_index(drop=True)
    tail = [*FAMILIES, *SOURCE_COLUMNS, "dialogue_threads", "note"]
    leading = [column for column in updated.columns if column not in tail]
    updated = updated[
        leading + [column for column in tail if column in updated.columns]
    ]

    untouched = [
        column
        for column in dataset.columns
        if column
        not in [*FAMILIES, *SOURCE_COLUMNS, "dialogue_threads"]
    ]
    pd.testing.assert_frame_equal(
        updated[untouched].reset_index(drop=True),
        dataset[untouched].reset_index(drop=True),
        check_dtype=True,
    )
    allowed_labels = updated[FAMILIES].isin(LABELS) | updated[
        FAMILIES
    ].eq("")
    if not allowed_labels.all().all():
        raise AssertionError(
            "Dataset contains a family value outside P/A/N/blank."
        )

    audit = pd.DataFrame(
        audit_rows, columns=["dialogue_id", "status", "detail"]
    )
    return updated, audit


def split_summary(
    original: pd.DataFrame,
    updated: pd.DataFrame,
    apply_audit: pd.DataFrame,
) -> pd.Series:
    """Return a compact incremental-update summary for notebook display."""
    applied = (
        int(apply_audit["status"].eq("applied").sum())
        if not apply_audit.empty
        else 0
    )
    skipped = len(apply_audit) - applied
    annotation_cells = int(
        updated[FAMILIES]
        .astype(str)
        .apply(lambda column: column.str.strip().ne(""))
        .sum()
        .sum()
    )
    return pd.Series(
        {
            "dataset dialogues": original["dialogue_id"].nunique(),
            "usable cache records considered": len(apply_audit),
            "cache records applied": applied,
            "structurally skipped records": skipped,
            "dataset dialogues not updated this run": (
                original["dialogue_id"].nunique() - applied
            ),
            "nonblank P/A/N cells after update": annotation_cells,
        }
    )


def save_in_place(dataframe: pd.DataFrame, path: str | Path) -> dict:
    """Atomically replace ``path`` after a CSV round-trip reconciliation.

    The caller owns the write-control decision. This function always writes
    when called, so notebooks should guard it with their explicit write flag.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(".tmp.csv")
    try:
        dataframe.to_csv(temporary_path, index=False)
        reloaded = load_dataset(temporary_path)
        if reloaded.columns.tolist() != dataframe.columns.tolist():
            raise AssertionError(
                "CSV columns changed during serialization."
            )
        if len(reloaded) != len(dataframe):
            raise AssertionError(
                "CSV row count changed during serialization."
            )
        expected_keys = (
            dataframe[["dialogue_id", "turn"]]
            .astype(str)
            .values.tolist()
        )
        actual_keys = (
            reloaded[["dialogue_id", "turn"]]
            .astype(str)
            .values.tolist()
        )
        if actual_keys != expected_keys:
            raise AssertionError(
                "CSV key order changed during serialization."
            )
        pd.testing.assert_frame_equal(
            reloaded.astype(str),
            dataframe.astype(str),
            check_dtype=True,
        )
        temporary_path.replace(path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    return {
        "path": path,
        "rows": len(reloaded),
        "dialogues": reloaded["dialogue_id"].nunique(),
        "size_mib": path.stat().st_size / 1024**2,
    }
