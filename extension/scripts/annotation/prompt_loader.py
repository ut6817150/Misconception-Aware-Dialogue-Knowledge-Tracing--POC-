"""Prompt discovery and assembly.

Prompt templates are markdown files in ``extension/artifacts/annotation_prompts``;
the filename stem is the prompt's name. Templates contain a
``{CODEBOOK_FULL_Vn}`` placeholder, filled from the matching
``codebook_full_vn.md`` file in ``extension/artifacts/codebooks``. Keeping
prompts as files means new variants are added by dropping a file in the folder,
and the extraction cache keys results by prompt name so variants never collide.

The assembled system prompt is cached against a fingerprint of the template
and codebook files (path, mtime, size), so editing either file mid-session
takes effect on the next call without a kernel restart. Every dialogue sees
the complete selected codebook; no dialogue-specific redaction is applied.

All paths are relative to the repository root (the notebooks chdir there).
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

PROMPTS_DIR = Path("extension/artifacts/annotation_prompts")
CODEBOOK_DIR = Path("extension/artifacts/codebooks")

PLACEHOLDER_RE = re.compile(r"\{CODEBOOK_FULL_V(\d+)\}")


def list_prompts(prompts_dir: Path = PROMPTS_DIR) -> List[str]:
    """Names (stems) of all prompt templates in the folder."""
    return sorted(p.stem for p in Path(prompts_dir).glob("P*.md"))


def _template_path(name: str, prompts_dir: Path) -> Path:
    path = Path(prompts_dir) / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"No prompt named {name!r} in {prompts_dir}")
    return path


def _codebook_paths(template_text: str) -> List[Tuple[str, Path]]:
    """(placeholder, codebook path) pairs for every placeholder in a template,
    any version number; missing files raise with the expected path named."""
    pairs: List[Tuple[str, Path]] = []
    for m in PLACEHOLDER_RE.finditer(template_text):
        path = CODEBOOK_DIR / f"codebook_full_v{m.group(1)}.md"
        if not path.exists():
            raise FileNotFoundError(
                f"Placeholder {m.group(0)} expects {path}, which does not exist"
            )
        pairs.append((m.group(0), path))
    return pairs


def _check_resolved(text: str, source: Path) -> None:
    unresolved = re.findall(r"\{CODEBOOK_[A-Z0-9_]+\}", text)
    if unresolved:
        raise ValueError(
            f"Unresolved codebook placeholder(s) in {source}: {unresolved}"
        )


def load_prompt(name: str, prompts_dir: Path = PROMPTS_DIR) -> str:
    """Load one template by stem and fill its codebook placeholders."""
    path = _template_path(name, prompts_dir)
    text = path.read_text()
    for placeholder, codebook in _codebook_paths(text):
        text = text.replace(placeholder, codebook.read_text())
    _check_resolved(text, path)
    return text


def load_all_prompts(prompts_dir: Path = PROMPTS_DIR) -> Dict[str, str]:
    return {n: load_prompt(n, prompts_dir) for n in list_prompts(prompts_dir)}


def _fingerprint(prompt_name: str, prompts_dir: Path) -> Tuple:
    """Hashable snapshot of the template and its codebook files. A change to
    any file's mtime or size changes the fingerprint and busts the cache."""
    template = _template_path(prompt_name, prompts_dir)
    stats = [(str(template), template.stat().st_mtime_ns, template.stat().st_size)]
    for _, codebook in _codebook_paths(template.read_text()):
        st = codebook.stat()
        stats.append((str(codebook), st.st_mtime_ns, st.st_size))
    return tuple(stats)


@lru_cache(maxsize=None)
def _system_cached(prompt_name: str, fingerprint: Tuple,
                   prompts_dir_str: str) -> str:
    """Assemble the complete system prompt.

    ``fingerprint`` is unused in the body and exists solely to key cache
    entries to the current template and codebook file state.
    """
    return load_prompt(prompt_name, Path(prompts_dir_str))


def system_for(prompt_name: str, dialogue_id: int | None = None,
               prompts_dir: Path = PROMPTS_DIR) -> str:
    """Return the complete selected system prompt for every dialogue.

    ``dialogue_id`` remains accepted for compatibility with existing callers
    but deliberately does not alter the prompt. Files are re-read whenever
    the template or codebook changes on disk.
    """
    return _system_cached(
        prompt_name, _fingerprint(prompt_name, Path(prompts_dir)),
        str(prompts_dir),
    )


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
    """Assemble the full message list for one annotation call."""
    return [
        {"role": "system", "content": system_for(prompt_name, dialogue_id)},
        {"role": "user", "content": user_msg(dialogue_id, conversation, units)},
    ]
