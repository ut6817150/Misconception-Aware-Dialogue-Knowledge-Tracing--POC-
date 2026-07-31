"""Load a formatted validation or misconception dataset.

The CSV exports use blank strings deliberately: for example, a blank
``correct`` value means that no correctness annotation is available. The
loader therefore disables pandas' default conversion of blanks to ``NaN``.

Examples
--------
>>> from extension.scripts.load_annotation_data import load_dataset
>>> validation = load_dataset(
...     "extension/artifacts/annotation_dev_and_val_sets/validation_set.csv"
... )
>>> train = load_dataset("data/misconception/mathdial_train.csv")
>>> test = load_dataset("data/misconception/mathdial_test.csv")
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "dialogue_id",
    "turn",
    "conversation",
    "student_turn_text",
    "correct",
    "kcs",
    "comprehension",
    "relevance",
    "principles",
    "wrong_operation",
    "steps",
}


def load_dataset(filepath: str | Path) -> pd.DataFrame:
    """Load and validate one formatted unit-level CSV as a DataFrame.

    Relative paths are interpreted from the process's current working
    directory. Blank CSV cells are preserved as empty strings.

    Parameters
    ----------
    filepath:
        Path to a formatted validation, misconception train, or misconception
        test CSV.
    """
    path = Path(filepath).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Dataset not found: {path}")

    dataframe = pd.read_csv(path, keep_default_na=False)

    missing = sorted(REQUIRED_COLUMNS - set(dataframe.columns))
    if missing:
        raise ValueError(f"{path.name} is missing required columns: {missing}")

    duplicate_rows = dataframe.duplicated(["dialogue_id", "turn"])
    if duplicate_rows.any():
        examples = dataframe.loc[
            duplicate_rows, ["dialogue_id", "turn"]
        ].head().to_dict("records")
        raise ValueError(
            f"{path.name} has duplicate dialogue/turn rows; examples: {examples}"
        )

    dialogues = set(dataframe["dialogue_id"])
    dialogues_with_solution = set(
        dataframe.loc[dataframe["turn"].eq("solution"), "dialogue_id"]
    )
    missing_solutions = sorted(dialogues - dialogues_with_solution)
    if missing_solutions:
        raise ValueError(
            f"{path.name} has dialogues without a solution row: "
            f"{missing_solutions[:10]}"
        )

    return dataframe
