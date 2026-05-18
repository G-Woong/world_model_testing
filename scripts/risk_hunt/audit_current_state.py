"""STEP 10 current state audit script.

Read-only audit: checks key file/directory states and emits JSON.
Does NOT modify any files.

Usage:
    python scripts/risk_hunt/audit_current_state.py
    python scripts/risk_hunt/audit_current_state.py --dry-run   # stdout only
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from datetime import datetime, timezone

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent


def _read_text(path: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return ""


def run_audit() -> dict:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # Sentinel list
    gates_dir = REPO_ROOT / "outputs" / "phase_gates"
    sentinel_list = sorted(p.name for p in gates_dir.glob("*.passed")) if gates_dir.exists() else []

    # Checkpoint inventory
    ckpt_root = REPO_ROOT / "outputs" / "checkpoints"
    pretrain_manifest = (ckpt_root / "pretrain_v0_4_long" / "manifest.json").exists()
    abl001_ckpt = (ckpt_root / "pretrain_v0_4_abl001" / "checkpoint_best.pt").exists()
    abl003_ckpt = (ckpt_root / "pretrain_v0_4_abl003" / "checkpoint_best.pt").exists()

    # v0_4 dataset manifest
    v0_4_manifest_path = REPO_ROOT / "data" / "frcgw_text" / "v0_4" / "manifest.json"
    v0_4_total = 0
    if v0_4_manifest_path.exists():
        try:
            mdata = json.loads(v0_4_manifest_path.read_text())
            v0_4_total = mdata.get("total_episodes", 0)
        except Exception:
            pass

    # Config metric checks
    long_cfg = _read_text(REPO_ROOT / "configs" / "lr_eval_real_v0_4_long.yaml")
    recovery_cfg = _read_text(REPO_ROOT / "configs" / "lr_eval_step9_c3_recovery.yaml")
    long_has_regime = "regime_shift_f1" in long_cfg
    recovery_has_regime = "regime_shift_f1" in recovery_cfg

    # frcg_agent.py: tau_f value
    frcg_agent_txt = _read_text(REPO_ROOT / "src" / "frcgw" / "evaluation" / "frcg_agent.py")
    tau_f_match = re.search(r"GateConfig\(tau_f=([\d.]+)\)", frcg_agent_txt)
    tau_f_val = tau_f_match.group(1) if tau_f_match else "not_found"
    lr_scorer_in_agent = "lr_scorer" in frcg_agent_txt

    # planner.py checks
    planner_txt = _read_text(REPO_ROOT / "src" / "frcgw" / "planning" / "planner.py")
    proxy_present = "no_state_change" in planner_txt
    state_update_called = "planner_state.update" in planner_txt

    # ablations.py: ABL-040 forced F_t
    ablations_txt = _read_text(REPO_ROOT / "src" / "frcgw" / "evaluation" / "ablations.py")
    abl040_forced = "_last_F_t = 10.0" in ablations_txt

    # Stale codex queue tasks (TASK_1098~1109)
    queue_dir = REPO_ROOT / ".agent_tasks" / "codex_queue"
    stale = 0
    if queue_dir.exists():
        for n in range(1098, 1110):
            if list(queue_dir.glob(f"TASK_{n}_*.md")):
                stale += 1

    return {
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "sentinel_list": sentinel_list,
        "pretrain_v0_4_long_manifest_exists": pretrain_manifest,
        "abl001_checkpoint_exists": abl001_ckpt,
        "abl003_checkpoint_exists": abl003_ckpt,
        "v0_4_total_episodes": v0_4_total,
        "lr_eval_long_has_regime_shift_f1": long_has_regime,
        "lr_eval_recovery_has_regime_shift_f1": recovery_has_regime,
        "tau_f_in_frcg_agent": tau_f_val,
        "no_state_change_proxy_present": proxy_present,
        "planner_state_update_called": state_update_called,
        "lr_scorer_in_frcg_agent": lr_scorer_in_agent,
        "abl040_forced_F_t_present": abl040_forced,
        "codex_queue_stale_task_count": stale,
        "last_known_leakage_count": 0,
        "last_known_fake_metric_count": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="STEP 10 current state audit")
    parser.add_argument("--dry-run", action="store_true", help="Print JSON to stdout only")
    args = parser.parse_args()

    result = run_audit()

    if args.dry_run:
        print(json.dumps(result, indent=2))
        return

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = REPO_ROOT / "outputs" / "risk_hunt" / "audits"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"current_state_audit_{ts}.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"Audit written to: {out_path}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
