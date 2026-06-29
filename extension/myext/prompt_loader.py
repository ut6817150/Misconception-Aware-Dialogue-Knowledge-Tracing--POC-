"""
myext/prompt_loader.py

Discovers and loads prompt templates from myext/prompts/. Each prompt is a
plain-text file with a .txt extension; the filename (without extension) is the
prompt's name. A template uses Python str.format placeholders that the
extraction step fills per dialogue:

  {problem}            the math problem statement
  {profile}            the student profile (the family-level misconception)
  {described}          the teacher-described specific confusion
  {dialogue_block}     the formatted dialogue turns, student turns numbered

Keeping prompts as files (not Python strings) means new variants are added by
dropping a file in the folder, with no code change, and the cache keys results
by prompt name so variants never collide.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List


PROMPTS_DIR = Path(__file__).parent / "prompts"


def list_prompts(prompts_dir: Path = PROMPTS_DIR) -> List[str]:
    """Names (without extension) of all .txt prompt files in the folder."""
    prompts_dir = Path(prompts_dir)
    return sorted(p.stem for p in prompts_dir.glob("*.txt"))


def load_prompt(name: str, prompts_dir: Path = PROMPTS_DIR) -> str:
    """Load a single prompt template by name."""
    path = Path(prompts_dir) / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"No prompt named {name!r} in {prompts_dir}")
    return path.read_text()


def load_all_prompts(prompts_dir: Path = PROMPTS_DIR) -> Dict[str, str]:
    """All prompt templates as {name: template}."""
    return {n: load_prompt(n, prompts_dir) for n in list_prompts(prompts_dir)}
