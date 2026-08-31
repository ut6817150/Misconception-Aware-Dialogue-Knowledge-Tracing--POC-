"""Per-dialogue misconception annotation via the OpenRouter API.

The public entry point is ``generate_annotation(prompt_name, model_name,
dialogue)``: it takes a self-contained dialogue record produced by
``dialogues_from`` (dataframe in, list of dialogues out), builds the messages
through ``prompt_loader.prompt_constructor``, sends them with ``llm_call``,
validates the returned JSON, and saves the full record (raw output, reasoning
trace, errors, usage, cost) to
``extension/artifacts/extraction_cache/{split}/{model}/{prompt}/{id}.json``.
Re-runs skip cells already cached as valid. Scoring reads only the cache.

Prompts listed in SCAN_PROMPTS additionally emit a per-unit line
scan and a departures ledger before the annotation proper; ``validate``
enforces their structural invariants so that a scanned departure cannot be
silently dropped, every thread is founded by exactly one departure at its
origin, and every present cell is backed by a founding or exhibiting
departure in its own unit.

The API key is read from the environment variable OPENROUTER_API_KEY and is
never written to disk. No output-token cap is sent; models run their
provider defaults, and cost comes from OpenRouter usage accounting per call.
"""

from __future__ import annotations

import json
import os
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

from . import prompt_loader
from .schema import FAMILIES

BASE_URL = "https://openrouter.ai/api/v1"
CACHE_DIR = Path("extension/artifacts/extraction_cache")

# Prompts whose output schema carries the mandatory scan and departures
# sections. Membership switches the scan invariants in ``validate`` from
# opportunistic (checked when present) to required.
SCAN_PROMPTS = {"P7", "P8", "P9", "P10", "P11", "P12"}

# Prompts under the v8 rules: principles grounds, family-consistent citations,
# and verbatim quote containment are additionally enforced.
V8_PROMPTS = {"P8", "P9", "P10", "P11", "P12"}
V9_PROMPTS = {"P9", "P10", "P11", "P12"}

DISPOSITION_RE = re.compile(
    r"^(?:(?:founds|exhibits|shadow of) S\d+|slip|available-reading|tutor-supplied)$"
)

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


def _thread_family_at(thread: dict, unit: str, units: List[str]) -> Optional[str]:
    """Return a thread's active family at one unit.

    P10 records a migrated thread with ``family`` as its final family and
    the paired ``origin_family``/``reattributed_at`` fields describing the
    earlier attribution. Older prompt schemas omit both fields, in which
    case the thread's family is constant as before.
    """
    family = thread.get("family")
    origin_family = thread.get("origin_family")
    reattributed_at = thread.get("reattributed_at")
    if origin_family is None or reattributed_at is None:
        return family
    try:
        return (
            origin_family
            if units.index(unit) < units.index(reattributed_at)
            else family
        )
    except ValueError:
        # Field-shape errors are reported by ``validate``. Returning the
        # final family here avoids turning malformed metadata into a crash.
        return family


