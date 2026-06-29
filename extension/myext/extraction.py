"""
myext/extraction.py

Per-dialogue misconception extraction via the OpenRouter API.

For each dialogue, the whole dialogue is sent in one call and the model labels
every student turn at the three-value granularity (present / absent /
not_evidenced). Results are cached to disk keyed by (dialogue_id, prompt_name,
model), so re-running, comparing prompts, and resuming after interruption never
re-call the API for combinations already done.

The API key is read from the environment variable OPENROUTER_API_KEY and is
never hard-coded. Export it in the same terminal that launches Jupyter.

Usage (from a notebook):
    from myext import extraction, prompt_loader
    tmpl = prompt_loader.load_prompt("codebook_concise")
    labels = extraction.extract_dialogue(row, tmpl, "codebook_concise")
    # or over many dialogues with caching and a progress bar:
    results = extraction.extract_many(df, ids, tmpl, "codebook_concise")
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "anthropic/claude-opus-4.8"
CACHE_DIR = Path("extension/artifacts/extraction_cache")

VALID_LABELS = {"present", "absent", "not_evidenced"}


# ---------------------------------------------------------------------------
# Formatting a dialogue into the prompt
# ---------------------------------------------------------------------------

def format_dialogue_block(dialogue: List[dict]) -> str:
    """Render the dialogue turns as text, numbering the student turns so the
    model can key its JSON by turn number. Each entry is
    {turn, teacher, student}; the turn integer is used as the key.
    """
    lines = []
    for entry in dialogue:
        t = entry.get("turn")
        teacher = (entry.get("teacher") or "").strip()
        student = (entry.get("student") or "").strip()
        if teacher:
            lines.append(f"Tutor: {teacher}")
        lines.append(f"Student (turn {t}): {student}")
    return "\n".join(lines)


def build_prompt(template: str, row) -> str:
    """Fill a prompt template with one dialogue's fields."""
    return template.format(
        problem=str(row["question"]).strip(),
        profile=str(row["student_profile"]).strip(),
        described=str(row["teacher_described_confusion"]).strip(),
        dialogue_block=format_dialogue_block(row["dialogue"]),
    )


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------

def _cache_path(dialogue_id: int, prompt_name: str, model: str) -> Path:
    safe_model = model.replace("/", "_").replace(".", "-")
    return CACHE_DIR / safe_model / prompt_name / f"dialogue_{dialogue_id}.json"


def _load_cached(dialogue_id: int, prompt_name: str, model: str) -> Optional[dict]:
    p = _cache_path(dialogue_id, prompt_name, model)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return None
    return None


def _save_cached(dialogue_id: int, prompt_name: str, model: str, payload: dict) -> None:
    p = _cache_path(dialogue_id, prompt_name, model)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2))


# ---------------------------------------------------------------------------
# The API call
# ---------------------------------------------------------------------------

def _api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Export it in the terminal that "
            "launched Jupyter, e.g. `export OPENROUTER_API_KEY=sk-or-...`, then "
            "restart the kernel."
        )
    return key


def _call_openrouter(prompt: str, model: str, max_tokens: int = 4000,
                     timeout: int = 120) -> str:
    """Single chat completion call. Returns the raw text content."""
    headers = {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0,
    }
    resp = requests.post(OPENROUTER_URL, headers=headers, json=body, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Parsing and validating the model's JSON
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> dict:
    """Pull the JSON object out of the model's response, tolerating stray text
    or markdown fences around it. Raises ValueError if no parseable object.
    """
    t = text.strip()
    # strip ```json ... ``` fences if present
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.startswith("json"):
            t = t[4:]
        t = t.strip()
    # find the outermost braces
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found in response")
    return json.loads(t[start:end + 1])


def _normalise_labels(parsed: dict) -> Dict[str, dict]:
    """Coerce keys to 'turn N' form and validate labels. Returns
    {turn_key: {label, reason}}. Invalid labels raise ValueError so the retry
    logic can trigger.
    """
    out = {}
    for k, v in parsed.items():
        # key may be "1", "turn 1", 1, etc -> canonical "turn N"
        digits = "".join(ch for ch in str(k) if ch.isdigit())
        if not digits:
            continue
        turn_key = f"turn {int(digits)}"
        if isinstance(v, dict):
            label = str(v.get("label", "")).strip().lower()
            reason = str(v.get("reason", "")).strip()
        else:
            label = str(v).strip().lower()
            reason = ""
        if label not in VALID_LABELS:
            raise ValueError(f"invalid label {label!r} for {turn_key}")
        out[turn_key] = {"label": label, "reason": reason}
    if not out:
        raise ValueError("no valid turn labels parsed")
    return out


# ---------------------------------------------------------------------------
# Public extraction entry points
# ---------------------------------------------------------------------------

def extract_dialogue(row, template: str, prompt_name: str,
                     model: str = DEFAULT_MODEL, max_retries: int = 2,
                     use_cache: bool = True) -> dict:
    """Extract per-turn labels for one dialogue, with caching and retry.

    Returns a dict {turn_key: {label, reason}}. On repeated failure, returns
    {"_error": "..."} so a batch run can continue and the failures be counted.
    """
    dialogue_id = int(row.name)
    if use_cache:
        cached = _load_cached(dialogue_id, prompt_name, model)
        if cached is not None:
            return cached

    prompt = build_prompt(template, row)
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            raw = _call_openrouter(prompt, model)
            labels = _normalise_labels(_extract_json(raw))
            if use_cache:
                _save_cached(dialogue_id, prompt_name, model, labels)
            return labels
        except Exception as e:  # noqa: BLE001 - we want to retry on anything
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    result = {"_error": f"{type(last_err).__name__}: {last_err}"}
    if use_cache:
        _save_cached(dialogue_id, prompt_name, model, result)
    return result


def extract_many(df, dialogue_ids: List[int], template: str, prompt_name: str,
                 model: str = DEFAULT_MODEL, use_cache: bool = True,
                 verbose: bool = True) -> Dict[int, dict]:
    """Extract labels for many dialogues. Returns {dialogue_id: labels}.

    Cached dialogues are free; only uncached ones hit the API, so re-running is
    cheap and interruptions resume. Failures are kept (as {"_error": ...}) and
    counted rather than aborting the batch.
    """
    results = {}
    n_err = 0
    for i, did in enumerate(dialogue_ids, 1):
        row = df.loc[did]
        labels = extract_dialogue(row, template, prompt_name, model=model,
                                  use_cache=use_cache)
        results[did] = labels
        if "_error" in labels:
            n_err += 1
        if verbose and (i % 10 == 0 or i == len(dialogue_ids)):
            print(f"  [{prompt_name}] {i}/{len(dialogue_ids)} done "
                  f"({n_err} errors)")
    if verbose and n_err:
        print(f"  [{prompt_name}] {n_err} dialogues failed extraction.")
    return results
