"""Direct Moonshot backend for Kimi K3 annotation runs.

Escapes third-party serving caps: Moonshot's first-party API defaults
``max_completion_tokens`` to 131,072 (double the 65,536 that killed cells
on OpenRouter's Modal route) and allows up to 1,048,576, with automatic
prefix caching that discounts the repeated P1 system prompt. Calls
https://api.moonshot.ai/v1/chat/completions directly, reusing the shared
cache layout, validator, and prompt constructor, so records score through
the ordinary scoring path.

Configuration facts (from platform.kimi.ai's K3 quickstart):
- effort is the top-level ``reasoning_effort`` field: "low", "high", or
  "max" (the platform default); thinking is always on and cannot be
  disabled
- temperature (1.0), top_p (0.95), n, and the penalties are FIXED
  server-side and must be omitted from requests; K3 output is therefore
  stochastic across runs on this backend too
- ``max_completion_tokens`` defaults to 131,072; MAX_COMPLETION_TOKENS
  below stays None to accept that default, or set an integer (up to
  1,048,576) for more headroom
- usage returns token counts (with cache-hit accounting on billing) but
  no cost field: cost_usd is recorded 0.0, meaning unaccounted, per the
  project convention

Responses are consumed as SSE streams so long reasoning runs continue to
deliver data instead of waiting for one buffered response. Records cache under
a backend-and-effort-qualified slug,
``moonshot-direct/kimi-k3-{effort}``, so they never mix with OpenRouter
K3 records or across efforts. The cache record follows the shared
OpenRouter layout; Moonshot's raw usage is retained in ``meta.usage`` and a
normalised token summary is added at ``meta.tokens``.

Auth: MOONSHOT_API_KEY in the environment, or in a .env file at the repo
root (minimal parser included; no python-dotenv dependency).
"""

from __future__ import annotations

import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from extension.scripts import prompt_loader
from extension.scripts.extraction import (cache_path, cached_ok,
                                           extract_json, validate)

MOONSHOT_URL = "https://api.moonshot.ai/v1/chat/completions"

# --- model-specific configuration (Kimi K3) ---------------------------------
# Effort is a model-specific scale: K3 exposes "low", "high", and "max",
# with "max" the platform default (and the configuration the OpenRouter
# sweeps ran, since no effort field was ever sent there).
MODEL_ID = "kimi-k3"
SUPPORTED_EFFORTS = ("low", "high", "max")
EFFORT_ALIASES = {"xhigh": "max"}  # courtesy for OpenRouter muscle memory
DEFAULT_EFFORT = "max"
MAX_COMPLETION_TOKENS: Optional[int] = None  # None = server default 131,072;
                                             # set an int (<= 1,048,576) to
                                             # raise it for deadlock cells
NO_TOKEN_TIMEOUT_SECONDS: Optional[float] = 300.0
# ----------------------------------------------------------------------------


class MoonshotStreamError(RuntimeError):
    """An incomplete stream together with any response received so far."""

    def __init__(self, message: str, text: str = "", reasoning: str = "",
                 meta: Optional[dict] = None):
        super().__init__(message)
        self.text = text
        self.reasoning = reasoning
        self.meta = meta or {}


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
    key = os.environ.get("MOONSHOT_API_KEY")
    if not key:
        env = Path(".env")
        if env.exists():
            for line in env.read_text().splitlines():
                line = line.strip()
                if line.startswith("MOONSHOT_API_KEY"):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'") \
                        if "=" in line else None
                    break
    if not key:
        raise RuntimeError("MOONSHOT_API_KEY not set (environment or .env)")
    return key


def cache_slug(reasoning_effort: str = DEFAULT_EFFORT) -> str:
    """The slug these records cache and score under."""
    return f"moonshot-direct/{MODEL_ID}-{resolve_effort(reasoning_effort)}"


def _token_summary(usage: dict) -> dict[str, int]:
    """Normalise Moonshot usage without discarding its raw usage object.

    Reasoning tokens are already included in completion tokens, while cached
    prompt tokens are already included in prompt tokens. The derived visible
    and uncached counts therefore subtract those subsets rather than adding
    them to the total.
    """
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
    """Yield complete payloads from ``data:`` fields in an SSE response."""
    data_lines: List[str] = []
    for raw_line in response.iter_lines(decode_unicode=True):
        if raw_line is None:
            continue
        if isinstance(raw_line, bytes):
            raw_line = raw_line.decode("utf-8")
        line = raw_line.rstrip("\r")
        if not line:
            if data_lines:
                yield "\n".join(data_lines)
                data_lines = []
            continue
        if line.startswith(":"):  # SSE comment/keep-alive
            continue
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
    if data_lines:
        yield "\n".join(data_lines)


