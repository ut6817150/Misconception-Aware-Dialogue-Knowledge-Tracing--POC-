"""Prompt discovery, assembly, and leave-one-out redaction.

Prompt templates are markdown files in ``extension/artifacts/annotation_prompts``;
the filename stem is the prompt's name. Templates contain a
``{CODEBOOK_FULL_Vn}`` placeholder, filled from the matching
``codebook_full_vn.md`` file in ``extension/artifacts/codebooks``. Keeping
prompts as files means new variants are added by dropping a file in the folder,
and the extraction cache keys results by prompt name so variants never collide.

The full codebook cites validation dialogues as worked examples, sometimes
stating their gold reading. ``system_for`` therefore applies block-aware
leave-one-out redaction: when annotating dialogue D, the block citing D keeps
its rule sentences and drops everything from the citation onward.

All paths are relative to the repository root (the notebooks chdir there).
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

PROMPTS_DIR = Path("extension/artifacts/annotation_prompts")
CODEBOOK_DIR = Path("extension/artifacts/codebooks")


def list_prompts(prompts_dir: Path = PROMPTS_DIR) -> List[str]:
    """Names (stems) of all prompt templates in the folder."""
    return sorted(p.stem for p in Path(prompts_dir).glob("P*.md"))


def load_prompt(name: str, prompts_dir: Path = PROMPTS_DIR) -> str:
    """Load one template by stem and fill its codebook placeholders."""
    path = Path(prompts_dir) / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"No prompt named {name!r} in {prompts_dir}")
    text = path.read_text()
    for version in range(7):
        placeholder = f"{{CODEBOOK_FULL_V{version}}}"
        if placeholder in text:
            codebook = CODEBOOK_DIR / f"codebook_full_v{version}.md"
            text = text.replace(placeholder, codebook.read_text())
    unresolved = re.findall(r"\{CODEBOOK_[A-Z0-9_]+\}", text)
    if unresolved:
        raise ValueError(
            f"Unresolved codebook placeholder(s) in {path}: {unresolved}"
        )
    return text


def load_all_prompts(prompts_dir: Path = PROMPTS_DIR) -> Dict[str, str]:
    return {n: load_prompt(n, prompts_dir) for n in list_prompts(prompts_dir)}


# ---------------------------------------------------------------------------
# Leave-one-out redaction
# ---------------------------------------------------------------------------

def cited_ids(system_text: str, dialogue_ids) -> List[int]:
    """Dialogue ids from ``dialogue_ids`` cited anywhere in the instrument."""
    found = {int(m) for m in re.findall(r"\b(\d{3,4})\b", system_text)}
    return sorted(found & {int(d) for d in dialogue_ids})


def redact(text: str, dialogue_id: int) -> str:
    """Block-aware leave-one-out redaction for one target dialogue.

    Within a block citing the id, sentences before the first citing sentence
    (the general rule) survive; the citing sentence and everything after it in
    the block (the worked example) are dropped.
    """
    pat = re.compile(rf"\b{dialogue_id}\b")
    if not pat.search(text):
        return text
    blocks = re.split(r"(\n\n+|\n(?=\s*- ))", text)  # keep separators
    out = []
    for block in blocks:
        if not pat.search(block):
            out.append(block)
            continue
        sentences = re.split(r"(?<=[.!?])\s+", block)
        keep = []
        for sentence in sentences:
            if pat.search(sentence):
                break
            keep.append(sentence)
        out.append(" ".join(keep))
    return "".join(out)


@lru_cache(maxsize=None)
def _system_cached(prompt_name: str, dialogue_id: int) -> str:
    return redact(load_prompt(prompt_name), dialogue_id)


def system_for(prompt_name: str, dialogue_id: int) -> str:
    """The per-dialogue system message: the template with leave-one-out
    redaction applied where the instrument cites this dialogue."""
    return _system_cached(prompt_name, int(dialogue_id))


# ---------------------------------------------------------------------------
# User message
# ---------------------------------------------------------------------------

def user_msg(dialogue_id: int, conversation: str, units: List[str]) -> str:
    """The user message: id, the dialogue verbatim, and the enumerated unit
    list that pins grid alignment. Nothing label-adjacent ever enters here."""
    return (
        f"dialogue_id: {dialogue_id}\n\n"
        f"=== DIALOGUE (problem, incorrect solution as turn 0, then turns) ===\n"
        f"{conversation}\n\n"
        f"Annotate exactly these units, in this order: {units}\n"
        f"('solution' is the student's initial incorrect solution, turn 0 above.)\n"
        f"Return only the JSON object."
    )


def prompt_constructor(prompt_name: str, dialogue_id: int, conversation: str,
                       units: List[str]) -> List[dict]:
    """Assemble the full message list for one annotation call: the per-dialogue
    system message (instrument, redaction applied if it cites this dialogue)
    and the user message (dialogue verbatim plus the enumerated unit list)."""
    return [
        {"role": "system", "content": system_for(prompt_name, dialogue_id)},
        {"role": "user", "content": user_msg(dialogue_id, conversation, units)},
    ]
