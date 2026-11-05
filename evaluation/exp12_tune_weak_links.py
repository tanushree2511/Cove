"""Experiment 12 - Attempt B: supported weak links (algorithm change, see cove/engines/stable_cluster.py Stage 1b).

Same tuning data and the same selection rule as exp11, fixed in advance (mean of LFW-library ARI, AgeDB pair accuracy,
CFP-FP pair accuracy). CALFW / CPLFW / seed-0 libraries are NOT read. The grid keeps the v2 base settings and adds the
weak-link threshold and the number of shared neighbours required.
Output: results/exp12_tuned_config.json
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import exp11_tune_pose_age as e11  # noqa: E402
from common import load_json, save_json  # noqa: E402

base = load_json("exp10_tuned_config.json")["config"]
e11.GRID = [dict(base, link=l, weak=w, support=s)
            for l in (0.50, 0.55) for w in (0.25, 0.30, 0.35, 0.40, 0.45) for s in (2, 3, 4, 6, 8)]

if __name__ == "__main__":
    e11.main.__globals__["save_json"] = lambda name, obj: save_json("exp12_tuned_config.json", {
        **obj, "config": {**obj["config"], **{k: obj["grid"][0][k] for k in ("weak", "support")}},
        "selected_on": obj["selected_on"] + " (Attempt B: supported weak links)"})
    e11.main()
