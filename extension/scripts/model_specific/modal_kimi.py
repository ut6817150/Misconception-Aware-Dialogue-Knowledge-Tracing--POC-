"""Kimi K3 annotation backend for Utsav's Modal Auto Endpoint.

The endpoint is an authenticated, OpenAI-compatible deployment of
``moonshotai/Kimi-K3``. This module keeps its results separate from both the
OpenRouter Kimi cache and Moonshot's first-party API cache while reusing the
project's prompt construction, JSON validation, cache layout, and scoring.

Endpoint and authentication
---------------------------
The deployed endpoint defaults to ``MODAL_ENDPOINT_URL`` below. Override it
with that environment variable (or ``MODAL-ENDPOINT-URL`` in ``.env``).
Authentication accepts either:

* ``MODAL_KEY`` and ``MODAL_SECRET`` environment variables; or
* the existing ``MODAL-KEY`` and ``MODAL-SECRET`` entries in the repo-root
  ``.env`` file.

An optional combined ``MODAL_AUTHORIZATION``/``MODAL-AUTHORIZATION`` value is
also supported. Credentials are read at request time and are never cached.

Model configuration
-------------------
The endpoint's ``/v1/models`` response reports reasoning efforts ``low``,
``high``, and ``max``. This backend explicitly selects ``max`` reasoning and
temperature 0.0. No output-token ceiling is imposed unless
``MAX_OUTPUT_TOKENS`` is set.

Modal bills this Auto Endpoint by compute time rather than returning a
per-request dollar cost. Cache records therefore retain token usage and use
``cost_usd = 0.0`` as the project's marker for unaccounted cost; it must not
be interpreted as free inference.
"""

from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

from extension.scripts import prompt_loader
from extension.scripts.extraction import (
    cache_path,
    cached_ok,
    extract_json,
    validate,
)

DEFAULT_ENDPOINT_URL = (
    "https://utsavtandon96--ep-kimi-k3-server.us-west.modal.direct"
)
MODEL_ID = "moonshotai/Kimi-K3"
SUPPORTED_EFFORTS = ("low", "high", "max")
DEFAULT_REASONING_EFFORT: Optional[str] = "max"
TEMPERATURE = 0.0
MAX_OUTPUT_TOKENS: Optional[int] = None

# Retry only failures that normally happen before generation begins. In
# particular, a 502 is *not* replayed: Modal has returned those after ten
# minutes of inference, so an automatic retry would repeat the same expensive
# work while blocking the batch. A later notebook run can retry the resulting
# invalid cache record deliberately.
MAX_REQUEST_ATTEMPTS = 3
RETRYABLE_STATUS_CODES = {429, 503, 504}


class ModalStreamError(RuntimeError):
    """A failed/incomplete stream together with any chunks received so far."""

    def __init__(self, message: str, text: str = "", reasoning: str = "",
                 meta: Optional[dict] = None):
        super().__init__(message)
        self.text = text
        self.reasoning = reasoning
        self.meta = meta or {}


def _dotenv_values(path: Path = Path(".env")) -> dict[str, str]:
    """Read the small subset of dotenv syntax needed by this project."""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _setting(*names: str) -> Optional[str]:
    """Return the first non-empty setting from the environment or ``.env``."""
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    dotenv = _dotenv_values()
    for name in names:
        value = dotenv.get(name)
        if value:
            return value
    return None


def endpoint_url() -> str:
    """Return the configured endpoint root without a trailing ``/v1``."""
    url = _setting("MODAL_ENDPOINT_URL", "MODAL-ENDPOINT-URL")
    url = (url or DEFAULT_ENDPOINT_URL).rstrip("/")
    return url[:-3] if url.endswith("/v1") else url


def _auth_headers() -> dict[str, str]:
    """Build Modal proxy-token headers without exposing their values."""
    key = _setting("MODAL_KEY", "MODAL-KEY")
    secret = _setting("MODAL_SECRET", "MODAL-SECRET")
    if key and secret:
        return {"Modal-Key": key, "Modal-Secret": secret}

    authorization = _setting("MODAL_AUTHORIZATION", "MODAL-AUTHORIZATION")
    if authorization:
        if not authorization.lower().startswith("bearer "):
            authorization = f"Bearer {authorization}"
        return {"Authorization": authorization}

    raise RuntimeError(
        "Modal proxy credentials not found. Set MODAL_KEY and MODAL_SECRET, "
        "or add MODAL-KEY and MODAL-SECRET to the repo-root .env file."
    )


def credentials_available() -> bool:
    """Report whether a supported credential pair exists, without printing it."""
    try:
        _auth_headers()
    except RuntimeError:
        return False
    return True


