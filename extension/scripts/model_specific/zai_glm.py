"""Direct Z.ai backend for GLM-5.2 annotation runs.

Exists for one reason: OpenRouter's GLM-5.2 endpoints cap completions at
65,536 tokens, which kills max-effort ("xhigh") runs on hard dialogues,
while Z.ai's first-party API serves the model's documented 128K output.
This module calls https://api.z.ai/api/paas/v4/chat/completions directly and
uses the API's standard Event Stream. Streaming is necessary here because a
max-effort response can exceed an HTTP proxy's synchronous response window.
The shared cache layout, validator, and prompt constructor are reused, so
records score through the ordinary scoring path.

Configuration facts (from Z.ai's GLM-5.2 documentation):
- effort is the top-level ``reasoning_effort`` field, values "high" or
  "max"; OpenRouter's "xhigh" is an alias for "max"
- thinking is on by default; sent explicitly as {"type": "enabled"}
- temperature range is [0.0, 1.0]; the configuration here remains 0.01
  (near-deterministic, noted for methods)
- max output 128K; sent explicitly since the whole point is headroom
- streaming is enabled so reasoning/content chunks keep the connection alive
- usage returns token counts only, no cost accounting: cost_usd is
  recorded 0.0, meaning unaccounted, per the project convention

Records are cached under a backend-and-effort-qualified slug,
``zai-direct/glm-5.2-{effort}``, so they never collide with OpenRouter
records for the same model, and mixed-effort caches stay separated. Cache
records follow the shared OpenRouter layout; Z.ai's raw usage is retained in
``meta.usage`` and a normalised token summary is added at ``meta.tokens``.

Auth: ZAI_API_KEY in the environment, or in a .env file at the repo root
(a minimal parser is included; no python-dotenv dependency).
"""

from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from extension.scripts import prompt_loader
from extension.scripts.extraction import (cache_path, cached_ok, extract_json,
                                          validate)

ZAI_URL = "https://api.z.ai/api/paas/v4/chat/completions"

# --- model-specific configuration (GLM-5.2) ---------------------------------
# Effort is a model-specific scale, not a universal one: GLM-5.2 exposes
# exactly two levels, "high" and "max" ("xhigh" is OpenRouter's alias for
# "max" and is accepted here as a courtesy). Other models in this folder
# will declare their own scales; nothing generic assumes these values.
MODEL_ID = "glm-5.2"
SUPPORTED_EFFORTS = ("high", "max")
EFFORT_ALIASES = {"xhigh": "max"}
DEFAULT_EFFORT = "max"      # this backend exists for the max-effort arm;
                            # pass "high" explicitly for the default-effort
                            # configuration
TEMPERATURE = 0.01          # Z.ai's floor; the deterministic setting here
MAX_OUTPUT_TOKENS = 128000  # the headroom this backend exists for
# ----------------------------------------------------------------------------


def resolve_effort(reasoning_effort: str) -> str:
    """Validate an effort against this model's scale, resolving aliases."""
    effort = EFFORT_ALIASES.get(reasoning_effort, reasoning_effort)
    if effort not in SUPPORTED_EFFORTS:
        raise ValueError(
            f"{reasoning_effort!r} is not an effort level of {MODEL_ID}; "
            f"supported: {SUPPORTED_EFFORTS} (alias {list(EFFORT_ALIASES)})"
        )
    return effort


def _api_key() -> str:
    key = os.environ.get("ZAI_API_KEY")
    if not key:
        env = Path(".env")
        if env.exists():
            for line in env.read_text().splitlines():
                line = line.strip()
                if line.startswith("ZAI_API_KEY"):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'") \
                        if "=" in line else None
                    break
    if not key:
        raise RuntimeError("ZAI_API_KEY not set (environment or .env)")
    return key


def cache_slug(reasoning_effort: str = DEFAULT_EFFORT) -> str:
    """The slug these records cache and score under."""
    return f"zai-direct/{MODEL_ID}-{resolve_effort(reasoning_effort)}"


def _token_summary(usage: dict) -> dict[str, int]:
    """Normalise Z.ai usage without discarding its raw usage object."""
    usage = usage or {}
    prompt = int(usage.get("prompt_tokens") or 0)
    completion = int(usage.get("completion_tokens") or 0)
    cached = int(
        usage.get("cached_tokens")
        or (usage.get("prompt_tokens_details") or {}).get("cached_tokens")
        or 0
    )
    reasoning = int(
        (usage.get("completion_tokens_details") or {}).get("reasoning_tokens")
        or 0
    )
    return {
        "prompt": prompt,
        "cached_prompt": cached,
        "uncached_prompt": max(prompt - cached, 0),
        "completion": completion,
        "reasoning": reasoning,
        "visible_completion": max(completion - reasoning, 0),
        "total": int(usage.get("total_tokens") or prompt + completion),
    }


