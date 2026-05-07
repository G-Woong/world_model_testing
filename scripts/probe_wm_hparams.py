"""OOM-safe hyperparameter probe for WM training.

본 스크립트는 ``wm_medium`` (또는 임의 wm_config) 모델을 현재 GPU에서 forward+backward 
가능한 batch / chunk / grad_accum / precision 조합으로 짧게 시도한다.

핵심 원칙:
    - 각 후보당 ``--max-probe-steps`` (기본 3) optimizer step 이하로만 실행한다.
    - CUDA OOM 발생 시 해당 후보를 실패로 기록하고 다음 후보로 넘어간다.
    - full training은 절대 실행하지 않는다.
    - 결과를 outputs/wm_hparam_probe/ 아래 JSON / CSV / yaml로 저장한다.
"""
from __future__ import annotations

import argparse
import csv
import gc
import json
import sys
import time
import traceback
from contextlib import nullcontext
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
from torch.utils.data import DataLoader

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from falsifiable_regime_world_model.wm import (   # noqa: E402
    RSSMWorldModel,
    WMConfig,
    WMDataConfig,
    build_chunk_dataset,
    build_source_indices,
    collate_chunks,
    compute_total_loss,
    pick_precision,
    collect_env_report,
)


@dataclass
class ProbeCandidate:
    chunk_len: int
    batch_size: int
    grad_accum_steps: int
    precision: str   # "bf16" | "fp16" | "fp32"

    @property
    def effective_batch(self) -> int:
        return self.batch_size * self.grad_accum_steps


@dataclass
class ProbeResult:
    candidate: ProbeCandidate
    success: bool
    error: Optional[str] = None
    step_time_sec: float = 0.0
    loss_finite: bool = False
    grad_finite: bool = False
    vram_peak_bytes: int = 0
    vram_total_bytes: int = 0
    vram_ratio: float = 0.0
    last_loss: float = 0.0
    last_grad_norm: float = 0.0


def autocast_ctx(precision: str, device: torch.device):
    if device.type != "cuda" or precision == "fp32":
        return nullcontext()
    if precision == "bf16":
        return torch.amp.autocast("cuda", dtype=torch.bfloat16)
    if precision == "fp16":
        return torch.amp.autocast("cuda", dtype=torch.float16)
    return nullcontext()


def run_one_probe(
    candidate: ProbeCandidate,
    *,
    wm_cfg: WMConfig,
    data_cfg_path: str,
    variant: str,
    max_steps: int,
    device: torch.device,
) -> ProbeResult:
    result = ProbeResult(candidate=candidate, success=False)
    if device.type == "cuda":
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()

    # data
    data_cfg = WMDataConfig.from_yaml(data_cfg_path)
    data_cfg.train.chunk_len = candidate.chunk_len
    data_cfg.train.batch_size = candidate.batch_size
    data_cfg.train.num_workers = 0
    sources = build_source_indices(data_cfg)
    ds = build_chunk_dataset(data_cfg, "train", epoch=0, sources=sources)
    loader = DataLoader(
        ds, batch_size=candidate.batch_size, num_workers=0,
        collate_fn=collate_chunks, drop_last=False,
    )
    loader_iter = iter(loader)

    # model + optim
    cfg_with_variant = wm_cfg.apply_variant(variant)
    model = RSSMWorldModel(cfg_with_variant).to(device)
    optim = torch.optim.AdamW(model.parameters(), lr=3e-4)
    scaler = torch.amp.GradScaler("cuda") if (candidate.precision == "fp16" and device.type == "cuda") else None

    try:
        t0 = time.time()
        for step in range(max_steps):
            optim.zero_grad(set_to_none=True)
            for accum_idx in range(candidate.grad_accum_steps):
                batch = next(loader_iter)
                inputs = {k: v.to(device, non_blocking=True) for k, v in batch["inputs"].items()}
                targets = {k: v.to(device, non_blocking=True) for k, v in batch["targets"].items()}
                sw = batch["sample_weight"].to(device, non_blocking=True)
                with autocast_ctx(candidate.precision, device):
                    out = model(inputs)
                    loss_out = compute_total_loss(
                        out, targets, cfg_with_variant.loss, sample_weight=sw,
                    )
                loss = loss_out.total / candidate.grad_accum_steps
                if scaler is not None:
                    scaler.scale(loss).backward()
                else:
                    loss.backward()
                last_loss = float(loss_out.total.detach().item())
            if scaler is not None:
                scaler.unscale_(optim)
            grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=100.0)
            grad_finite = bool(torch.isfinite(grad_norm).item()) if torch.is_tensor(grad_norm) else True
            if scaler is not None:
                scaler.step(optim)
                scaler.update()
            else:
                optim.step()
        elapsed = (time.time() - t0) / max(1, max_steps)

        result.success = True
        result.step_time_sec = float(elapsed)
        result.loss_finite = (last_loss == last_loss) and abs(last_loss) < float("inf")
        result.grad_finite = bool(grad_finite)
        result.last_loss = float(last_loss)
        result.last_grad_norm = float(grad_norm.item()) if torch.is_tensor(grad_norm) else float(grad_norm)
    except torch.cuda.OutOfMemoryError as exc:
        result.error = f"OOM: {exc}"
    except RuntimeError as exc:
        msg = str(exc)
        # CUDA OOM이 RuntimeError로 보고될 수 있음
        if "out of memory" in msg.lower():
            result.error = f"OOM: {exc}"
        else:
            result.error = f"RuntimeError: {exc}"
    except Exception as exc:    # noqa: BLE001
        result.error = f"{type(exc).__name__}: {exc}"
    finally:
        if device.type == "cuda":
            try:
                result.vram_peak_bytes = int(torch.cuda.max_memory_reserved())
                result.vram_total_bytes = int(torch.cuda.get_device_properties(device).total_memory)
                result.vram_ratio = result.vram_peak_bytes / max(1, result.vram_total_bytes)
            except Exception:    # noqa: BLE001
                pass
        del model, optim, loader, loader_iter, ds
        gc.collect()
        if device.type == "cuda":
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
    return result


