"""Experiment 21 (E2) - two devices, different photos and different corrections: do they end with the same people?

Setting (per test library of the shared exp14 set; thresholds exp14's tuning half; nothing tuned here):
  base      50% of the faces, synced to both devices, same clustering on both.
  device A  receives 25% more faces (its own random arrival order) and its user makes up to 5 corrections on what
            device A shows (exp15's oracle user, aimed at the biggest remaining mistake).
  device B  the same with the other 25% of faces, independently.
  sync      each device receives the other's new faces (in the sender's arrival order) and corrections.
Methods (all see the same faces and the same clicks):
  ours        state = SET of faces and corrections; the result is recomputed from the set (set semantics).
              Replicas insert faces in different random orders, so identical results are not built in.
  c-avg       constrained average linkage recomputed from the same set (batch, own implementation).
  frozen+log  Immich-style frozen labels (new face joins the person of its most similar placed face at cosine >= 0.5,
              else a new person) with each correction applied as an edit of the labels, and the other device's edits
              replayed in the order received (the standard way to combine edit logs without set semantics).
Pre-declared pass: ours gives identical people on 100% of libraries; if no alternative differs, report that.
Outcome per method: share of libraries where both replicas end with the identical partition, minimum and mean ARI
between replicas, F1 of the replicas against truth, share of ALL corrections (both devices') held in each replica.
Run: COVE_FACE_MODEL=mbf|edgeface_s python evaluation/exp21_replica_convergence.py
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import exp19_correction_baselines as E  # noqa: E402
from adaptive import run_adaptive  # noqa: E402
from common import save_json  # noqa: E402
from exp1_cluster import evaluate  # noqa: E402
from sklearn.metrics import adjusted_rand_score  # noqa: E402

THR = 0.5
MAXK = 5
METHODS = ("ours", "c-avg", "frozen+log")


def canon(lab):
    seen, out = {}, np.empty(len(lab), dtype=int)
    for i, v in enumerate(lab.tolist()):
        out[i] = seen.setdefault(v, len(seen))
    return out


def frozen_insert(lab, placed, ids, Xu):
    """Immich-style: each new face (in the given order) takes the person of its most similar placed face if the
    cosine is >= THR, else starts a new person."""
    nxt = lab.max() + 1
    for i in ids:
        s = Xu[placed] @ Xu[i]
        j = int(np.argmax(s))
        if s[j] >= THR:
            lab[i] = lab[placed[j]]
        else:
            lab[i] = nxt
            nxt += 1
        placed.append(i)


def apply_op(lab, op, Xu):
    """A correction applied as an edit of the stored labels."""
    kind, a, b = op
    if kind == "must":
        lab[lab == lab[b]] = lab[a]
    elif lab[a] == lab[b]:
        idx = np.where(lab == lab[a])[0]
        side_b = idx[(Xu[idx] @ Xu[b]) > (Xu[idx] @ Xu[a])]
        lab[side_b] = lab.max() + 1


def user_session(method, Xl, Nl, yl):
    """Up to MAXK corrections by the oracle user on what this device shows (indices local to this device)."""
    cons = []
    lab = E.run(method, Xl, Nl, cons)
    for _ in range(MAXK):
        c = E.pick_correction(lab, yl, Xl, set(cons))
        if c is None:
            break
        cons.append(c)
        lab = E.run(method, Xl, Nl, cons)
    return cons


def _job(key):
    sl = E._D["sl"][key]
    X, N, y = np.asarray(E._D["X"][sl]), E._D["N"][sl], E._D["y"][sl]
    n = len(X)
    seed = int(key.split("|")[2])
    r = np.random.RandomState(seed + 21000)
    perm = r.permutation(n)
    nb, na = int(round(0.5 * n)), int(round(0.25 * n))
    base, A, B = perm[:nb], perm[nb:nb + na], perm[nb + na:]
    Xu = X / np.linalg.norm(X, axis=1, keepdims=True)
    out = {"faces": n}
    for method in METHODS:
        mr = np.random.RandomState(seed + 21100)
        # ---- each device works alone ------------------------------------------------------------------
        ops, locs = {}, {}
        for dev, new in (("A", A), ("B", B)):
            loc = np.concatenate([base, mr.permutation(new)])     # local arrival order
            locs[dev] = loc
            if method == "frozen+log":
                lab = np.full(n, -1)
                lb = E.ours(X[base], N[base], ())
                lab[base] = lb
                placed = list(base)
                frozen_insert(lab, placed, [i for i in loc[len(base):]], Xu)
                cons, done = [], set()
                for _ in range(MAXK):                                  # same oracle user, on this device's labels
                    c = E.pick_correction(lab[loc], y[loc], X[loc], done)
                    if c is None:
                        break
                    done.add(c)
                    kind, a, b = c
                    op = (kind, int(loc[a]), int(loc[b]))
                    cons.append(op)
                    apply_op(lab, op, Xu)
                ops[dev] = (cons, lab, placed)
            else:
                cl = user_session(method, X[loc], N[loc], y[loc])
                ops[dev] = [(k, int(loc[a]), int(loc[b])) for k, a, b in cl]
        # ---- sync -------------------------------------------------------------------------------------
        finals = {}
        if method == "frozen+log":
            for dev, other, onew in (("A", "B", B), ("B", "A", A)):
                cons, lab, placed = ops[dev]
                lab = lab.copy()
                placed = list(placed)
                recv = [i for i in locs[other][len(base):]]
                frozen_insert(lab, placed, recv, Xu)
                for op in ops[other][0]:                                # replay the other device's edits
                    apply_op(lab, op, Xu)
                finals[dev] = lab
            allcons = ops["A"][0] + ops["B"][0]
        else:
            allcons = ops["A"] + ops["B"]
            for dev in ("A", "B"):
                order = np.concatenate([mr.permutation(base), mr.permutation(A if dev == "A" else B),
                                        mr.permutation(B if dev == "A" else A)])
                finals[dev] = E.run(method, X, N, allcons, order=order)
        la, lb_ = finals["A"], finals["B"]
        out[method] = {"identical": bool(np.array_equal(canon(la), canon(lb_))),
                       "ari_between": float(adjusted_rand_score(la, lb_)),
                       "F1_A": evaluate(la, y)["B3_F1"], "F1_B": evaluate(lb_, y)["B3_F1"],
                       "n_cons": len(allcons), "held_A": E.held(la, allcons), "held_B": E.held(lb_, allcons)}
    return key, out


def main():
    t0 = time.time()
    keys = [k for k in np.load(E.SHARED + ".npz")["keys"].tolist() if k.startswith("test|")]
    if len(sys.argv) > 1:
        keys = keys[:int(sys.argv[1])]
    rows = dict(run_adaptive(_job, keys, initializer=E._init, name="REPLICAS", per_step=4))
    table = {}
    for m in METHODS:
        v = [r[m] for r in rows.values()]
        nc = sum(x["n_cons"] for x in v)
        table[m] = {"libraries": len(v), "identical_share": float(np.mean([x["identical"] for x in v])),
                    "identical_count": int(sum(x["identical"] for x in v)),
                    "min_ari_between": float(min(x["ari_between"] for x in v)),
                    "mean_ari_between": float(np.mean([x["ari_between"] for x in v])),
                    "F1": float(np.mean([(x["F1_A"] + x["F1_B"]) / 2 for x in v])),
                    "F1_gap_between_replicas": float(np.mean([abs(x["F1_A"] - x["F1_B"]) for x in v])),
                    "held_share_both_devices": (sum(x["held_A"] + x["held_B"] for x in v) / (2 * nc)) if nc else None,
                    "corrections": nc}
        print(m, {k: round(a, 4) if isinstance(a, float) else a for k, a in table[m].items()}, flush=True)
    if len(sys.argv) > 1:
        return
    save_json(f"exp21_replicas_{E.MODEL}.json", {"model": E.MODEL, "protocol": __doc__, "table": table,
                                                 "per_library": rows, "seconds": time.time() - t0})
    print(f"DONE in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
