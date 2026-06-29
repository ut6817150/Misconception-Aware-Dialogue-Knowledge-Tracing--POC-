"""
myext/agreement.py

Agreement between a prompt's extracted labels and the human (author) labels on
the frozen validation set. This is the SELECTION criterion for choosing a
prompt, complementing the endpoint screen.

Computed at both granularities:
  - trinary: present / absent / not_evidenced as labelled.
  - binary:  present / absent, with not_evidenced folded into absent
             (matching the binary scheme in the report).

Reports raw agreement and Cohen's kappa (chance-corrected). With a single
human annotator this is model-vs-author agreement, not inter-annotator
reliability; it still validly ranks prompts, but it is labelled honestly as
agreement with author labels.

Only turns the human has actually labelled are scored, so the comparison works
on a partially-labelled validation set and grows as labelling proceeds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np


def _to_binary(label: str) -> str:
    return "present" if label == "present" else "absent"


def cohen_kappa(a: List[str], b: List[str]) -> float:
    """Cohen's kappa between two label sequences over the same items."""
    cats = sorted(set(a) | set(b))
    idx = {c: i for i, c in enumerate(cats)}
    n = len(a)
    if n == 0:
        return float("nan")
    k = len(cats)
    conf = np.zeros((k, k))
    for x, y in zip(a, b):
        conf[idx[x], idx[y]] += 1
    po = np.trace(conf) / n
    row = conf.sum(axis=1) / n
    col = conf.sum(axis=0) / n
    pe = float(np.sum(row * col))
    if pe == 1.0:
        return float("nan")
    return (po - pe) / (1 - pe)


@dataclass
class AgreementResult:
    n_turns: int
    raw_trinary: float
    kappa_trinary: float
    raw_binary: float
    kappa_binary: float

    def summary(self) -> str:
        return (f"n={self.n_turns}  "
                f"trinary raw={self.raw_trinary:.3f} kappa={self.kappa_trinary:.3f}  "
                f"binary raw={self.raw_binary:.3f} kappa={self.kappa_binary:.3f}")


def align_labels(
    extracted: Dict[int, dict],
    human: Dict[Tuple[int, str], str],
) -> Tuple[List[str], List[str]]:
    """Pair up model and human labels over the turns the human has labelled.

    extracted: {dialogue_id: {turn_key: {label, reason}}}
    human:     {(dialogue_id, turn_key): label}
    Returns (model_labels, human_labels) over the shared, human-labelled turns.
    """
    model_seq, human_seq = [], []
    for (did, turn_key), hlabel in human.items():
        labels = extracted.get(did)
        if not labels or "_error" in labels:
            continue
        entry = labels.get(turn_key)
        if not isinstance(entry, dict):
            continue
        model_seq.append(entry["label"])
        human_seq.append(str(hlabel).strip().lower())
    return model_seq, human_seq


def agreement(extracted: Dict[int, dict],
              human: Dict[Tuple[int, str], str]) -> AgreementResult:
    """Compute raw agreement and kappa at trinary and binary granularity."""
    m, h = align_labels(extracted, human)
    n = len(m)
    if n == 0:
        return AgreementResult(0, float("nan"), float("nan"),
                               float("nan"), float("nan"))
    raw_tri = float(np.mean([x == y for x, y in zip(m, h)]))
    kap_tri = cohen_kappa(m, h)
    mb = [_to_binary(x) for x in m]
    hb = [_to_binary(x) for x in h]
    raw_bin = float(np.mean([x == y for x, y in zip(mb, hb)]))
    kap_bin = cohen_kappa(mb, hb)
    return AgreementResult(n, raw_tri, kap_tri, raw_bin, kap_bin)
