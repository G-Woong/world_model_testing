"""Training environment / dependency / GPU probe utility.

본 모듈은 학습 시작 전에 환경을 한 번 점검하고, 그 결과를 dataclass로 노출한다.
- python / torch / cuda / GPU name / VRAM / bf16 / fp16 AMP 가능 여부
- 필수 / 선택 dependency import 가능 여부
- 권장 precision (auto-pick: bf16 → fp16 → fp32)

본 모듈은 어떠한 학습도 수행하지 않으며, hard-coded mutation도 하지 않는다.
PART0 §3 §4 (config 없이 hard-coded 수치 박기 금지)와 정합.
"""
from __future__ import annotations

import importlib
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# 1. 핵심 / 선택 dependency 목록
# =============================================================================


CORE_DEPS: Tuple[str, ...] = (
    "torch",
    "numpy",
    "yaml",
    "tqdm",
    "pandas",
    "matplotlib",
)

OPTIONAL_DEPS: Tuple[str, ...] = (
    "tensorboard",
    "wandb",
)


# =============================================================================
# 2. dataclass results
# =============================================================================


@dataclass
class DepStatus:
    name: str
    importable: bool
    version: Optional[str] = None
    error: Optional[str] = None


@dataclass
class GPUStatus:
    available: bool
    device_count: int = 0
    device_name: Optional[str] = None
    capability: Optional[Tuple[int, int]] = None
    total_memory_bytes: int = 0
    allocated_bytes: int = 0
    reserved_bytes: int = 0
    bf16_supported: bool = False
    fp16_supported: bool = False
    cuda_runtime: Optional[str] = None
    torch_cuda_version: Optional[str] = None


@dataclass
class EnvReport:
    python_version: str
    platform: str
    hostname: str
    torch_version: str
    cwd: str
    pip_check: Optional[str]
    git_commit: Optional[str]
    deps: List[DepStatus] = field(default_factory=list)
    optional_deps: List[DepStatus] = field(default_factory=list)
    gpu: GPUStatus = field(default_factory=lambda: GPUStatus(available=False))
    recommended_precision: str = "fp32"     # bf16 | fp16 | fp32
    recommended_device: str = "cpu"         # cuda | cpu
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # tuple is non-JSON; serialize as list
        if d["gpu"]["capability"] is not None:
            d["gpu"]["capability"] = list(d["gpu"]["capability"])
        return d


# =============================================================================
# 3. dependency probe
# =============================================================================


def probe_dependency(name: str) -> DepStatus:
    """단일 module을 import 시도하고 version을 추출한다.

    yaml은 PyYAML이 설치되어 있어야 하므로 'yaml' 그대로 시도한다.
    """
    try:
        mod = importlib.import_module(name)
        version = getattr(mod, "__version__", None)
        if version is None and name == "yaml":
            # PyYAML은 yaml.__version__으로 노출
            version = getattr(mod, "__version__", "unknown")
        return DepStatus(name=name, importable=True, version=str(version) if version else None)
    except Exception as exc:   # noqa: BLE001
        return DepStatus(name=name, importable=False, error=f"{type(exc).__name__}: {exc}")


def probe_core_deps() -> List[DepStatus]:
    return [probe_dependency(n) for n in CORE_DEPS]


def probe_optional_deps() -> List[DepStatus]:
    return [probe_dependency(n) for n in OPTIONAL_DEPS]


# =============================================================================
# 4. GPU probe
# =============================================================================