def llm_call_moonshot(messages: List[dict],
                      reasoning_effort: str = DEFAULT_EFFORT) -> Tuple[str, str, dict]:
    """Stream one Moonshot completion. Return content, reasoning, and metadata.

    Sampling parameters are deliberately absent: Moonshot fixes them
    server-side and documents that they be omitted.
    """
    import requests
    reasoning_effort = resolve_effort(reasoning_effort)
    t0 = time.time()
    resp = requests.post(
        MOONSHOT_URL,
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        json={
            "model": MODEL_ID,
            "messages": messages,
            "reasoning_effort": reasoning_effort,
            "stream": True,
            "stream_options": {"include_usage": True},
            **({"max_completion_tokens": MAX_COMPLETION_TOKENS}
               if MAX_COMPLETION_TOKENS else {}),
        },
        stream=True,
        timeout=None,
    )
    resp.raise_for_status()
    content_parts: List[str] = []
    reasoning_parts: List[str] = []
    usage: dict = {}
    finish_reason = None
    event_count = 0
    saw_done = False
    first_event_s: Optional[float] = None
    first_token_s: Optional[float] = None
    last_token_at = time.monotonic()
    stream_finished = threading.Event()
    no_token_timed_out = threading.Event()

    def no_token_watchdog() -> None:
        """Close the response if meaningful model output stops arriving."""
        if not NO_TOKEN_TIMEOUT_SECONDS:
            return
        while not stream_finished.is_set():
            remaining = NO_TOKEN_TIMEOUT_SECONDS - (
                time.monotonic() - last_token_at
            )
            if remaining <= 0:
                no_token_timed_out.set()
                resp.close()
                return
            stream_finished.wait(min(remaining, 1.0))

    watchdog = threading.Thread(target=no_token_watchdog, daemon=True)
    watchdog.start()

    def metadata() -> dict:
        return {
            "latency_s": time.time() - t0,
            "first_event_s": first_event_s,
            "first_token_s": first_token_s,
            "usage": usage,
            "tokens": _token_summary(usage),
            "cost_usd": 0.0,  # unaccounted: Moonshot returns tokens, not cost
            "provider": "moonshot (direct)",
            "finish_reason": finish_reason,
            "stream": True,
            "stream_events": event_count,
            "stream_done": saw_done,
            "no_token_timeout_s": NO_TOKEN_TIMEOUT_SECONDS,
        }

    try:
        for event_payload in _iter_sse_data(resp):
            if event_payload == "[DONE]":
                saw_done = True
                break
            try:
                event = json.loads(event_payload)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"invalid SSE JSON: {event_payload[:300]}"
                ) from exc
            event_count += 1
            if first_event_s is None:
                first_event_s = time.time() - t0
            if event.get("error"):
                error = event["error"]
                message = error.get("message") if isinstance(error, dict) else error
                raise RuntimeError(f"Moonshot stream error: {message}")
            if event.get("usage"):
                usage = event["usage"]
            choices = event.get("choices") or []
            if not choices:
                continue
            choice = choices[0]
            if choice.get("usage"):
                usage = choice["usage"]
            delta = choice.get("delta") or choice.get("message") or {}
            content = delta.get("content")
            reasoning = delta.get("reasoning_content") or delta.get("reasoning")
            if content:
                content_parts.append(content)
            if reasoning:
                reasoning_parts.append(reasoning)
            if (content or reasoning) and first_token_s is None:
                first_token_s = time.time() - t0
            if content or reasoning:
                last_token_at = time.monotonic()
            if choice.get("finish_reason") is not None:
                finish_reason = choice["finish_reason"]
        if no_token_timed_out.is_set():
            raise TimeoutError(
                f"no model token received for {NO_TOKEN_TIMEOUT_SECONDS:g}s"
            )
    except Exception as exc:
        error = exc
        if no_token_timed_out.is_set():
            error = TimeoutError(
                f"no model token received for {NO_TOKEN_TIMEOUT_SECONDS:g}s"
            )
        raise MoonshotStreamError(
            str(error), "".join(content_parts), "".join(reasoning_parts),
            metadata(),
        ) from exc
    finally:
        stream_finished.set()
        resp.close()
        watchdog.join(timeout=0.1)

    text = "".join(content_parts)
    reasoning = "".join(reasoning_parts)
    if not saw_done:
        raise MoonshotStreamError(
            "Moonshot stream ended without [DONE]", text, reasoning, metadata()
        )
    return text, reasoning, metadata()


def generate_annotation(prompt_name: str, dialogue: dict,
                        reasoning_effort: str = DEFAULT_EFFORT) -> str:
    """Annotate one dialogue record via the direct Moonshot backend.

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
        text, reasoning, meta = llm_call_moonshot(messages, reasoning_effort)
    except MoonshotStreamError as exc:
        record["attempts"].append({
            "transport_error": str(exc)[:2000],
            "raw": exc.text[-4000:],
            "reasoning": exc.reasoning,
            "errors": [f"incomplete stream: {exc}"],
            "meta": exc.meta,
        })
        record["latency_s"] = exc.meta.get("latency_s", time.time() - started)
    except Exception as exc:  # noqa: BLE001 (recorded, not retried)
        record["attempts"].append({"transport_error": f"{exc}"[:2000]})
        record["latency_s"] = time.time() - started
    else:
        try:
            obj = extract_json(text)
            errors = validate(obj, dialogue["units"])
        except Exception as exc:  # noqa: BLE001 (parse failure, recorded)
            obj, errors = None, [f"parse: {exc}"]
        record["attempts"].append({
            "raw": text[-4000:], "reasoning": reasoning,
            "errors": errors, "meta": meta,
        })
        record["latency_s"] = meta["latency_s"]
        if not errors:
            record["valid"] = True
            record["annotation"] = obj
    json.dump(
        record,
        open(cache_path(slug, prompt_name, did, split), "w"),
        indent=1,
    )
    return "ok" if record["valid"] else "invalid"


def generate_annotations(prompt_name: str, dialogues: List[dict],
                         reasoning_effort: str = DEFAULT_EFFORT,
                         max_workers: int = 2) -> Dict[int, str]:
    """Parallel runner over dialogue records; statuses print as they land.

    Keep max_workers modest: Moonshot rate limits scale with the account's
    top-up tier, and 429s land as recorded transport errors (no retries).
    """
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