def _iter_sse_data(response):
    """Yield complete ``data:`` payloads from a standard Event Stream.

    SSE permits one event to span multiple ``data:`` lines. Z.ai ordinarily
    sends one JSON object per line, but collecting until the blank event
    boundary keeps the parser compliant and makes mocked/provider variants
    behave identically. Comments and non-data fields are ignored.
    """
    data_lines = []
    for raw_line in response.iter_lines(decode_unicode=True):
        if isinstance(raw_line, bytes):
            raw_line = raw_line.decode("utf-8")
        line = (raw_line or "").rstrip("\r")
        if not line:
            if data_lines:
                yield "\n".join(data_lines)
                data_lines = []
            continue
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
    if data_lines:
        yield "\n".join(data_lines)


def llm_call_zai(messages: List[dict],
                 reasoning_effort: str = DEFAULT_EFFORT) -> Tuple[str, str, dict]:
    """One streamed Z.ai completion. Return (content, reasoning, metadata)."""
    import requests
    reasoning_effort = resolve_effort(reasoning_effort)
    t0 = time.time()
    resp = requests.post(
        ZAI_URL,
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
            "Accept-Language": "en-US,en",
            "Accept": "text/event-stream",
        },
        json={
            "model": MODEL_ID,
            "messages": messages,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "thinking": {"type": "enabled"},
            "reasoning_effort": reasoning_effort,
            "stream": True,
        },
        stream=True,
        timeout=None,
    )
    resp.raise_for_status()
    content_parts: List[str] = []
    reasoning_parts: List[str] = []
    usage = {}
    finish_reason = None
    event_count = 0
    saw_done = False
    for payload in _iter_sse_data(resp):
        if payload == "[DONE]":
            saw_done = True
            break
        try:
            event = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"invalid SSE JSON: {payload[:300]}") from exc
        event_count += 1
        if event.get("error"):
            error = event["error"]
            message = error.get("message") if isinstance(error, dict) else error
            raise RuntimeError(f"Z.ai stream error: {message}")
        if event.get("usage"):
            usage = event["usage"]
        choices = event.get("choices") or []
        if not choices:
            continue
        choice = choices[0]
        delta = choice.get("delta") or choice.get("message") or {}
        content = delta.get("content")
        reasoning = delta.get("reasoning_content")
        if content:
            content_parts.append(content)
        if reasoning:
            reasoning_parts.append(reasoning)
        if choice.get("finish_reason") is not None:
            finish_reason = choice["finish_reason"]
    if event_count == 0:
        raise RuntimeError("Z.ai stream ended without any JSON events")
    if not saw_done:
        raise RuntimeError("Z.ai stream ended without data: [DONE]")
    text = "".join(content_parts)
    reasoning = "".join(reasoning_parts)
    return text, reasoning, {
        "latency_s": time.time() - t0,
        "usage": usage,
        "tokens": _token_summary(usage),
        "cost_usd": 0.0,  # unaccounted: Z.ai returns tokens, not cost
        "provider": "z-ai (direct)",
        "finish_reason": finish_reason,
        "stream_events": event_count,
        "stream_done": saw_done,
    }


def generate_annotation(prompt_name: str, dialogue: dict,
                        reasoning_effort: str = DEFAULT_EFFORT) -> str:
    """Annotate one dialogue record via the direct Z.ai backend.

    Same contract as extraction.generate_annotation: single call, no
    retries, full forensic record, 'cached' short-circuit on a valid
    record. Returns 'cached', 'ok', or 'invalid'.
    """
    reasoning_effort = resolve_effort(reasoning_effort)
    slug = cache_slug(reasoning_effort)
    did, split = dialogue["dialogue_id"], dialogue["split"]
    if cached_ok(slug, prompt_name, did, split):
        return "cached"
    messages = prompt_loader.prompt_constructor(
        prompt_name, did, dialogue["conversation"], dialogue["units"])
    record = {
        "model": slug,
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
    started = time.time()
    try:
        text, reasoning, meta = llm_call_zai(messages, reasoning_effort)
    except Exception as exc:  # noqa: BLE001 (transport layer; recorded, not retried)
        record["attempts"].append({"transport_error": f"{exc}"[:2000]})
        record["latency_s"] = time.time() - started
    else:
        try:
            annotation = extract_json(text)
            errors = validate(annotation, dialogue["units"])
        except Exception as exc:  # noqa: BLE001 (model output layer)
            annotation, errors = None, [f"parse: {exc}"]
        record["attempts"].append({
            "raw": text[-4000:], "reasoning": reasoning,
            "errors": errors, "meta": meta,
        })
        record["latency_s"] = meta["latency_s"]
        if not errors:
            record["valid"] = True
            record["annotation"] = annotation
    json.dump(
        record,
        open(cache_path(slug, prompt_name, did, split), "w"),
        indent=1,
    )
    return "ok" if record["valid"] else "invalid"


def generate_annotations(prompt_name: str, dialogues: List[dict],
                         reasoning_effort: str = DEFAULT_EFFORT,
                         max_workers: int = 2) -> Dict[int, str]:
    """Parallel runner over dialogue records; statuses print as they land."""
    results: Dict[int, str] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(generate_annotation, prompt_name, dlg, reasoning_effort):
            dlg["dialogue_id"] for dlg in dialogues
        }
        for fut in as_completed(futures):
            did = futures[fut]
            try:
                status = fut.result()
            except Exception as exc:  # noqa: BLE001
                status = f"error: {exc}"
            results[did] = status
            print(f"  {did}: {status}")
    return results