def probe_gpu() -> GPUStatus:
    """torch + CUDA 환경을 점검한다. torch import 실패 시 available=False."""
    try:
        import torch  # noqa
    except Exception:
        return GPUStatus(available=False)

    if not torch.cuda.is_available():
        return GPUStatus(
            available=False,
            torch_cuda_version=getattr(torch.version, "cuda", None),
        )

    dev = torch.device("cuda:0")
    name = torch.cuda.get_device_name(dev)
    cap = torch.cuda.get_device_capability(dev)
    props = torch.cuda.get_device_properties(dev)
    total = int(props.total_memory)
    alloc = int(torch.cuda.memory_allocated(dev))
    reserved = int(torch.cuda.memory_reserved(dev))
    bf16_ok = bool(torch.cuda.is_bf16_supported()) if hasattr(torch.cuda, "is_bf16_supported") else (cap[0] >= 8)
    # fp16 (autocast) — Pascal(6.0) 이상에서 일반적으로 가능, 더 구체적으론 cap >= (6,0).
    fp16_ok = bool(cap[0] >= 6)

    return GPUStatus(
        available=True,
        device_count=int(torch.cuda.device_count()),
        device_name=str(name),
        capability=(int(cap[0]), int(cap[1])),
        total_memory_bytes=total,
        allocated_bytes=alloc,
        reserved_bytes=reserved,
        bf16_supported=bf16_ok,
        fp16_supported=fp16_ok,
        cuda_runtime=getattr(torch.version, "cuda", None),
        torch_cuda_version=getattr(torch.version, "cuda", None),
    )


# =============================================================================
# 5. precision auto-pick
# =============================================================================


def pick_precision(gpu: GPUStatus, requested: str = "auto") -> str:
    """학습 precision을 결정한다.

    requested ∈ {"auto", "bf16", "fp16", "fp32"}.
    auto:
        - GPU가 bf16을 지원하면 bf16
        - 아니면 fp16 AMP
        - 그것도 안 되면 fp32
    auto가 아니지만 GPU가 미지원이면 fp32로 fallback (warning).
    """
    requested = (requested or "auto").lower()
    if requested not in ("auto", "bf16", "fp16", "fp32"):
        raise ValueError(f"unknown precision request: {requested!r}")

    if not gpu.available:
        return "fp32"
    if requested == "auto":
        if gpu.bf16_supported:
            return "bf16"
        if gpu.fp16_supported:
            return "fp16"
        return "fp32"
    if requested == "bf16":
        return "bf16" if gpu.bf16_supported else "fp32"
    if requested == "fp16":
        return "fp16" if gpu.fp16_supported else "fp32"
    return "fp32"


# =============================================================================
# 6. helpers
# =============================================================================


