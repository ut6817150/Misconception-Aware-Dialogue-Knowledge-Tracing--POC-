"""Direct Alibaba Cloud Model Studio backend for Qwen 3.8 Max.

This module mirrors ``moonshot_kimi.py``: it constructs the shared prompts,
streams one completion per dialogue, validates the annotation, and writes a
forensic cache record that the ordinary scoring code can read.

Live API discovery on 2026-08-04 confirmed that the saved ``QWEN_PI_KEY`` is
a Singapore-region workspace key and that its model catalogue contains the
exact ID ``qwen3.8-max``. Qwen 3.8 Max is thinking-only. Its documented
maximum reasoning effort is ``xhigh`` (mapped to a 262,144-token thinking
budget). The model does not permit effective temperature 0: values below
0.6 are reset to 0.6, so this backend sends 0.6 explicitly.

Records cache under ``qwen-direct/qwen3.8-max-{effort}``, separate from
OpenRouter Qwen records. Alibaba returns token usage but not a dollar cost,
so ``cost_usd`` remains 0.0 (unaccounted), matching the direct-Moonshot
project convention.

Auth: ``QWEN_PI_KEY`` in the environment or repo-root ``.env``. The default
base URL is the Singapore OpenAI-compatible endpoint. Override it with
``QWEN_BASE_URL`` if the key is moved to another region or a dedicated
workspace endpoint.
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
from extension.scripts.extraction import (
    cache_path,
    cached_ok,
    extract_json,
    validate,
)

DEFAULT_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

# --- model-specific configuration (Qwen 3.8 Max) ---------------------------
MODEL_ID = "qwen3.8-max"
SUPPORTED_EFFORTS = ("low", "medium", "xhigh")
EFFORT_ALIASES = {"high": "xhigh", "max": "xhigh"}
DEFAULT_EFFORT = "xhigh"
TEMPERATURE = 0.6  # Qwen 3.8 resets every lower value to 0.6.
NO_TOKEN_TIMEOUT_SECONDS: Optional[float] = 300.0
# No max_tokens field is sent: a cap can truncate the final annotation JSON.
# ----------------------------------------------------------------------------


class QwenStreamError(RuntimeError):
    """An incomplete stream together with any response received so far."""

    def __init__(
        self,
        message: str,
        text: str = "",
        reasoning: str = "",
        meta: Optional[dict] = None,
    ):
        super().__init__(message)
        self.text = text
        self.reasoning = reasoning
        self.meta = meta or {}


def resolve_effort(reasoning_effort: str) -> str:
    """Validate an effort against Qwen 3.8's scale, resolving aliases."""
    effort = EFFORT_ALIASES.get(reasoning_effort, reasoning_effort)
    if effort not in SUPPORTED_EFFORTS:
        raise ValueError(
            f"{reasoning_effort!r} is not an effort level of {MODEL_ID}; "
            f"supported: {SUPPORTED_EFFORTS} "
            f"(aliases: {EFFORT_ALIASES})"
        )
    return effort


