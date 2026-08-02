"""Per-dialogue misconception annotation via the OpenRouter API.

The public entry point is ``generate_annotation(prompt_name, model_name,
dialogue)``: it takes a self-contained dialogue record produced by
``dialogues_from`` (dataframe in, list of dialogues out), builds the messages
through ``prompt_loader.prompt_constructor``, sends them with ``llm_call``,
validates the returned JSON, and saves the full record (raw output, reasoning
trace, errors, usage, cost) to
``extension/artifacts/extraction_cache/{split}/{model}/{prompt}/{id}.json``.
Re-runs skip cells already cached as valid. Scoring reads only the cache.

The API key is read from the environment variable OPENROUTER_API_KEY and is
never written to disk. No output-token cap is sent; models run their
provider defaults, and cost comes from OpenRouter usage accounting per call.
"""

from __future__ import annotations

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

from . import prompt_loader

BASE_URL = "https://openrouter.ai/api/v1"
CACHE_DIR = Path("extension/artifacts/extraction_cache")
FAMILIES = ["comprehension", "relevance", "principles", "wrong_operation", "steps"]

TEMPERATURE = 0.0
# Optional provider pinning (OpenRouter routing). None routes freely across
# all providers serving the slug. To pin, set an ordered list of provider
# names exactly as OpenRouter's model page spells them, e.g.
# PROVIDER_ORDER = ["Fireworks", "Together"]; with ALLOW_FALLBACKS = False
# routing is restricted to that list, converting the speed lottery into a
# constant. Every call's serving provider is recorded in meta for ranking.
PROVIDER_ORDER = None
ALLOW_FALLBACKS = False
# Optional output circuit breaker. None sends no cap (models run provider
# defaults). A generous value such as 40000 bounds runaway reasoning
# (observed: 51k reasoning tokens, $0.78, 20 minutes on one uncapped call)
# without recreating truncation, K3's ordinary appetite being 16-25k.
MAX_OUTPUT_TOKENS = None

# ---------------------------------------------------------------------------
# Dialogue records
# ---------------------------------------------------------------------------

def dialogues_from(dataset, split: str) -> List[dict]:
    """Turn a unit-level dataframe from load_dataset into a list of dialogue
    records ready for generate_annotation.

    Each record carries its own identity: {'dialogue_id', 'split',
    'conversation', 'units'}. The caller names the split (e.g. 'validation',
    'train', 'test'), which is what keeps identically indexed MathDial splits
    from colliding anywhere downstream, including in the cache.

    Only these fields are derived: the dataframe also holds labels, thread
    grammars, and MathDial's own confusion fields, none of which may ever
    reach a prompt. Never widen this."""
    records = []
    for did, group in dataset.groupby("dialogue_id", sort=True):
        records.append({
            "dialogue_id": int(did),
            "split": str(split),
            "conversation": group.iloc[-1]["conversation"],
            "units": list(group["turn"]),
        })
    return records


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def _model_dirname(model_slug: str) -> str:
    """Filesystem-safe folder name for a slug (slashes and colons replaced)."""
    return model_slug.replace("/", "__").replace(":", "-")


def cache_path(model_slug: str, prompt_name: str, dialogue_id: int,
               split: str = "validation") -> Path:
    # the validation gold is carved from the MathDial train split and keeps
    # its train indices, so its cache lives with train: annotating the full
    # train set later finds these dialogues already done and skips them
    if split == "validation":
        split = "train"
    folder = CACHE_DIR / split / _model_dirname(model_slug) / prompt_name
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{dialogue_id}.json"


def cached_ok(model_slug: str, prompt_name: str, dialogue_id: int,
              split: str = "validation") -> bool:
    path = cache_path(model_slug, prompt_name, dialogue_id, split)
    if not path.exists():
        return False
    try:
        return json.load(open(path)).get("valid", False)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Validation of the model's JSON against the unit list and invariants
# ---------------------------------------------------------------------------

def extract_json(text: str) -> dict:
    text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object found")
    return json.loads(text[start : end + 1])


