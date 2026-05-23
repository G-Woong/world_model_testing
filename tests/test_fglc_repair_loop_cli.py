import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from scripts.fglc import repair_loop


def test_cli_smoke_improve(tmp_path, capsys):
    tmp_yaml = tmp_path / "smoke.yaml"
    tmp_yaml.write_text("phase: R3\n", encoding="utf-8")
    argv = [
        "--phase",
        "R3",
        "--config",
        str(tmp_yaml),
        "--descriptor",
        "smoke",
        "--mock-scenario",
        "improve",
        "--max-iter",
        "2",
        "--output-root",
        str(tmp_path / "out"),
    ]

    assert repair_loop.main(argv) == 0
    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == {
        "loop_id",
        "final_result",
        "stop_condition_hit",
        "ledger_path",
        "next_action",
    }
    assert Path(payload["ledger_path"]).exists()


def test_cli_invalid_phase():
    argv = ["--phase", "BAD", "--config", "x.yaml", "--descriptor", "d"]

    assert repair_loop.main(argv) == 2


def test_cli_invalid_failed_metric():
    argv = [
        "--phase",
        "R3",
        "--config",
        "x.yaml",
        "--descriptor",
        "d",
        "--failed-metric",
        "garbage_metric_xyz",
    ]

    assert repair_loop.main(argv) == 2


def test_cli_internal_exception(monkeypatch):
    def boom(cfg, *, runner):
        del cfg, runner
        raise RuntimeError("test error")

    monkeypatch.setattr(repair_loop, "run_repair_loop", boom)
    argv = ["--phase", "R3", "--config", "x.yaml", "--descriptor", "d"]

    assert repair_loop.main(argv) == 1