def _headers() -> dict[str, str]:
    return {"Content-Type": "application/json", **_auth_headers()}


def endpoint_info() -> dict:
    """Fetch and return the endpoint's advertised model record."""
    response = requests.get(
        f"{endpoint_url()}/v1/models", headers=_headers(), timeout=30
    )
    if not response.ok:
        raise RuntimeError(_http_error(response))
    models = response.json().get("data") or []
    if not models:
        raise RuntimeError("Modal endpoint returned no models")
    model = next((item for item in models if item.get("id") == MODEL_ID), None)
    if model is None:
        served = [item.get("id") for item in models]
        raise RuntimeError(f"endpoint does not serve {MODEL_ID!r}; found {served}")
    return model


def resolve_effort(reasoning_effort: Optional[str]) -> Optional[str]:
    """Validate a requested Kimi K3 reasoning effort."""
    if reasoning_effort is not None and reasoning_effort not in SUPPORTED_EFFORTS:
        raise ValueError(
            f"unsupported reasoning effort {reasoning_effort!r}; "
            f"choose one of {SUPPORTED_EFFORTS} or None"
        )
    return reasoning_effort


def cache_slug(
    reasoning_effort: Optional[str] = DEFAULT_REASONING_EFFORT,
) -> str:
    """Return a backend-and-effort-qualified cache/scoring identifier."""
    effort = resolve_effort(reasoning_effort) or "default"
    return f"modal-endpoint/kimi-k3-{effort}"


def _token_summary(usage: dict) -> dict[str, int]:
    """Normalise token fields while retaining Modal's raw usage object."""
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


def _http_error(response: requests.Response) -> str:
    """Preserve Modal's response body and retry hint in transport errors."""
    body = response.text.strip().replace("\n", " ")[:1500]
    retry_after = response.headers.get("Retry-After")
    detail = f"HTTP {response.status_code} from Modal endpoint"
    if retry_after:
        detail += f" (Retry-After: {retry_after})"
    if body:
        detail += f": {body}"
    return detail


def _retry_delay(response: requests.Response, attempt: int) -> float:
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        try:
            return max(float(retry_after), 0.0)
        except ValueError:
            pass
    return float(2 ** attempt)


def _iter_sse_data(response: requests.Response):
    """Yield complete ``data:`` payloads from an SSE response.

    OpenAI-compatible servers ordinarily send one data line per event, but
    joining consecutive data lines also implements the SSE multiline rule.
    Blank keep-alives and comment lines are ignored.
    """
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


def llm_call_modal(
    messages: List[dict],
    reasoning_effort: Optional[str] = DEFAULT_REASONING_EFFORT,
) -> Tuple[str, str, dict]:
    """Stream one Kimi K3 completion and return its assembled response.

    Streaming makes Modal return headers and token chunks while Kimi reasons,
    avoiding the ten-minute no-response gateway failure seen with buffered
    ``stream=False`` requests. A stream that terminates without ``[DONE]`` or
    a finish reason is rejected rather than mistaken for a complete result.
    """
    effort = resolve_effort(reasoning_effort)
    payload = {
        "model": MODEL_ID,
        "messages": messages,
        "temperature": TEMPERATURE,
        "stream": True,
        "stream_options": {"include_usage": True},
        **({"max_tokens": MAX_OUTPUT_TOKENS} if MAX_OUTPUT_TOKENS else {}),
        **({"reasoning_effort": effort} if effort else {}),
    }
    started = time.time()
    response = None
    request_attempts = 0
    for attempt in range(MAX_REQUEST_ATTEMPTS):
        request_attempts = attempt + 1
        response = requests.post(
            f"{endpoint_url()}/v1/chat/completions",
            headers={**_headers(), "Accept": "text/event-stream"},
            json=payload,
            stream=True,
            timeout=None,
        )
        if response.ok:
            break
        error = _http_error(response)
        status = response.status_code
        response.close()
        if (
            status not in RETRYABLE_STATUS_CODES
            or request_attempts == MAX_REQUEST_ATTEMPTS
        ):
            raise RuntimeError(error)
        time.sleep(_retry_delay(response, attempt))

    if response is None or not response.ok:
        raise RuntimeError("Modal endpoint request failed without a response")

    content_parts: List[str] = []
    reasoning_parts: List[str] = []
    usage: dict = {}
    finish_reason = None
    event_count = 0
    saw_done = False
    first_event_s: Optional[float] = None
    first_token_s: Optional[float] = None

    def metadata() -> dict:
        return {
            "latency_s": time.time() - started,
            "first_event_s": first_event_s,
            "first_token_s": first_token_s,
            "usage": usage,
            "tokens": _token_summary(usage),
            "cost_usd": 0.0,
            "cost_accounting": "unavailable; Modal Auto Endpoint is compute-billed",
            "provider": "modal auto endpoint (direct)",
            "endpoint": endpoint_url(),
            "finish_reason": finish_reason,
            "request_attempts": request_attempts,
            "stream": True,
            "stream_events": event_count,
            "stream_done": saw_done,
        }

    try:
        for event_payload in _iter_sse_data(response):
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
                first_event_s = time.time() - started
            if event.get("error"):
                error = event["error"]
                message = error.get("message") if isinstance(error, dict) else error
                raise RuntimeError(f"Modal stream error: {message}")
            if event.get("usage"):
                usage = event["usage"]
            choices = event.get("choices") or []
            if not choices:
                continue
            choice = choices[0]
            delta = choice.get("delta") or choice.get("message") or {}
            content = delta.get("content")
            reasoning = delta.get("reasoning_content") or delta.get("reasoning")
            if content:
                content_parts.append(content)
            if reasoning:
                reasoning_parts.append(reasoning)
            if (content or reasoning) and first_token_s is None:
                first_token_s = time.time() - started
            if choice.get("finish_reason") is not None:
                finish_reason = choice["finish_reason"]
    except Exception as exc:
        raise ModalStreamError(
            str(exc), "".join(content_parts), "".join(reasoning_parts), metadata()
        ) from exc
    finally:
        response.close()

    text = "".join(content_parts)
    reasoning = "".join(reasoning_parts)
    if not saw_done and finish_reason is None:
        raise ModalStreamError(
            "Modal stream ended without [DONE] or a finish reason",
            text,
            reasoning,
            metadata(),
        )
    return text, reasoning, metadata()


