"""Cohen's d analysis for action_gain: mean-based vs abs-mean-based.

gain=0.7 reduces action magnitude (variance), not mean (both ~0).
This script checks both formulations and reports which is appropriate.
"""
import h5py
import numpy as np
from scipy import stats as scipy_stats


def load_actions(h5_path, max_ep=None):
    with h5py.File(h5_path, "r") as f:
        eps = f["episodes"]
        keys = sorted(eps.keys(), key=int)
        if max_ep:
            keys = keys[:max_ep]
        return np.concatenate([eps[k]["action"][:] for k in keys])


def cohens_d_mean(a1, a2):
    """Standard Cohen's d: difference in means / pooled std."""
    mu1, mu2 = a1.mean(), a2.mean()
    s1, s2 = a1.std(), a2.std()
    pooled = np.sqrt((s1 ** 2 + s2 ** 2) / 2)
    return abs(mu1 - mu2) / pooled if pooled > 1e-9 else 0.0


def cohens_d_absmean(a1, a2):
    """Cohen's d on |a|: captures magnitude reduction."""
    a1_abs, a2_abs = np.abs(a1), np.abs(a2)
    mu1, mu2 = a1_abs.mean(), a2_abs.mean()
    s1, s2 = a1_abs.std(), a2_abs.std()
    pooled = np.sqrt((s1 ** 2 + s2 ** 2) / 2)
    return abs(mu1 - mu2) / pooled if pooled > 1e-9 else 0.0


for task, id_path, ood_path in [
    ("PickCube", "data/fglc/PickCube-v1/raw/train_id.h5",
     "data/fglc/PickCube-v1/raw/ood_gain_low.h5"),
    ("PushCube", "data/fglc/PushCube-v1/raw/train_id.h5",
     "data/fglc/PushCube-v1/raw/ood_gain_low.h5"),
]:
    print(f"\n=== {task} action Cohen's d analysis ===")
    id_a = load_actions(id_path, max_ep=100)
    ood_a = load_actions(ood_path)

    print(f"  ID  mean: {id_a.mean():.4f}  std: {id_a.std():.4f}  mean|a|: {np.abs(id_a).mean():.4f}")
    print(f"  OOD mean: {ood_a.mean():.4f}  std: {ood_a.std():.4f}  mean|a|: {np.abs(ood_a).mean():.4f}")

    print(f"\n  Per-dim Cohen's d (mean-based):")
    d_mean = [cohens_d_mean(id_a[:, i], ood_a[:, i]) for i in range(id_a.shape[1])]
    print(f"  {[f'{d:.3f}' for d in d_mean]}")
    print(f"  dims > 0.3: {sum(d > 0.3 for d in d_mean)}/8")

    print(f"\n  Per-dim Cohen's d (|action| mean-based, captures magnitude reduction):")
    d_abs = [cohens_d_absmean(id_a[:, i], ood_a[:, i]) for i in range(id_a.shape[1])]
    print(f"  {[f'{d:.3f}' for d in d_abs]}")
    print(f"  dims > 0.3: {sum(d > 0.3 for d in d_abs)}/8")

    # KS test on |action| per dim
    print(f"\n  KS test on |action| per dim (p-values):")
    ks_ps = [scipy_stats.ks_2samp(np.abs(id_a[:, i]), np.abs(ood_a[:, i])).pvalue for i in range(id_a.shape[1])]
    print(f"  {[f'{p:.4f}' for p in ks_ps]}")
    print(f"  dims with p<0.05: {sum(p < 0.05 for p in ks_ps)}/8")

    # Std ratio (captures variance reduction)
    print(f"\n  Per-dim std ratio (OOD_std/ID_std, should be ~0.7 for uniform clip):")
    std_ratios = [ood_a[:, i].std() / id_a[:, i].std() for i in range(id_a.shape[1])]
    print(f"  {[f'{r:.3f}' for r in std_ratios]}")
    print(f"  mean ratio: {np.mean(std_ratios):.3f} (expected ~0.7 * sqrt(3/4) ≈ 0.606)")
