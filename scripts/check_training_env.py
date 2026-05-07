"""Training environment check script (Session 9).

Cursor / 사용자가 실행:
    python scripts\\check_training_env.py --requirements requirements.txt --out-dir outputs\\wm_env_check

본 스크립트는 학습을 시작하기 전에 한 번 실행하여 GPU/VRAM/bf16/fp16/dependency
status를 outputs/wm_env_check에 JSON+MD로 저장한다. requirements.txt를 자동 수정하지
않는다.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import List

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from falsifiable_regime_world_model.wm.env_check import (   # noqa: E402
    CORE_DEPS,
    collect_env_report,
    write_report,
)


def _read_requirements(p: Path) -> List[str]:
    if not p.is_file():
        return []
    out: List[str] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line)
    return out


def _suggest_install(missing: List[str], requirements_path: Path) -> str:
    """requirements를 자동 수정하지 않고, 사용자가 직접 실행할 명령만 출력한다."""
    if not missing:
        return ""
    return (
        "Missing core dependencies detected. Cursor는 requirements를 자동으로 수정하지 않습니다.\n"
        f"  pip install {' '.join(missing)}\n"
        f"또는 requirements.txt 검토 후 동일 환경 재구성:\n"
        f"  pip install -r {requirements_path}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="WM training environment check.")
    parser.add_argument("--requirements", type=str, default="requirements.txt")
    parser.add_argument("--out-dir", type=str, default="outputs/wm_env_check")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    requirements_path = Path(args.requirements)

    print(f"[env-check] cwd={_REPO_ROOT}")
    print(f"[env-check] requirements={requirements_path}  out_dir={out_dir}")

    report = collect_env_report(cwd=str(_REPO_ROOT))
    json_path, md_path = write_report(report, out_dir)

    # Console summary
    print("\n=== summary ===")
    print(f" python: {report.python_version}")
    print(f" torch:  {report.torch_version}")
    if report.gpu.available:
        g = report.gpu
        print(f" GPU:    {g.device_name}  cap={g.capability}  "
              f"VRAM={g.total_memory_bytes / 1024 ** 3:.1f}GB  "
              f"bf16={g.bf16_supported}  fp16={g.fp16_supported}")
    else:
        print(" GPU:    (not available)")
    print(f" recommended_precision: {report.recommended_precision}")
    print(f" recommended_device:    {report.recommended_device}")

    print("\n core deps:")
    for d in report.deps:
        flag = "OK " if d.importable else "FAIL"
        print(f"   [{flag}] {d.name:<14s} v{d.version or '?'}"
              + (f"  err={d.error}" if d.error else ""))
    print(" optional deps:")
    for d in report.optional_deps:
        flag = "OK " if d.importable else "-- "
        print(f"   [{flag}] {d.name:<14s} {('v' + d.version) if d.version else '(not installed)'}")

    if report.warnings:
        print("\n warnings:")
        for w in report.warnings:
            print(f"   - {w}")
    if report.errors:
        print("\n errors:")
        for e in report.errors:
            print(f"   - {e}")

    # missing dep 추천
    missing = [d.name for d in report.deps if not d.importable]
    if missing:
        msg = _suggest_install(missing, requirements_path)
        print("\n" + msg)
        # docs/WM_TRAINING_ENV_REPORT.md에도 명시적으로 적어 둔다.
    # docs 사본 (사용자 친화)
    docs_path = _REPO_ROOT / "docs" / "WM_TRAINING_ENV_REPORT.md"
    docs_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(md_path, docs_path)
    print(f"\n wrote: {json_path}")
    print(f"        {md_path}")
    print(f"        {docs_path}  (docs copy)")

    return 0 if not report.errors else 1


if __name__ == "__main__":
    sys.exit(main())