def validate(obj: dict, units: List[str]) -> List[str]:
    errs: List[str] = []
    if not isinstance(obj, dict):
        return ["not a dict"]
    grid = obj.get("grid")
    if not isinstance(grid, list):
        return ["grid missing"]
    got_units = [r.get("unit") for r in grid if isinstance(r, dict)]
    if got_units != list(units):
        errs.append(f"units mismatch (got {got_units[:3]}...)")
    thread_ids = {t.get("id") for t in obj.get("threads", []) if isinstance(t, dict)}
    for t in obj.get("threads", []):
        if t.get("family") not in set(FAMILIES):
            errs.append(f"bad family {t.get('family')}")
        resolved_at = t.get("resolved_at")
        if resolved_at:
            row = next((r for r in grid if r.get("unit") == resolved_at), None)
            if not row or row.get(t.get("family")) != "A":
                errs.append(f"{t.get('id')}: no A at resolved_at {resolved_at}")
    for row in grid:
        for fam in FAMILIES:
            if row.get(fam) not in ("P", "A", "N"):
                errs.append(f"{row.get('unit')}: bad {fam}={row.get(fam)}")
        for fam, src in (row.get("srcs") or {}).items():
            # srcs matter only where a misconception is asserted; stray
            # strings on A/N cells are ignored rather than failing the record
            if row.get(fam) != "P":
                continue
            sids = src if isinstance(src, (list, tuple)) else str(src).split(",")
            for sid in sids:
                sid = str(sid).strip()
                if sid and sid not in thread_ids:
                    errs.append(f"{row.get('unit')}: unknown src {sid}")
    return errs


# ---------------------------------------------------------------------------
# The LLM call
# ---------------------------------------------------------------------------

def llm_call(model_slug: str, messages: List[dict],
             provider: Optional[str] = None,
             reasoning_effort: Optional[str] = None) -> Tuple[str, str, dict]:
    """One OpenRouter chat completion against the given slug (e.g.
    'moonshotai/kimi-k3'). Returns (content, reasoning_trace, meta) where
    meta carries latency, usage, and OpenRouter's accounted cost. ``provider``
    pins the call to one named provider (spelled as on the OpenRouter model
    page); None falls back to PROVIDER_ORDER, and free routing if that is
    also unset. ``reasoning_effort`` sets OpenRouter's reasoning effort
    ("low", "medium", "high", "xhigh" where the model supports them); None
    sends no reasoning field, leaving the provider's default in force."""
    order = [provider] if provider else PROVIDER_ORDER
    t0 = time.time()
    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost/annotation-screen",
            "X-Title": "annotation-grader-screen",
        },
        json={
            "model": model_slug,
            "messages": messages,
            "temperature": TEMPERATURE,
            "usage": {"include": True},
            **({"max_tokens": MAX_OUTPUT_TOKENS} if MAX_OUTPUT_TOKENS else {}),
            **({"provider": {"order": order,
                             "allow_fallbacks": ALLOW_FALLBACKS}}
               if order else {}),
            **({"reasoning": {"effort": reasoning_effort}}
               if reasoning_effort else {}),
        },
        timeout=None,
    )
    resp.raise_for_status()
    data = resp.json()
    if "choices" not in data or not data["choices"]:
        # error-in-body: providers sometimes return an error object with
        # HTTP 200; surface its message instead of a bare KeyError
        err = data.get("error") or {}
        raise RuntimeError(
            f"no choices in response: {err.get('message', json.dumps(data)[:300])}"
        )
    message = data["choices"][0]["message"]
    text = message.get("content") or ""
    # archival: reasoning models return their trace in a separate field
    # (OpenRouter normalises it to 'reasoning'; some providers use
    # 'reasoning_content'); captured for codebook-misreading diagnosis,
    # never used for extraction or scoring
    reasoning = message.get("reasoning") or message.get("reasoning_content") or ""
    usage = data.get("usage", {}) or {}
    cost = usage.get("cost") or 0.0
    return text, reasoning, {
        "latency_s": time.time() - t0, "usage": usage, "cost_usd": float(cost),
        "provider": data.get("provider"),
    }


# ---------------------------------------------------------------------------
# The entry point
# ---------------------------------------------------------------------------