def generate_annotation(
    prompt_name: str,
    dialogue: dict,
    reasoning_effort: Optional[str] = DEFAULT_REASONING_EFFORT,
) -> str:
    """Annotate and cache one dialogue through the Modal Auto Endpoint."""
    effort = resolve_effort(reasoning_effort)
    slug = cache_slug(effort)
    missing = {"dialogue_id", "split", "conversation", "units"} - set(dialogue)
    if missing:
        raise KeyError(f"dialogue record missing fields: {sorted(missing)}")
    did, split = int(dialogue["dialogue_id"]), str(dialogue["split"])
    if cached_ok(slug, prompt_name, did, split):
        return "cached"

    units = list(dialogue["units"])
    messages = prompt_loader.prompt_constructor(
        prompt_name, did, dialogue["conversation"], units
    )
    record = {
        "model": slug,
        "backend": "modal-endpoint",
        "endpoint_model": MODEL_ID,
        "prompt": prompt_name,
        "reasoning_effort": effort,
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
        text, reasoning, meta = llm_call_modal(messages, effort)
    except ModalStreamError as exc:
        record["attempts"].append(
            {
                "transport_error": str(exc)[:2000],
                "raw": exc.text[-4000:],
                "reasoning": exc.reasoning,
                "errors": [f"incomplete stream: {exc}"],
                "meta": exc.meta,
            }
        )
        record["latency_s"] = exc.meta.get("latency_s", time.time() - started)
    except Exception as exc:  # noqa: BLE001 - failure is preserved in the cache
        record["attempts"].append({"transport_error": str(exc)[:2000]})
        record["latency_s"] = time.time() - started
    else:
        try:
            annotation = extract_json(text)
            errors = validate(annotation, units)
        except Exception as exc:  # noqa: BLE001 - parsing failure is forensic data
            annotation, errors = None, [f"parse: {exc}"]
        record["attempts"].append(
            {
                "raw": text[-4000:],
                "reasoning": reasoning,
                "errors": errors,
                "meta": meta,
            }
        )
        record["latency_s"] = meta["latency_s"]
        if not errors:
            record["valid"] = True
            record["annotation"] = annotation

    with cache_path(slug, prompt_name, did, split).open("w") as handle:
        json.dump(record, handle, indent=1)
    return "ok" if record["valid"] else "invalid"


def generate_annotations(
    prompt_name: str,
    dialogues: List[dict],
    reasoning_effort: Optional[str] = DEFAULT_REASONING_EFFORT,
    max_workers: int = 2,
) -> Dict[int, str]:
    """Run independent dialogue annotations with bounded parallelism."""
    results: Dict[int, str] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(generate_annotation, prompt_name, dialogue, reasoning_effort):
            dialogue["dialogue_id"]
            for dialogue in dialogues
        }
        for future in as_completed(futures):
            did = futures[future]
            try:
                status = future.result()
            except Exception as exc:  # noqa: BLE001 - keep the batch running
                status = f"error: {exc}"
            results[did] = status
            print(f"  {did}: {status}")
    return results
