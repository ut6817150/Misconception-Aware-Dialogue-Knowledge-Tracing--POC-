"""
myext/splits.py

Frozen, reproducible split of the training dialogues into three disjoint sets:

  - dev:        a small set for prompt development (label freely, iterate).
  - validation: the held-out set for human labelling and prompt selection;
                fixed before labelling so the human-agreement numbers are not
                contaminated by selection.
  - pool:       the remainder, used for the eventual full production run.

The split is seeded and written to disk as id lists, so it never silently
changes between runs. Selection of the prompt is done on validation; prompts
are developed on dev; the two are disjoint.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np


SPLIT_FILE = Path("extension/artifacts/prompt_splits.json")


@dataclass
class PromptSplits:
    dev: List[int]
    validation: List[int]
    pool: List[int]

    def summary(self) -> str:
        return (f"dev={len(self.dev)}  validation={len(self.validation)}  "
                f"pool={len(self.pool)}  total={len(self.dev)+len(self.validation)+len(self.pool)}")


def make_or_load_splits(
    all_dialogue_ids: List[int],
    n_dev: int = 8,
    n_validation: int = 55,
    seed: int = 7,
    path: Path = SPLIT_FILE,
) -> PromptSplits:
    """Create the frozen split if it does not exist, else load it from disk.

    n_validation defaults to about 55 dialogues, which at a median of five
    student turns lands in the 250 to 300 turn range where Krippendorff's
    alpha is stable. n_dev is a small handful for prompt iteration.
    """
    path = Path(path)
    if path.exists():
        with open(path) as f:
            d = json.load(f)
        return PromptSplits(dev=d["dev"], validation=d["validation"], pool=d["pool"])

    rng = np.random.default_rng(seed)
    ids = list(all_dialogue_ids)
    rng.shuffle(ids)
    dev = sorted(ids[:n_dev])
    validation = sorted(ids[n_dev:n_dev + n_validation])
    pool = sorted(ids[n_dev + n_validation:])

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump({"seed": seed, "dev": dev, "validation": validation, "pool": pool}, f, indent=2)
    return PromptSplits(dev=dev, validation=validation, pool=pool)
