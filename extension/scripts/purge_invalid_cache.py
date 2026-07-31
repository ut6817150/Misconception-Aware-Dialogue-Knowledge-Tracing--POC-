"""Delete invalid records from the extraction cache so they re-run fresh.

Scans every JSON under extension/artifacts/extraction_cache/ (all splits,
models, and prompts), reports each record's status, and deletes the ones
that are not valid: records whose "valid" flag is false (failed validation,
transport errors, generation cutoffs) and files that cannot be parsed as
JSON at all (interrupted writes). Valid records are never touched.

Deleting an invalid record is safe by design: the runner treats a missing
file exactly like an invalid one (both re-fire on the next run), so the only
effect is a cleaner cache. The forensic content of invalid records (traces,
errors, usage) is lost on deletion; if a record is still awaiting diagnosis,
run with --dry-run first and copy it aside.

Usage, from the repo root:
    python extension/scripts/purge_invalid_cache.py --dry-run   # report only
    python extension/scripts/purge_invalid_cache.py             # delete
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

CACHE_DIR = Path("extension/artifacts/extraction_cache")


def scan(cache_dir: Path):
    """Yield (path, status) for every JSON file in the cache tree.

    Status is 'valid', 'invalid', or 'unreadable'.
    """
    for path in sorted(cache_dir.rglob("*.json")):
        try:
            record = json.load(open(path))
        except Exception:  # noqa: BLE001 (corrupt or interrupted write)
            yield path, "unreadable"
            continue
        yield path, ("valid" if record.get("valid") else "invalid")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would be deleted without deleting")
    parser.add_argument("--cache-dir", default=str(CACHE_DIR),
                        help=f"cache root to scan (default: {CACHE_DIR})")
    args = parser.parse_args()

    cache_dir = Path(args.cache_dir)
    if not cache_dir.exists():
        raise SystemExit(f"{cache_dir} does not exist; run from the repo root")

    counts = {"valid": 0, "invalid": 0, "unreadable": 0}
    to_delete = []
    for path, status in scan(cache_dir):
        counts[status] += 1
        if status != "valid":
            to_delete.append((path, status))
            print(f"  {status:10s} {path.relative_to(cache_dir)}")

    print(f"\nscanned {sum(counts.values())} records: "
          f"{counts['valid']} valid, {counts['invalid']} invalid, "
          f"{counts['unreadable']} unreadable")

    if not to_delete:
        print("nothing to delete")
        return
    if args.dry_run:
        print(f"dry run: {len(to_delete)} files would be deleted")
        return
    for path, _status in to_delete:
        path.unlink()
    print(f"deleted {len(to_delete)} files; they will re-run on the next sweep")


if __name__ == "__main__":
    main()