def default_candidate_grid(precision: str) -> List[ProbeCandidate]:
    """후보 grid. 작은 것부터 시도하여 OOM이 나면 다음 더 큰 candidate를 try."""
    out: List[ProbeCandidate] = []
    for chunk_len in (64, 128):
        for batch_size in (4, 8, 16, 32):
            for grad_accum in (1, 2, 4):
                out.append(ProbeCandidate(
                    chunk_len=chunk_len,
                    batch_size=batch_size,
                    grad_accum_steps=grad_accum,
                    precision=precision,
                ))
    return out


def pick_recommended(results: List[ProbeResult]) -> Optional[ProbeResult]:
    """추천 기준 (Session 9 §5):
       1) success + loss/grad finite
       2) vram_ratio < 0.90
       3) chunk_len=128 우선
       4) effective_batch 큰 쪽 우선
       5) step_time 안정 (낮은 쪽)
    """
    feasible = [r for r in results
                if r.success and r.loss_finite and r.grad_finite and r.vram_ratio < 0.90]
    if not feasible:
        # cap을 풀어 vram_ratio < 0.95까지 허용
        feasible = [r for r in results
                    if r.success and r.loss_finite and r.grad_finite and r.vram_ratio < 0.95]
    if not feasible:
        return None
    feasible.sort(key=lambda r: (
        -r.candidate.chunk_len,
        -r.candidate.effective_batch,
        r.step_time_sec,
        r.vram_ratio,
    ))
    return feasible[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="WM hyperparameter probe (OOM-safe).")
    parser.add_argument("--wm-config", type=str, required=True)
    parser.add_argument("--data-config", type=str, required=True)
    parser.add_argument("--out-dir", type=str, default="outputs/wm_hparam_probe")
    parser.add_argument("--variant", type=str, default="full_model")
    parser.add_argument("--max-probe-steps", type=int, default=3)
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--precision", type=str, default="auto",
                        help="auto | bf16 | fp16 | fp32. probe는 단일 precision으로 한다.")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    env = collect_env_report()
    device = torch.device("cuda" if (args.device in ("auto", "cuda") and env.gpu.available) else "cpu")
    precision = pick_precision(env.gpu, args.precision)
    print(f"[probe] device={device}  precision={precision}")
    print(f"[probe] wm_config={args.wm_config}  data_config={args.data_config}  variant={args.variant}")

    wm_cfg = WMConfig.from_yaml(args.wm_config)
    candidates = default_candidate_grid(precision)
    print(f"[probe] candidates: {len(candidates)} (chunk × batch × accum × {precision})")

    results: List[ProbeResult] = []
    for i, c in enumerate(candidates):
        print(f"\n[probe {i+1}/{len(candidates)}] "
              f"chunk={c.chunk_len} batch={c.batch_size} accum={c.grad_accum_steps} "
              f"precision={c.precision} eff_batch={c.effective_batch}")
        try:
            r = run_one_probe(
                c, wm_cfg=wm_cfg, data_cfg_path=args.data_config,
                variant=args.variant, max_steps=int(args.max_probe_steps),
                device=device,
            )
        except Exception as exc:    # noqa: BLE001
            r = ProbeResult(candidate=c, success=False, error=f"{type(exc).__name__}: {exc}")
        results.append(r)
        if r.success:
            print(f"   -> OK  step_time={r.step_time_sec:.3f}s  "
                  f"vram={r.vram_ratio:.0%}  loss={r.last_loss:.3f}  grad={r.last_grad_norm:.2f}")
        else:
            print(f"   -> FAIL  err={r.error}")

    # Save CSV
    csv_path = out_dir / "probe_results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp)
        writer.writerow([
            "chunk_len", "batch_size", "grad_accum_steps", "precision",
            "effective_batch", "success", "error",
            "step_time_sec", "loss_finite", "grad_finite",
            "vram_peak_bytes", "vram_total_bytes", "vram_ratio",
            "last_loss", "last_grad_norm",
        ])
        for r in results:
            c = r.candidate
            writer.writerow([
                c.chunk_len, c.batch_size, c.grad_accum_steps, c.precision,
                c.effective_batch, r.success, r.error or "",
                f"{r.step_time_sec:.4f}", r.loss_finite, r.grad_finite,
                r.vram_peak_bytes, r.vram_total_bytes, f"{r.vram_ratio:.4f}",
                f"{r.last_loss:.6f}", f"{r.last_grad_norm:.4f}",
            ])

    json_path = out_dir / "probe_results.json"
    with json_path.open("w", encoding="utf-8") as fp:
        json.dump({
            "device": str(device),
            "precision": precision,
            "wm_config": args.wm_config,
            "data_config": args.data_config,
            "variant": args.variant,
            "candidates": [asdict(r) for r in results],
        }, fp, indent=2, default=str)

    # Recommended
    rec = pick_recommended(results)
    rec_yaml = out_dir / "recommended_train_config.yaml"
    if rec is None:
        print("\n[probe] WARNING: no feasible candidate found.")
        rec_payload = {
            "note": "No feasible candidate. Use configs/wm_train_medium_safe.yaml as fallback.",
        }
    else:
        c = rec.candidate
        rec_payload = {
            "_note": "probe_wm_hparams.py 추천. 사용자가 본 값을 wm_train_medium_local.yaml에 반영.",
            "chunk_len": c.chunk_len,
            "batch_size": c.batch_size,
            "grad_accum_steps": c.grad_accum_steps,
            "precision": c.precision,
            "effective_batch": c.effective_batch,
            "step_time_sec": rec.step_time_sec,
            "vram_ratio": rec.vram_ratio,
            "wm_config": args.wm_config,
            "data_config": args.data_config,
            "variant": args.variant,
        }
        print(f"\n[probe] recommended: chunk={c.chunk_len} batch={c.batch_size} "
              f"accum={c.grad_accum_steps} precision={c.precision} "
              f"eff_batch={c.effective_batch} vram={rec.vram_ratio:.0%}")
    import yaml
    rec_yaml.write_text(yaml.safe_dump(rec_payload, sort_keys=False), encoding="utf-8")

    # Markdown report
    md_path = _REPO_ROOT / "docs" / "WM_HPARAM_PROBE_REPORT.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    _write_md_report(md_path, results, rec, env=env)

    print(f"\n[probe] wrote {csv_path}")
    print(f"        {json_path}")
    print(f"        {rec_yaml}")
    print(f"        {md_path}")
    return 0