def _validate_scan(obj: dict, units: List[str], grid: list,
                   thread_ids: set, require_scan: bool,
                   conversation: str = "", v8: bool = False,
                   v9: bool = False) -> List[str]:
    """Invariants for the P7-P10 scan and departures sections.

    Structural only, by design: the validator cannot judge whether a
    disposition is the right one, but it guarantees that every scanned
    departure receives exactly one explicit disposition, that dispositions
    use the closed vocabulary, that every thread is founded by exactly one
    departure at its origin unit, and that every present cell is backed by a
    founding or exhibiting departure in its own unit. A departure can be
    disposed of wrongly; it can no longer evaporate."""
    errs: List[str] = []
    scan = obj.get("scan")
    if not isinstance(scan, list):
        if require_scan:
            errs.append("scan missing")
        return errs
    scan_units = [e.get("unit") for e in scan if isinstance(e, dict)]
    if scan_units != list(units):
        errs.append(f"scan units mismatch (got {scan_units[:3]}...)")
    scan_departures: List[Tuple[str, str]] = []
    for entry in scan:
        if not isinstance(entry, dict):
            continue
        unit = entry.get("unit")
        lines = entry.get("lines")
        if not isinstance(lines, list):
            errs.append(f"scan {unit}: lines missing")
            continue
        for ln in lines:
            if not isinstance(ln, dict):
                errs.append(f"scan {unit}: non-object line")
                continue
            if ln.get("verdict") not in ("match", "departure"):
                errs.append(f"scan {unit}: bad verdict {ln.get('verdict')!r}")
                continue
            if not ln.get("written") or not ln.get("expected"):
                errs.append(f"scan {unit}: line missing written/expected")
            if ln.get("verdict") == "departure":
                if not ln.get("slot") or not ln.get("contradicts"):
                    errs.append(f"scan {unit}: departure missing slot/contradicts")
                scan_departures.append((unit, str(ln.get("written") or "").strip()))
    deps = obj.get("departures")
    if not isinstance(deps, list):
        errs.append("departures missing")
        deps = []
    for dep in deps:
        if not isinstance(dep, dict):
            errs.append("departures: non-object entry")
    dep_pairs = [(d.get("unit"), str(d.get("written") or "").strip())
                 for d in deps if isinstance(d, dict)]
    dep_counts = Counter(dep_pairs)
    scan_counts = Counter(scan_departures)
    if dep_counts != scan_counts:
        extra = list((dep_counts - scan_counts).elements())
        missing = list((scan_counts - dep_counts).elements())
        detail = ""
        if extra:
            detail += (
                f"; departure not in scan e.g. {extra[0][0]}: "
                f"{extra[0][1][:60]!r}"
            )
        if missing:
            detail += (
                f"; scan departure unmatched e.g. {missing[0][0]}: "
                f"{missing[0][1][:60]!r}"
            )
        errs.append(
            f"departures do not mirror scan ({len(dep_pairs)} entries vs "
            f"{len(scan_departures)} scanned departures{detail})"
        )
    founded: Dict[str, List[str]] = {}
    exhibits_by_unit: Dict[str, set] = {}
    for d in deps:
        if not isinstance(d, dict):
            continue
        disp = str(d.get("disposition") or "")
        if not DISPOSITION_RE.match(disp):
            errs.append(f"{d.get('unit')}: bad disposition {disp!r}")
            continue
        if disp.split()[-1].startswith("S"):
            sid = disp.split()[-1]
            if sid not in thread_ids:
                errs.append(f"{d.get('unit')}: disposition names unknown thread {sid}")
            if disp.startswith("founds"):
                founded.setdefault(sid, []).append(d.get("unit"))
            if disp.startswith(("founds", "exhibits")):
                exhibits_by_unit.setdefault(d.get("unit"), set()).add(sid)
    for t in obj.get("threads", []):
        if not isinstance(t, dict):
            continue
        sid = t.get("id")
        places = founded.get(sid, [])
        if len(places) != 1:
            errs.append(f"{sid}: founded by {len(places)} departures (need exactly 1)")
        elif places[0] != t.get("origin"):
            errs.append(f"{sid}: founding departure at {places[0]} but origin {t.get('origin')}")
    for row in grid if isinstance(grid, list) else []:
        if not isinstance(row, dict):
            continue
        for fam in FAMILIES:
            if row.get(fam) != "P":
                continue
            src = (row.get("srcs") or {}).get(fam)
            sids = src if isinstance(src, (list, tuple)) else str(src or "").split(",")
            if not any(str(s).strip() for s in sids):
                errs.append(f"{row.get('unit')}: P {fam} has no source thread")
                continue
            for sid in (str(s).strip() for s in sids):
                if sid and sid not in exhibits_by_unit.get(row.get("unit"), set()):
                    errs.append(
                        f"{row.get('unit')}: P {fam} cites {sid} with no "
                        f"founding or exhibiting departure in this unit"
                    )
    if require_scan:
        claims: Dict[str, List[str]] = {}
        for t in obj.get("threads", []):
            if not isinstance(t, dict):
                continue
            sig = str(t.get("signature") or "")
            for m in re.findall(r"protected output\s+([0-9][\d.,]*)", sig, flags=re.I):
                claims.setdefault(m.rstrip(".,"), []).append(t.get("id"))
        for val, ids in claims.items():
            if len(ids) > 1:
                errs.append(f"protected output {val} claimed by multiple threads {ids}")
        for t in obj.get("threads", []):
            if not isinstance(t, dict):
                continue
            thread_families = {t.get("family"), t.get("origin_family")}
            if thread_families & {"wrong_operation", "steps"}:
                witness = str(t.get("witness") or "").strip()
                if not witness:
                    errs.append(f"{t.get('id')}: construction thread without witness")
                elif conversation and witness not in conversation:
                    errs.append(
                        f"{t.get('id')}: witness not verbatim in dialogue: "
                        f"{witness[:60]!r}"
                    )
            if v9 and thread_families & {"wrong_operation", "steps"}:
                witness_check = str(t.get("witness_check") or "").strip()
                if not witness_check:
                    errs.append(
                        f"{t.get('id')}: construction thread without witness_check"
                    )
            if v8 and "principles" in thread_families:
                grounds = str(t.get("grounds") or "").strip()
                if not grounds:
                    errs.append(f"{t.get('id')}: principles thread without grounds")
                elif conversation and grounds not in conversation:
                    errs.append(
                        f"{t.get('id')}: grounds not verbatim in dialogue: "
                        f"{grounds[:60]!r}"
                    )

        if v8:
            thread_by_id = {
                t.get("id"): t
                for t in obj.get("threads", [])
                if isinstance(t, dict)
            }
            for row in grid if isinstance(grid, list) else []:
                if not isinstance(row, dict):
                    continue
                for fam in FAMILIES:
                    if row.get(fam) not in ("P", "A"):
                        continue
                    src = (row.get("srcs") or {}).get(fam)
                    sids = (
                        src
                        if isinstance(src, (list, tuple))
                        else str(src or "").split(",")
                    )
                    for sid in (str(value).strip() for value in sids):
                        thread = thread_by_id.get(sid)
                        cited_family = (
                            _thread_family_at(thread, row.get("unit"), units)
                            if thread
                            else None
                        )
                        if sid and cited_family and cited_family != fam:
                            errs.append(
                                f"{row.get('unit')}: {fam} cites {sid} "
                                f"of family {cited_family}"
                            )
                if conversation:
                    for fam, quote in (row.get("quotes") or {}).items():
                        if quote and str(quote) not in conversation:
                            errs.append(
                                f"{row.get('unit')}: quote for {fam} not verbatim: "
                                f"{str(quote)[:50]!r}"
                            )
            if conversation:
                for thread in obj.get("threads", []):
                    if not isinstance(thread, dict):
                        continue
                    quote = thread.get("quote")
                    if quote and str(quote) not in conversation:
                        errs.append(
                            f"{thread.get('id')}: thread quote not verbatim: "
                            f"{str(quote)[:50]!r}"
                        )

        for row in grid if isinstance(grid, list) else []:
            if not isinstance(row, dict):
                continue
            triggers = row.get("triggers")
            if triggers is None:
                triggers = {}
            elif not isinstance(triggers, dict):
                errs.append(f"{row.get('unit')}: triggers must be an object")
                triggers = {}

            for fam in FAMILIES:
                if row.get(fam) == "A":
                    trigger = str(triggers.get(fam) or "").strip()
                    if not trigger:
                        errs.append(f"{row.get('unit')}: A {fam} without trigger")
                    elif conversation and trigger not in conversation:
                        errs.append(
                            f"{row.get('unit')}: trigger for {fam} not verbatim in dialogue: "
                            f"{trigger[:50]!r}"
                        )
                elif fam in triggers:
                    errs.append(f"{row.get('unit')}: trigger on non-A {fam}")
    return errs