def safe_pip_check() -> Optional[str]:
    """`python -m pip check` 실행 결과를 반환. 실패 시 None."""
    py = sys.executable
    try:
        r = subprocess.run(
            [py, "-m", "pip", "check"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        return (r.stdout + ("\n" + r.stderr if r.stderr else "")).strip()
    except Exception:   # noqa: BLE001
        return None


def safe_git_commit(cwd: str) -> Optional[str]:
    """현재 commit hash. git이 없거나 repo가 아니면 None."""
    if shutil.which("git") is None:
        return None
    try:
        r = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5, check=False,
        )
        if r.returncode == 0:
            return r.stdout.strip() or None
    except Exception:   # noqa: BLE001
        return None
    return None


def collect_env_report(*, cwd: Optional[str] = None) -> EnvReport:
    cwd = cwd or os.getcwd()
    deps = probe_core_deps()
    opt_deps = probe_optional_deps()
    gpu = probe_gpu()
    precision = pick_precision(gpu, requested="auto")
    device = "cuda" if gpu.available else "cpu"
    warnings: List[str] = []
    errors: List[str] = []

    # ---- core dep 체크 ----
    missing = [d.name for d in deps if not d.importable]
    if missing:
        errors.append(f"core dependencies missing: {missing}")
    # ---- GPU 체크 ----
    if not gpu.available:
        warnings.append(
            "CUDA GPU not available. Full WM training on CPU is strongly discouraged "
            "(expected ~50× slower). Use --device cpu only for sanity smoke."
        )
    elif gpu.total_memory_bytes < 6 * 1024 ** 3:
        warnings.append(
            f"GPU VRAM is small ({gpu.total_memory_bytes / 1024 ** 3:.1f} GB). "
            "Use configs/wm_train_medium_safe.yaml or run probe_wm_hparams.py first."
        )

    import torch  # for version
    return EnvReport(
        python_version=platform.python_version(),
        platform=platform.platform(),
        hostname=socket.gethostname(),
        torch_version=torch.__version__,
        cwd=cwd,
        pip_check=safe_pip_check(),
        git_commit=safe_git_commit(cwd),
        deps=deps,
        optional_deps=opt_deps,
        gpu=gpu,
        recommended_precision=precision,
        recommended_device=device,
        warnings=warnings,
        errors=errors,
    )


def write_report(report: EnvReport, out_dir: Path) -> Tuple[Path, Path]:
    """JSON과 MD 두 파일로 저장한다.

    - <out_dir>/env_report.json
    - <out_dir>/env_report.md
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "env_report.json"
    md_path = out_dir / "env_report.md"

    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    md_path.write_text(_format_markdown(report), encoding="utf-8")
    return json_path, md_path


def _format_markdown(r: EnvReport) -> str:
    """사람이 보기 편한 markdown 요약."""
    lines: List[str] = []
    lines.append("# WM Training Environment Report")
    lines.append("")
    lines.append(f"- python: {r.python_version}")
    lines.append(f"- platform: {r.platform}")
    lines.append(f"- hostname: {r.hostname}")
    lines.append(f"- cwd: {r.cwd}")
    lines.append(f"- torch: {r.torch_version}")
    lines.append(f"- git_commit: {r.git_commit}")
    lines.append("")
    lines.append("## GPU")
    g = r.gpu
    if not g.available:
        lines.append("- **CUDA GPU not detected.** training이 가능은 하지만 매우 느릴 것이며, "
                     "본 논문 main 결과는 CPU에서 보고하지 않는다.")
    else:
        lines.append(f"- device_count: {g.device_count}")
        lines.append(f"- device: {g.device_name}")
        lines.append(f"- capability: {g.capability}")
        lines.append(f"- total VRAM: {g.total_memory_bytes / 1024 ** 3:.2f} GB")
        lines.append(f"- allocated: {g.allocated_bytes / 1024 ** 2:.1f} MB")
        lines.append(f"- reserved:  {g.reserved_bytes / 1024 ** 2:.1f} MB")
        lines.append(f"- bf16 supported: {g.bf16_supported}")
        lines.append(f"- fp16 (AMP) supported: {g.fp16_supported}")
        lines.append(f"- CUDA runtime: {g.cuda_runtime}")
    lines.append("")
    lines.append(f"- **recommended_precision (auto):** `{r.recommended_precision}`")
    lines.append(f"- **recommended_device:** `{r.recommended_device}`")
    lines.append("")

    lines.append("## Core dependencies")
    for d in r.deps:
        flag = "OK " if d.importable else "FAIL"
        ver = d.version or "?"
        err = f"  error={d.error}" if d.error else ""
        lines.append(f"- [{flag}] {d.name:<14s} v{ver}{err}")
    lines.append("")
    lines.append("## Optional dependencies")
    for d in r.optional_deps:
        flag = "OK " if d.importable else "-- "
        ver = d.version or ""
        lines.append(f"- [{flag}] {d.name:<14s} {('v' + ver) if ver else '(not installed)'}")
    lines.append("")
    lines.append("## pip check")
    lines.append("```")
    lines.append(r.pip_check or "(skipped or unavailable)")
    lines.append("```")
    lines.append("")
    if r.warnings:
        lines.append("## Warnings")
        for w in r.warnings:
            lines.append(f"- {w}")
        lines.append("")
    if r.errors:
        lines.append("## Errors")
        for e in r.errors:
            lines.append(f"- {e}")
        lines.append("")
    return "\n".join(lines) + "\n"


__all__ = [
    "CORE_DEPS",
    "OPTIONAL_DEPS",
    "DepStatus",
    "GPUStatus",
    "EnvReport",
    "probe_dependency",
    "probe_core_deps",
    "probe_optional_deps",
    "probe_gpu",
    "pick_precision",
    "safe_pip_check",
    "safe_git_commit",
    "collect_env_report",
    "write_report",
]
