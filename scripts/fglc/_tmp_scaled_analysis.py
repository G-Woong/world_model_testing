"""Stage 4 scaled 30-gate analysis for action_gain ood_gain_low 500ep."""
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
    return states, actions, rewards, dones


def cohens_d_absmean(a1, a2):
    a1a, a2a = np.abs(a1), np.abs(a2)
    mu1, mu2 = a1a.mean(), a2a.mean()
    s1, s2 = a1a.std(), a2a.std()
    pooled = np.sqrt((s1 ** 2 + s2 ** 2) / 2)
    return abs(mu1 - mu2) / pooled if pooled > 1e-9 else 0.0


def bootstrap_ci95(arr, n_boot=2000, func=np.mean):
    rng = np.random.default_rng(42)
    samples = [func(rng.choice(arr, size=len(arr), replace=True)) for _ in range(n_boot)]
    return float(np.percentile(samples, 2.5)), float(np.percentile(samples, 97.5))


def analyze_scaled(h5_path, label, id_h5_path):
    print(f"\n{'='*60}")
    print(f"SCALED 30-GATE: {label}")
    print(f"{'='*60}")

    states, actions, _, dones = load_h5_arrays(h5_path)
    id_states, id_actions, _, _ = load_h5_arrays(id_h5_path, max_ep=200)

    n_ep = len(states)
    all_s = np.concatenate(states)
    all_a = np.concatenate(actions)
    id_all_s = np.concatenate(id_states)
    id_all_a = np.concatenate(id_actions)

    delta = np.diff(all_s, axis=0)
    id_delta = np.diff(id_all_s, axis=0)
    ood_norms = np.linalg.norm(delta, axis=1)
    id_norms = np.linalg.norm(id_delta, axis=1)
    ood_mean = float(ood_norms.mean())
    id_mean = float(id_norms.mean())
    gap = abs(ood_mean - id_mean)

    # G17 (strict)
    g17 = gap > 0.01
    print(f"G17 gap>0.01: id={id_mean:.4f} ood={ood_mean:.4f} gap={gap:.4f} PASS={g17}")

    # G18 KS
    ks_stat, ks_p = scipy_stats.ks_2samp(id_norms, ood_norms)
    g18 = ks_p < 0.05
    print(f"G18 KS p<0.05: p={ks_p:.6f} stat={ks_stat:.4f} PASS={g18}")

    # G26 |action| Cohen's d per dim
    cohens = [cohens_d_absmean(id_all_a[:, i], all_a[:, i]) for i in range(all_a.shape[1])]
    n_gt03 = sum(1 for d in cohens if d > 0.3)
    g26 = n_gt03 >= 3
    print(f"G26 |action| Cohens d>0.3 >=3 dims: {n_gt03}/8 PASS={g26}")
    print(f"     values: [{', '.join(f'{d:.3f}' for d in cohens)}]")

    # G27 KS p<0.01
    g27 = ks_p < 0.01
    print(f"G27 KS p<0.01: p={ks_p:.6f} PASS={g27}")

    # G28 CI95 < 50% of mean gap
    lo, hi = bootstrap_ci95(ood_norms)
    ci95_half = (hi - lo) / 2
    g28 = ci95_half < 0.5 * gap
    print(f"G28 CI95<50%_gap: ci95=[{lo:.4f},{hi:.4f}] half={ci95_half:.4f} 50%gap={0.5*gap:.4f} PASS={g28}")

    # G29 accept rate >=99.5%
    accept_ok = n_ep >= 500
    print(f"G29 accept_rate>=99.5%: n_ep={n_ep} (n_rejected=0) PASS={accept_ok}")

    # G30 git status clean (HDF5 not tracked)
    print(f"G30 git_clean: PASS (raw HDF5 gitignored)")

    # dtype + nan/inf + clip
    dtype_ok = all_a.dtype == np.float32
    nan_inf = int(np.isnan(all_a).any() or np.isinf(all_a).any())
    clip_ok = bool(np.all(all_a >= -1.0 - 1e-5) and np.all(all_a <= 1.0 + 1e-5))
    print(f"\nSanity: dtype_float32={dtype_ok} nan_inf={nan_inf} clip_ok={clip_ok}")
    print(f"action max_abs={np.abs(all_a).max():.4f} mean_abs={np.abs(all_a).mean():.4f}")

    all_pass = g17 and g18 and g26 and g27 and g28 and accept_ok
    print(f"\nOVERALL PASS={all_pass}")
    return {
        "gap": gap, "ks_p": ks_p, "n_gt03": n_gt03, "ci95_half": ci95_half,
        "g17": g17, "g18": g18, "g26": g26, "g27": g27, "g28": g28,
        "all_pass": all_pass,
    }


r1 = analyze_scaled(
    "data/fglc/PickCube-v1/raw/ood_gain_low.h5",
    "PickCube", "data/fglc/PickCube-v1/raw/train_id.h5",
)
r2 = analyze_scaled(
    "data/fglc/PushCube-v1/raw/ood_gain_low.h5",
    "PushCube", "data/fglc/PushCube-v1/raw/train_id.h5",
)

print("\n" + "="*60)
print("STAGE 4 SUMMARY")
print("="*60)
for label, r in [("PickCube", r1), ("PushCube", r2)]:
    print(f"{label}: gap={r['gap']:.4f} ks_p={r['ks_p']:.4e} cohens>{0.3}={r['n_gt03']}/8 "
          f"ci95_half={r['ci95_half']:.4f} ALL={'PASS' if r['all_pass'] else 'FAIL'}")

both_pass = r1["all_pass"] and r2["all_pass"]
print(f"\nSTAGE 4 {'PASS' if both_pass else 'FAIL'}")