def validate(obj: dict, units: List[str], require_scan: bool = False,
             conversation: str = "", v8: bool = False,
             v9: bool = False) -> List[str]:
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
        origin_family = t.get("origin_family")
        reattributed_at = t.get("reattributed_at")
        if (origin_family is None) != (reattributed_at is None):
            errs.append(
                f"{t.get('id')}: origin_family and reattributed_at must appear together"
            )
        elif origin_family is not None:
            if origin_family not in set(FAMILIES):
                errs.append(f"{t.get('id')}: bad origin_family {origin_family}")
            if origin_family == t.get("family"):
                errs.append(
                    f"{t.get('id')}: origin_family equals final family"
                )
            if reattributed_at not in units:
                errs.append(
                    f"{t.get('id')}: bad reattributed_at {reattributed_at}"
                )
            elif t.get("origin") in units and units.index(reattributed_at) <= units.index(t.get("origin")):
                errs.append(
                    f"{t.get('id')}: reattributed_at must follow origin {t.get('origin')}"
                )
        resolved_at = t.get("resolved_at")
        if resolved_at:
            row = next((r for r in grid if r.get("unit") == resolved_at), None)
            resolved_family = _thread_family_at(t, resolved_at, units)
            if not row or row.get(resolved_family) != "A":
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
    errs.extend(
        _validate_scan(
            obj, units, grid, thread_ids, require_scan, conversation, v8, v9
        )
    )
    return errs


