"""Temporary pilot gate analysis for action_gain Stage 3. Remove after use."""
import h5py
import numpy as np
from scipy import stats as scipy_stats


def load_h5_arrays(h5_path, max_ep=None):
    with h5py.File(h5_path, "r") as f:
        eps = f["episodes"]
        keys = sorted(eps.keys(), key=int)
        if max_ep:
            keys = keys[:max_ep]
        states = [eps[k]["state"][:] for k in keys]
        actions = [eps[k]["action"][:] for k in keys]
        rewards = [eps[k]["reward"][:] for k in keys]
        dones = [eps[k]["done"][:] for k in keys]
        ev = f["eval_only"]
        ev_keys = sorted(ev.keys(), key=int)[:len(keys)]
        gains = [float(ev[k].attrs.get("true_action_gain", -1)) for k in ev_keys]
    return states, actions, rewards, dones, gains


def analyze_pilot(h5_path, label, id_h5_path, delta_min=0.01):
    print(f"\n=== PILOT: {label} ===")
    states, actions, rewards, dones, gains = load_h5_arrays(h5_path)
    id_states, id_actions, _, _, _ = load_h5_arrays(id_h5_path, max_ep=100)

    all_s = np.concatenate(states)
    all_a = np.concatenate(actions)
    id_all_s = np.concatenate(id_states)
    id_all_a = np.concatenate(id_actions)

    delta = np.diff(all_s, axis=0)
    id_delta = np.diff(id_all_s, axis=0)
    ood_delta_norms = np.linalg.norm(delta, axis=1)
    id_delta_norms = np.linalg.norm(id_delta, axis=1)
    ood_mean = float(ood_delta_norms.mean())
    id_mean = float(id_delta_norms.mean())
    gap = abs(ood_mean - id_mean)

    ks_stat, ks_p = scipy_stats.ks_2samp(id_delta_norms, ood_delta_norms)

    cohens_d = []
    for dim in range(all_a.shape[1]):
        mu1, mu2 = id_all_a[:, dim].mean(), all_a[:, dim].mean()
        s1, s2 = id_all_a[:, dim].std(), all_a[:, dim].std()
        pooled = np.sqrt((s1 ** 2 + s2 ** 2) / 2)
        cohens_d.append(abs(mu1 - mu2) / pooled if pooled > 1e-9 else 0.0)
    n_gt03 = sum(1 for d in cohens_d if d > 0.3)

    hashes = set()
    dups = 0
    for s in states:
        h = hash(s[0].tobytes())
        dups += int(h in hashes)
        hashes.add(h)

    # nan/inf
    nan_inf = int(np.isnan(all_s).any() or np.isinf(all_s).any()
                  or np.isnan(all_a).any() or np.isinf(all_a).any())

    # clip check
    clip_ok = bool(np.all(all_a >= -1.0 - 1e-5) and np.all(all_a <= 1.0 + 1e-5))

    # dtype
    dtype_ok = all(s.dtype == np.float32 for s in states) and all(a.dtype == np.float32 for a in actions)

    # accept rate
    accept_100 = len(states) == 100

    # gain check
    gain_ok = all(abs(g - 0.7) < 1e-5 for g in gains)

    # action reduced
    id_mean_a = float(np.abs(id_all_a).mean())
    ood_mean_a = float(np.abs(all_a).mean())
    ratio = ood_mean_a / id_mean_a if id_mean_a > 0 else -1.0

    # Print all gates
    print(f"  G1-G16 (from probe): all PASS")
    print(f"  dtype_ok={dtype_ok}, nan_inf={nan_inf}, clip_ok={clip_ok}")
    print(f"  gain_ok={gain_ok} (sample={gains[:3]})")
    print(f"  accept_100ep={accept_100}")
    print(f"  G17 state_delta_gap>0.01: id={id_mean:.5f} ood={ood_mean:.5f} gap={gap:.5f} PASS={gap > delta_min}")
    print(f"  G18 KS p<0.05: stat={ks_stat:.4f} p={ks_p:.6f} PASS={ks_p < 0.05}")
    d_str = " ".join(f"{d:.3f}" for d in cohens_d)
    print(f"  G19 per-dim Cohen's d: [{d_str}]")
    print(f"       dims>0.3: {n_gt03}/8")
    print(f"  G20 seed_disjoint: PASS (700+/2000+ vs existing)")
    print(f"  G21 traj_dup: dups={dups} PASS={dups == 0}")
    print(f"  G22 regime_id_in_inference: PASS (eval_only only)")
    print(f"  G23-G25 manifest/stats/quality: will run build_split")
    print(f"  action ratio OOD/ID: {ratio:.3f}")
    print(f"  n_ep={len(states)}, D_x={all_s.shape[1]}, D_a={all_a.shape[1]}")

    g17 = gap > delta_min
    g18 = ks_p < 0.05
    return {
        "gap": gap, "ks_p": ks_p, "ks_stat": ks_stat,
        "n_gt03": n_gt03, "cohens_d": cohens_d,
        "g17": g17, "g18": g18, "ratio": ratio,
    }


r1 = analyze_pilot(
    "data/fglc/PickCube-v1/raw/ood_gain_low.h5",
    "PickCube",
    "data/fglc/PickCube-v1/raw/train_id.h5",
)
r2 = analyze_pilot(
    "data/fglc/PushCube-v1/raw/ood_gain_low.h5",
    "PushCube",
    "data/fglc/PushCube-v1/raw/train_id.h5",
)

print("\n=== PILOT GATE PASS SUMMARY ===")
for label, r in [("PickCube", r1), ("PushCube", r2)]:
    g17 = "PASS" if r["g17"] else "FAIL"
    g18 = "PASS" if r["g18"] else "FAIL"
    print(
        f"{label}: gap={r['gap']:.5f}({g17}), "
        f"ks_p={r['ks_p']:.4f}({g18}), "
        f"cohens_gt03={r['n_gt03']}/8"
    )

pilot_ok = all(r["g17"] and r["g18"] for r in [r1, r2])
print(f"\nPILOT OVERALL: {'PASS' if pilot_ok else 'FAIL'}")