def _env_value(name: str) -> Optional[str]:
    value = os.environ.get(name)
    if value:
        return value
    env = Path(".env")
    if not env.exists():
        return None
    for line in env.read_text().splitlines():
        line = line.strip()
        if line.startswith(f"{name}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _api_key() -> str:
    key = _env_value("QWEN_PI_KEY")
    if not key:
        raise RuntimeError("QWEN_PI_KEY not set (environment or .env)")
    return key


def _base_url() -> str:
    return (_env_value("QWEN_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")


def cache_slug(reasoning_effort: str = DEFAULT_EFFORT) -> str:
    """The slug these records cache and score under."""
    return f"qwen-direct/{MODEL_ID}-{resolve_effort(reasoning_effort)}"


def _token_summary(usage: dict) -> dict[str, int]:
    """Normalise OpenAI- and DashScope-style token usage fields."""
    usage = usage or {}
    prompt = int(
        usage.get("prompt_tokens") or usage.get("input_tokens") or 0
    )
    completion = int(
        usage.get("completion_tokens") or usage.get("output_tokens") or 0
    )
    prompt_details = usage.get("prompt_tokens_details") or {}
    completion_details = usage.get("completion_tokens_details") or {}
    cached = int(
        usage.get("cached_tokens")
        or prompt_details.get("cached_tokens")
        or 0
    )
    reasoning = int(
        usage.get("reasoning_tokens")
        or completion_details.get("reasoning_tokens")
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
        if line.startswith(":"):
            continue
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
    if data_lines:
        yield "\n".join(data_lines)


def llm_call_qwen(
    messages: List[dict],
    reasoning_effort: str = DEFAULT_EFFORT,
) -> Tuple[str, str, dict]:
    """Stream one Qwen completion; return content, reasoning, and metadata."""
    import requests

    reasoning_effort = resolve_effort(reasoning_effort)
    t0 = time.time()
    resp = requests.post(
        f"{_base_url()}/chat/completions",
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        json={
            "model": MODEL_ID,
            "messages": messages,
            "temperature": TEMPERATURE,
            "reasoning_effort": reasoning_effort,
            "stream": True,
            "stream_options": {"include_usage": True},
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
            "cost_usd": 0.0,
            "provider": "Alibaba Cloud Model Studio (direct)",
            "base_url": _base_url(),
            "finish_reason": finish_reason,
            "stream": True,
            "stream_events": event_count,
            "stream_done": saw_done,
            "no_token_timeout_s": NO_TOKEN_TIMEOUT_SECONDS,
            "temperature": TEMPERATURE,
            "reasoning_effort": reasoning_effort,
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
                message = (
                    error.get("message")
                    if isinstance(error, dict) else error
                )
                raise RuntimeError(f"Qwen stream error: {message}")
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
            reasoning = (
                delta.get("reasoning_content") or delta.get("reasoning")
            )
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
                f"no model token received for "
                f"{NO_TOKEN_TIMEOUT_SECONDS:g}s"
            )
    except Exception as exc:
        error = exc
        if no_token_timed_out.is_set():
            error = TimeoutError(
                f"no model token received for "
                f"{NO_TOKEN_TIMEOUT_SECONDS:g}s"
            )
        raise QwenStreamError(
            str(error),
            "".join(content_parts),
            "".join(reasoning_parts),
            metadata(),
        ) from exc
    finally:
        stream_finished.set()
        resp.close()
        watchdog.join(timeout=0.1)

    text = "".join(content_parts)
    reasoning = "".join(reasoning_parts)
    if not saw_done:
        raise QwenStreamError(
            "Qwen stream ended without [DONE]",
            text,
            reasoning,
            metadata(),
        )
    return text, reasoning, metadata()


def generate_annotation(
    prompt_name: str,
    dialogue: dict,
    reasoning_effort: str = DEFAULT_EFFORT,
) -> str:
    """Annotate one dialogue and persist the shared forensic record."""
    reasoning_effort = resolve_effort(reasoning_effort)
    slug = cache_slug(reasoning_effort)
    did, split = dialogue["dialogue_id"], dialogue["split"]
    if cached_ok(slug, prompt_name, did, split):
        return "cached"
    messages = prompt_loader.prompt_constructor(
        prompt_name,
        did,
        dialogue["conversation"],
        dialogue["units"],
    )
    record = {
        "model": slug,
        "prompt": prompt_name,
        "reasoning_effort": reasoning_effort,
        "temperature": TEMPERATURE,
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
        text, reasoning, meta = llm_call_qwen(
            messages, reasoning_effort
        )
    except QwenStreamError as exc:
        record["attempts"].append({
            "transport_error": str(exc)[:2000],
            "raw": exc.text[-4000:],
            "reasoning": exc.reasoning,
            "errors": [f"incomplete stream: {exc}"],
            "meta": exc.meta,
        })
        record["latency_s"] = exc.meta.get(
            "latency_s", time.time() - started
        )
    except Exception as exc:
        record["attempts"].append({
            "transport_error": f"{exc}"[:2000]
        })
        record["latency_s"] = time.time() - started
    else:
        try:
            obj = extract_json(text)
            errors = validate(obj, dialogue["units"])
        except Exception as exc:
            obj, errors = None, [f"parse: {exc}"]
        record["attempts"].append({
            "raw": text[-4000:],
            "reasoning": reasoning,
            "errors": errors,
            "meta": meta,
        })
        record["latency_s"] = meta["latency_s"]
        if not errors:
            record["valid"] = True
            record["annotation"] = obj
    with open(cache_path(slug, prompt_name, did, split), "w") as handle:
        json.dump(record, handle, indent=1)
    return "ok" if record["valid"] else "invalid"


def generate_annotations(
    prompt_name: str,
    dialogues: List[dict],
    reasoning_effort: str = DEFAULT_EFFORT,
    max_workers: int = 2,
) -> Dict[int, str]:
    """Parallel runner over dialogue records; statuses print as they land."""
    results: Dict[int, str] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(
                generate_annotation,
                prompt_name,
                dialogue,
                reasoning_effort,
            ): dialogue["dialogue_id"]
            for dialogue in dialogues
        }
        for future in as_completed(futures):
            did = futures[future]
            try:
                status = future.result()
            except Exception as exc:
                status = f"error: {exc}"
            results[did] = status
            print(f"  {did}: {status}")
    return results
