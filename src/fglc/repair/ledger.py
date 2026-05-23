"""JSON Lines ledger helpers for closed-loop repair iterations.

Source: docs/EXPERIMENT_LEDGER_SCHEMA.md (Ledger Line Schema + REQUIRED_KEYS)
"""

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from filelock import FileLock


REQUIRED_KEYS: tuple[str, ...] = (
    "loop_id",
    "iter",
    "run_id",
    "git_sha",
    "config_hash",
    "config_path",
    "phase",
    "split",
    "metrics_before",
    "metrics_after",
    "deltas",
    "failed_metric",
    "diagnosed_cause",
    "candidate_chosen",
    "result",
    "stop_condition_hit",
    "next_action",
    "wall_clock_minutes",
    "vram_peak_mib",
)

VALID_RESULTS = frozenset({"accept", "reject", "inconclusive"})
VALID_STOP_CONDITIONS = frozenset(
    {
        "max_iter",
        "wall_clock",
        "target_reached",
        "consecutive_inconclusive",
        "hook_blocked",
    }
)


class LedgerSchemaError(ValueError):
    pass


def validate_ledger_line(line: dict[str, Any]) -> None:
    missing = set(REQUIRED_KEYS) - set(line)
    if missing:
        raise LedgerSchemaError(f"missing keys: {sorted(missing)}")

    if line["result"] not in VALID_RESULTS:
        raise LedgerSchemaError(f"invalid result: {line['result']!r}")

    stop_condition = line["stop_condition_hit"]
    if stop_condition is not None and stop_condition not in VALID_STOP_CONDITIONS:
        raise LedgerSchemaError(f"invalid stop_condition_hit: {stop_condition!r}")


def compute_config_hash(config: dict[str, Any] | str | Path) -> str:
    if isinstance(config, dict):
        payload = json.dumps(config, sort_keys=True, ensure_ascii=False).encode("utf-8")
    elif isinstance(config, Path):
        payload = config.read_bytes()
    elif isinstance(config, str):
        payload = config.encode("utf-8")
    else:
        raise TypeError("config must be a dict, str, or Path")

    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def build_loop_id(now: datetime | None = None) -> str:
    if now is None:
        now = datetime.now(timezone.utc).replace(microsecond=0)
    suffix = uuid.uuid4().hex[:4]
    return f"loop_{now.strftime('%Y-%m-%dT%H-%M-%S')}-{suffix}"


def build_run_id(phase: str, descriptor: str, seed: int, key_params: dict[str, Any]) -> str:
    params_sorted = "_".join(f"{key}{value}" for key, value in sorted(key_params.items()))
    return f"{phase}_{descriptor}_seed{seed}_{params_sorted}"


def append_ledger_line(
    ledger_path: Path, line: dict[str, Any], *, lock_timeout: float = 10.0
) -> None:
    validate_ledger_line(line)
    lock_path = ledger_path.with_suffix(ledger_path.suffix + ".lock")
    with FileLock(str(lock_path), timeout=lock_timeout):
        with ledger_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False, sort_keys=True))
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