def _write_md_report(path: Path, results: List[ProbeResult], rec: Optional[ProbeResult], *, env) -> None:
    lines: List[str] = []
    lines.append("# WM Hyperparameter Probe Report\n")
    if env.gpu.available:
        g = env.gpu
        lines.append(f"- GPU: {g.device_name} ({g.total_memory_bytes / 1024**3:.1f} GB)\n")
        lines.append(f"- bf16 supported: {g.bf16_supported}, fp16: {g.fp16_supported}\n")
    else:
        lines.append("- GPU: not available (CPU probe)\n")
    lines.append("")
    if rec is not None:
        c = rec.candidate
        lines.append("## Recommended\n")
        lines.append(
            f"- chunk_len={c.chunk_len}, batch_size={c.batch_size}, "
            f"grad_accum_steps={c.grad_accum_steps}, precision={c.precision}, "
            f"effective_batch={c.effective_batch}, vram_ratio={rec.vram_ratio:.0%}, "
            f"step_time={rec.step_time_sec:.3f}s\n"
        )
    else:
        lines.append("## Recommended\n- 후보 모두 실패. wm_train_medium_safe.yaml 사용 권장.\n")
    lines.append("\n## All candidates\n\n")
    lines.append("| chunk | batch | accum | precision | eff_batch | success | step_time (s) | vram | last_loss | error |\n")
    lines.append("|---:|---:|---:|---|---:|:-:|---:|---:|---:|---|\n")
    for r in results:
        c = r.candidate
        lines.append(
            f"| {c.chunk_len} | {c.batch_size} | {c.grad_accum_steps} | {c.precision} | "
            f"{c.effective_batch} | {'OK' if r.success else 'FAIL'} | "
            f"{r.step_time_sec:.3f} | {r.vram_ratio:.0%} | "
            f"{r.last_loss:.3f} | {r.error or ''} |\n"
        )
    path.write_text("".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
