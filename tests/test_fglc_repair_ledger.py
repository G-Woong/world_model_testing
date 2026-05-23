import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from fglc.repair.ledger import (
    REQUIRED_KEYS,
    LedgerSchemaError,
    append_ledger_line,
    build_loop_id,
    build_run_id,
    compute_config_hash,
    validate_ledger_line,
)


EXPECTED_REQUIRED_KEYS = (
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


def _minimal_line() -> dict:
    return {
        "loop_id": "loop_2026-05-23T15-00-00",
        "iter": 0,
        "run_id": "R3_smoke_seed42_K6_d32_h128",
        "git_sha": "6fcc09c",
        "config_hash": "sha256:abc123",
        "config_path": "configs/fglc/smoke_4060.yaml",
        "phase": "R3",
        "split": "PickCube/id",
        "metrics_before": {"id_nll_1step": 0.42},
        "metrics_after": {"id_nll_1step": 0.28},
        "deltas": {"id_nll_1step": -0.14},
        "failed_metric": "id_nll_1step",
        "diagnosed_cause": ["MODEL_UNDERCAPACITY"],
        "candidate_chosen": {"id": "C-014"},
        "result": "accept",
        "stop_condition_hit": None,
        "next_action": "proceed to R4 smoke",
        "wall_clock_minutes": 24,
        "vram_peak_mib": 5230,
    }


def test_required_keys_count_and_content():
    assert len(REQUIRED_KEYS) == 19
    assert REQUIRED_KEYS == EXPECTED_REQUIRED_KEYS


def test_validate_passes_on_complete_line():
    validate_ledger_line(_minimal_line())


def test_validate_raises_on_missing_key():
    line = _minimal_line()
    del line["run_id"]

    with pytest.raises(LedgerSchemaError, match="missing keys"):
        validate_ledger_line(line)


def test_validate_raises_on_invalid_result():
    line = _minimal_line()
    line["result"] = "maybe"

    with pytest.raises(LedgerSchemaError, match="invalid result"):
        validate_ledger_line(line)


def test_validate_raises_on_invalid_stop_condition():
    line = _minimal_line()
    line["stop_condition_hit"] = "forever"

    with pytest.raises(LedgerSchemaError, match="invalid stop_condition_hit"):
        validate_ledger_line(line)


def test_validate_allows_none_stop_condition():
    line = _minimal_line()
    line["stop_condition_hit"] = None

    validate_ledger_line(line)


def test_compute_config_hash_dict_deterministic():
    first = compute_config_hash({"K": 6, "d": 32})
    second = compute_config_hash({"K": 6, "d": 32})

    assert first == second
    assert first.startswith("sha256:")


def test_compute_config_hash_dict_order_invariant():
    assert compute_config_hash({"a": 1, "b": 2}) == compute_config_hash({"b": 2, "a": 1})


def test_compute_config_hash_str_and_path(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_bytes(b"K: 6\n")

    assert compute_config_hash("K: 6\n").startswith("sha256:")
    assert compute_config_hash(config_path) == compute_config_hash("K: 6\n")


def test_build_loop_id_format():
    loop_id = build_loop_id(datetime(2026, 5, 23, 15, 0, 0, tzinfo=timezone.utc))

    assert re.match(r"^loop_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}$", loop_id)
    assert loop_id == "loop_2026-05-23T15-00-00"


def test_build_run_id_format():
    assert (
        build_run_id("R3", "smoke", 42, {"K": 6, "d": 32, "h": 128})
        == "R3_smoke_seed42_K6_d32_h128"
    )


def test_append_ledger_line_round_trip(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    line = _minimal_line()

    append_ledger_line(ledger_path, line)

    assert json.loads(ledger_path.read_text(encoding="utf-8")) == line


def test_append_two_lines_yields_two_records(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    first = _minimal_line()
    second = _minimal_line()
    second["iter"] = 1
    second["result"] = "inconclusive"

    append_ledger_line(ledger_path, first)
    append_ledger_line(ledger_path, second)

    records = [
        json.loads(line)
        for line in ledger_path.read_text(encoding="utf-8").splitlines()
    ]
    assert records == [first, second]
