"""Analysis script: compare detection scores for R4 easy-looking OOD."""
import math
import sys
import torch
import yaml

sys.path.insert(0, "src")

from fglc.data.dataloader import make_dataloaders
from fglc.evaluation.metrics import Evaluator
from fglc.falsification.conformal import fit_threshold
from fglc.falsification.gate import auroc_from_scores
from fglc.training import TrainerConfig, TrainerR3

config = yaml.safe_load(open("configs/fglc/r4_falsification_pickcube.yaml", encoding="utf-8"))
config["device"] = "cuda"

tc = TrainerConfig(batch_size=16, train_horizon=8, epochs=0, device="cuda")
trainer = TrainerR3(config["model"], tc)
trainer.load_state("outputs/r4_falsification/pickcube_30ep/r3_model.pt", freeze=True)

dataloaders = make_dataloaders(config)
ev = Evaluator(trainer)

data = {}
for s in ["test_id", "ood_friction", "ood_gain", "ood_mass"]:
    if s in dataloaders:
        data[s] = ev.evaluate_residuals(dataloaders[s])

tau = fit_threshold(data["test_id"]["F_total"], alpha=0.05)
print(f"tau = {tau:.4f}")
print()

F_id = data["test_id"]["F_total"]
nll_id = data["test_id"]["raw_nll_step"]
dbs_id = data["test_id"]["directional_bias_step"]

for ood_key in ["ood_friction", "ood_gain"]:
    if ood_key not in data:
        continue
    F_ood = data[ood_key]["F_total"]
    nll_ood = data[ood_key]["raw_nll_step"]
    dbs_ood = data[ood_key]["directional_bias_step"]

    print(f"=== {ood_key} ===")
    print(f"  mean F_id={float(F_id.mean()):.2f}  mean F_ood={float(F_ood.mean()):.2f}")
    print(f"  std  F_id={float(F_id.std()):.2f}   std  F_ood={float(F_ood.std()):.2f}")
    mean_diff = float(F_id.mean()) - float(F_ood.mean())
    pooled_std = math.sqrt(0.5 * (float(F_id.std()) ** 2 + float(F_ood.std()) ** 2))
    d_prime = mean_diff / pooled_std if pooled_std > 0 else 0
    auroc_theory = 0.5 + 0.5 * math.erf(d_prime / (2 ** 0.5))
    print(f"  d_prime={d_prime:.3f}  theoretical_max_AUROC={auroc_theory:.4f}")
    print()

    a_f = auroc_from_scores(F_id, F_ood)
    a_inv = auroc_from_scores(tau - F_id, tau - F_ood)
    a_dbs = auroc_from_scores(dbs_id, dbs_ood)
    a_nll = auroc_from_scores(nll_id, nll_ood)

    print(f"  AUROC(F_total):          {a_f:.4f}")
    print(f"  AUROC(tau-F, inverted):  {a_inv:.4f}")
    print(f"  AUROC(directional_bias): {a_dbs:.4f}")
    print(f"  AUROC(raw_nll):          {a_nll:.4f}")
    print()
