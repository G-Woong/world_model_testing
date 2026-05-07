"""P1 검증 보조: smoke_p1_filtered의 split별 observed field family 분포를 출력.

각 episode_meta.json의 field_info_static[*].family를 읽어 split별로 집계하고,
allowed pool과 disjoint 검사 결과를 PASS/FAIL로 출력한다.

본 스크립트는 일회성 검증용이며 dataset/api/scheme에 영향을 주지 않는다.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Set


_FAMILY_NAME = {0: "VISIBILITY", 1: "FRICTION", 2: "INT_INTF", 3: "CTRL_INTF"}


def _collect_family_counter(split_dir: Path) -> Counter:
    counter: Counter = Counter()
    eps_dir = split_dir / "episodes"
    if not eps_dir.is_dir():
        return counter
    for meta_path in sorted(eps_dir.glob("*.meta.json")):
        try:
            with meta_path.open("r", encoding="utf-8") as fp:
                meta = json.load(fp)
        except Exception:
            continue
        for f in meta.get("field_info_static") or []:
            counter[int(f.get("family", -1))] += 1
    return counter


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python scripts/_p1_check_family_disjoint.py <root>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    if not root.is_dir():
        print(f"[ERROR] root not found: {root}", file=sys.stderr)
        return 2

    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        print(f"[ERROR] manifest.json missing: {manifest_path}", file=sys.stderr)
        return 2
    with manifest_path.open("r", encoding="utf-8") as fp:
        manifest = json.load(fp)

    factor_policy = manifest.get("factor_recomb_policy") or {}
    train_pool = set(int(x) for x in factor_policy.get("train_field_families", [0, 1, 2, 3]))
    ood_pool = set(int(x) for x in factor_policy.get("ood_field_families", []))
    train_apply_filter = bool(factor_policy.get("train_apply_family_filter", False))

    print("=" * 80)
    print("P1 train_apply_family_filter 검증 (smoke_p1_filtered)")
    print("=" * 80)
    print(f"manifest.factor_recomb_policy:")
    print(f"  train_field_families       = {sorted(train_pool)}")
    print(f"  ood_field_families         = {sorted(ood_pool)}")
    print(f"  train_apply_family_filter  = {train_apply_filter}")
    print(f"  disjoint                   = {factor_policy.get('disjoint')}")
    print()

    # P1 정책상 family pool이 강제되는 split은 4개뿐:
    #   train/valid/test_id: train_apply_filter가 true일 때만 train_pool로 강제.
    #   ood_factor_recomb : 항상 ood_pool로 강제.
    # 다른 OOD split (room_perm / param_shift / obs_shift / field_placement)는
    # family를 강제하지 않으므로 기존 invariant 유지 — 4 family 모두 등장 정상.
    all_families = set(_FAMILY_NAME.keys())
    rows: List[Dict[str, object]] = []
    expected: Dict[str, Set[int]] = {
        "train": train_pool if train_apply_filter else all_families,
        "valid": train_pool if train_apply_filter else all_families,
        "test_id": train_pool if train_apply_filter else all_families,
        "ood_factor_recomb": ood_pool,
        "ood_room_perm": all_families,
        "ood_param_shift": all_families,
        "ood_obs_shift": all_families,
        "ood_field_placement": all_families,
    }

    overall_pass = True
    for split in [
        "train", "valid", "test_id",
        "ood_room_perm", "ood_factor_recomb", "ood_param_shift",
        "ood_obs_shift", "ood_field_placement",
    ]:
        split_dir = root / split
        if not split_dir.is_dir():
            print(f"[SKIP] {split}: directory missing")
            continue
        counter = _collect_family_counter(split_dir)
        observed: Set[int] = set(counter.keys()) - {-1}
        allowed = expected.get(split, set(_FAMILY_NAME))
        outside = observed - allowed
        status = "PASS" if not outside else "FAIL"
        if status == "FAIL":
            overall_pass = False
        rows.append({
            "split": split,
            "allowed": sorted(allowed),
            "observed": sorted(observed),
            "counts": dict(sorted(counter.items())),
            "status": status,
            "outside": sorted(outside),
        })

    # table
    print(f"{'split':22}  {'allowed':14}  {'observed':14}  status  detail")
    print("-" * 100)
    for r in rows:
        allowed_str = "{" + ",".join(str(x) for x in r["allowed"]) + "}"
        observed_str = "{" + ",".join(str(x) for x in r["observed"]) + "}" if r["observed"] else "{}"
        detail = ", ".join(
            f"{_FAMILY_NAME.get(k, '?')}={v}" for k, v in r["counts"].items()
        )
        print(f"{r['split']:22}  {allowed_str:14}  {observed_str:14}  {r['status']:6}  {detail}")
    print("-" * 100)
    print(f"OVERALL: {'PASS' if overall_pass else 'FAIL'}")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