# ---------------------------------------------------------------------------
# The LLM call
# ---------------------------------------------------------------------------

def llm_call(model_slug: str, messages: List[dict],
             provider: Optional[str] = None,
             reasoning_effort: Optional[str] = None,
             reasoning_enabled: Optional[bool] = None) -> Tuple[str, str, dict]:
    """One OpenRouter chat completion against the given slug (e.g.
    'moonshotai/kimi-k3'). Returns (content, reasoning_trace, meta) where
    meta carries latency, usage, and OpenRouter's accounted cost. ``provider``
    pins the call to one named provider (spelled as on the OpenRouter model
    page); None falls back to PROVIDER_ORDER, and free routing if that is
    also unset. ``reasoning_effort`` sets OpenRouter's reasoning effort
    (including "low", "medium", "high", "xhigh", and "max" where the model
    supports them). For models that expose reasoning but no effort selector,
    ``reasoning_enabled=True`` explicitly enables model-managed reasoning.
    The two controls are mutually exclusive; when both are None, no reasoning
    field is sent and the provider default remains in force."""
    if reasoning_effort is not None and reasoning_enabled is not None:
        raise ValueError(
            "set reasoning_effort or reasoning_enabled, not both"
        )
    reasoning = (
        {"effort": reasoning_effort}
        if reasoning_effort is not None
        else ({"enabled": reasoning_enabled}
              if reasoning_enabled is not None else None)
    )
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
            **({"reasoning": reasoning} if reasoning is not None else {}),
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
                        reasoning_effort: Optional[str] = None,
                        reasoning_enabled: Optional[bool] = None) -> str:
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
    optionally overrides the model's reasoning effort for this call.
    ``reasoning_enabled`` supports models whose reasoning can be enabled but
    whose effort cannot be selected. The record stores both controls.
    Prompts in SCAN_PROMPTS are validated against the scan invariants as
    well; membership is by prompt name.
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
        "reasoning_enabled": reasoning_enabled,
        "dialogue_id": did,
        "split": split,
        "attempts": [],
        "valid": False,
        "annotation": None,
        "cost_usd": 0.0,
        "latency_s": 0.0,
    }
    try:
        text, reasoning, meta = llm_call(
            model_slug, messages, provider, reasoning_effort,
            reasoning_enabled,
        )
    except Exception as exc:  # noqa: BLE001 (transport layer; recorded, not retried)
        record["attempts"].append({"transport_error": str(exc)})
        json.dump(record, open(cache_path(model_slug, prompt_name, did, split), "w"), indent=1)
        return "invalid"
    record["cost_usd"] = meta["cost_usd"]
    record["latency_s"] = meta["latency_s"]
    try:
        obj = extract_json(text)
        errs = validate(
            obj, units, require_scan=(prompt_name in SCAN_PROMPTS),
            conversation=dialogue["conversation"],
            v8=(prompt_name in V8_PROMPTS),
            v9=(prompt_name in V9_PROMPTS),
        )
    except Exception as exc:  # noqa: BLE001 (model output layer)
        obj, errs = None, [f"parse: {exc}"]
    record["attempts"].append({"raw": text[-20000:], "reasoning": reasoning,
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
    reasoning_enabled: Optional[bool] = None,
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
                        provider, reasoning_effort, reasoning_enabled):
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