def generate_annotation(prompt_name: str, model_slug: str, dialogue: dict,
                        provider: Optional[str] = None,
                        reasoning_effort: Optional[str] = None) -> str:
    """Annotate one dialogue under one prompt with one model.

    ``dialogue`` is a record from dialogues_from: {'dialogue_id', 'split',
    'conversation', 'units'}. No dialogue lookup happens here; identity and
    content arrive together. Messages are built by
    prompt_loader.prompt_constructor, sent by llm_call in a single call (no
    timeout, no retries), and the full record
    (raw output, reasoning trace, errors, usage, cost) is cached under
    extraction_cache/{split}/{model}/{prompt}/{id}.json.
    Returns 'cached', 'ok', or 'invalid'. ``provider`` optionally pins this
    call to one OpenRouter provider; omitted, routing behaves as configured
    at module level (PROVIDER_ORDER, or free routing). ``reasoning_effort``
    optionally overrides the model's reasoning effort for this call; None
    keeps the provider default. The record stores the effort sent.
    """
    if not model_slug or "/" not in model_slug:
        raise ValueError(f"{model_slug!r} does not look like an OpenRouter slug "
                         f"(expected 'vendor/model', e.g. 'moonshotai/kimi-k3')")
    missing = {"dialogue_id", "split", "conversation", "units"} - set(dialogue)
    if missing:
        raise KeyError(f"dialogue record missing fields: {sorted(missing)}")
    did, split = int(dialogue["dialogue_id"]), dialogue["split"]
    if cached_ok(model_slug, prompt_name, did, split):
        return "cached"
    units = list(dialogue["units"])
    messages = prompt_loader.prompt_constructor(
        prompt_name, did, dialogue["conversation"], units
    )
    record = {
        "model": model_slug,
        "prompt": prompt_name,
        "reasoning_effort": reasoning_effort,
        "dialogue_id": did,
        "split": split,
        "attempts": [],
        "valid": False,
        "annotation": None,
        "cost_usd": 0.0,
        "latency_s": 0.0,
    }
    try:
        text, reasoning, meta = llm_call(model_slug, messages, provider,
                                         reasoning_effort)
    except Exception as exc:  # noqa: BLE001 (transport layer; recorded, not retried)
        record["attempts"].append({"transport_error": str(exc)})
        json.dump(record, open(cache_path(model_slug, prompt_name, did, split), "w"), indent=1)
        return "invalid"
    record["cost_usd"] = meta["cost_usd"]
    record["latency_s"] = meta["latency_s"]
    try:
        obj = extract_json(text)
        errs = validate(obj, units)
    except Exception as exc:  # noqa: BLE001 (model output layer)
        obj, errs = None, [f"parse: {exc}"]
    record["attempts"].append({"raw": text[-4000:], "reasoning": reasoning,
                               "errors": errs, "meta": meta})
    if not errs:
        record["valid"] = True
        record["annotation"] = obj
    json.dump(record, open(cache_path(model_slug, prompt_name, did, split), "w"), indent=1)
    return "ok" if record["valid"] else "invalid"


def generate_annotations(
    prompt_name: str,
    model_slug: str,
    dialogues: List[dict],
    provider: Optional[str] = None,
    max_workers: int = 4,
    reasoning_effort: Optional[str] = None,
) -> Dict[int, str]:
    """Run generate_annotation over many dialogue records in parallel.

    Each dialogue is an independent request writing its own cache file, so
    parallelism is safe; max_workers bounds concurrent in-flight calls (4-6
    is polite to a pinned provider, higher risks rate limits). Cached cells
    return instantly without occupying a worker for long. Statuses are
    printed as calls complete (completion order, not input order) and
    returned as {dialogue_id: status}.
    """
    results: Dict[int, str] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(generate_annotation, prompt_name, model_slug, dlg,
                        provider, reasoning_effort):
            dlg["dialogue_id"] for dlg in dialogues
        }
        for fut in as_completed(futures):
            did = futures[fut]
            try:
                status = fut.result()
            except Exception as exc:  # noqa: BLE001 (surface, do not kill the batch)
                status = f"error: {exc}"
            results[did] = status
            print(f"  {did}: {status}")
    return results
