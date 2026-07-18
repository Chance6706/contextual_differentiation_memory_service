"""Committed reproduction of the v2 resolving-angle probe NEGATIVE (PT5-fixstat).

Question: is cell (2) of the v2 probe (RESOLVING_ANGLE_PROBE.md) a LATENT relational
figure, or a valence-LEXEME readback tautology?

The real stored gist vector = embed(Gist.search_text()) = f"{subject} {relation} {object}",
and relation = relation_from_valence(valence) in {"handles_well","has_trouble_with"}. So in
cell (2) (shared topics, OPPOSITE valence) every gist string differs by exactly that token:
the fixture writes the disposition into the embedded text as plain valence words.

Result (real fastembed, reproduced 2026-07-17): with the valence label present cell (2)
separates at held-out acc 1.000; STRIP the label (object only) and it collapses to 0.688,
sitting exactly on the same-distribution null's 95th percentile (0.689) -> statistically null.
The state carries no above-noise trace of disposition once the written-in label is removed.
This is the goalset tautology in a third costume (survivor==goalset -> separator==topic-axis
-> separator==valence-lexeme). See RESOLVING_ANGLE_PROBE.md sec.10; SUPERSEDED by
FORGETTING_GEOMETRY_CAPSTONE.md.

Run: python tools/eval_harness/probe_v2_strip_test.py   (product venv; ~4s; CDMS home isolated)
"""
from __future__ import annotations
import os, sys, time
os.environ["CDMS_EVAL_MODE"] = "1"
os.environ["CDMS_EMBED_BACKEND"] = "fastembed"
import numpy as np
from pathlib import Path
import tempfile

_REPO = Path(__file__).resolve().parents[2]
# src FIRST (sibling-clone editable-install shadowing; verified inert for this probe — identical
# numbers both sources, embeddings.py is identical — but pinned + asserted for provenance).
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "src"))

from cdms.config import Config
from cdms.embeddings import Embedder
from tools.eval_harness.provenance import assert_worktree_cdms

assert_worktree_cdms()

emb = Embedder(Config(home=Path(tempfile.mkdtemp(prefix="probev2-"))))
assert emb.backend == "fastembed", emb.backend
D = emb.dim

# topic sets from the real fixture (_SUBTOPICS / _DISPOSITIONS)
SHARED = {
    "auth":     ["token refresh", "oauth callback", "session cookie", "MFA enrollment"],
    "crypto":   ["key rotation", "cert pinning", "nonce reuse", "cipher upgrade"],
    "payments": ["refund flow", "idempotency key", "webhook retry", "chargeback"],
    "database": ["query planner", "index migration", "connection pool", "replication lag"],
}
OPPOSED = {
    "cache":         ["eviction policy", "cache stampede", "key sharding", "TTL tuning"],
    "scheduler":     ["cron parser", "retry backoff", "job dedup", "priority queue"],
    "notifications": ["push token", "batch digest", "quiet hours", "delivery receipt"],
    "analytics":     ["event schema", "funnel query", "cohort roll-up", "sampling bias"],
}
GOOD = ["refactored", "hardened", "optimized", "documented", "profiled"]
BAD  = ["broke", "regressed", "hotpatched", "corrupted"]
TOPICS = sorted(SHARED)

_bank = {}
def E(s: str) -> np.ndarray:
    if s not in _bank:
        _bank[s] = np.asarray(emb.embed_one(s), dtype=np.float64)
    return _bank[s]
def unit(v):
    n = np.linalg.norm(v); return v / n if n > 0 else v
def obj_of(ent, sub):           return f"{ent} {sub.split()[0]}"
def gist_searchtext(ent, sub, relation): return f"work {relation} {obj_of(ent, sub)}"
def ep_text(ent, sub, verb):    return f"work on the {ent} {sub} {verb} the {ent} {sub}"

def rep_searchtext(topicset, valence_sign, seed):
    rng = np.random.default_rng(seed)
    rel = "handles_well" if valence_sign > 0 else "has_trouble_with"
    return np.concatenate([unit(E(gist_searchtext(t, rng.choice(topicset[t]), rel))) for t in TOPICS])

def rep_searchtext_nolabel(topicset, seed):
    rng = np.random.default_rng(seed)
    return np.concatenate([unit(E(f"work {obj_of(t, rng.choice(topicset[t]))}")) for t in TOPICS])

def rep_centroid(topicset, valence_sign, seed, n_ep=10):
    rng = np.random.default_rng(seed)
    verbs = GOOD if valence_sign > 0 else BAD
    slots = []
    for t in TOPICS:
        vs = [E(ep_text(t, rng.choice(topicset[t]), rng.choice(verbs))) for _ in range(n_ep)]
        slots.append(unit(np.mean(vs, axis=0)))
    return np.concatenate(slots)

def rep_topicpole(which, seed):
    rng = np.random.default_rng(seed)
    topicset = SHARED if which == "A" else OPPOSED
    union = sorted(list(SHARED) + list(OPPOSED))
    slotmap = {t: np.zeros(D) for t in union}
    for t in topicset:
        slotmap[t] = unit(E(gist_searchtext(t, rng.choice(topicset[t]), "handles_well")))
    return np.concatenate([slotmap[t] for t in union])

def heldout(XA, XB, k=4):
    n = len(XA); iA = np.array_split(np.arange(n), k); iB = np.array_split(np.arange(n), k)
    pr, la = [], []
    for f in range(k):
        teA, teB = iA[f], iB[f]
        trA = np.setdiff1d(np.arange(n), teA); trB = np.setdiff1d(np.arange(n), teB)
        d = unit(XA[trA].mean(0) - XB[trB].mean(0)); thr = 0.5 * ((XA[trA] @ d).mean() + (XB[trB] @ d).mean())
        pr += list((XA[teA] @ d > thr).astype(int)) + list((XB[teB] @ d > thr).astype(int))
        la += [1] * len(teA) + [0] * len(teB)
    pr = np.array(pr); la = np.array(la); return float((pr == la).mean())

def perm_p(XA, XB, obs, n_perm=300, seed=42):
    rng = np.random.default_rng(seed); X = np.vstack([XA, XB]); n = len(XA); ge = 1
    for _ in range(n_perm):
        p = rng.permutation(len(X)); ge += (heldout(X[p][:n], X[p][n:]) >= obs)
    return ge / (n_perm + 1)

N = 16
def stack(fn, *a): return np.vstack([fn(*a, s) for s in range(N)])

if __name__ == "__main__":
    t0 = time.time()
    A2  = stack(rep_searchtext, SHARED,  1);  B2  = stack(rep_searchtext, SHARED, -1)
    A2n = stack(rep_searchtext_nolabel, SHARED)
    B2n = np.vstack([rep_searchtext_nolabel(SHARED, 500 + s) for s in range(N)])
    A2c = stack(rep_centroid, SHARED,  1);    B2c = stack(rep_centroid, SHARED, -1)
    A1  = stack(rep_searchtext, SHARED,  1)
    B1  = np.vstack([rep_searchtext(SHARED, 1, 900 + s) for s in range(N)])
    A3  = stack(rep_topicpole, "A");          B3  = stack(rep_topicpole, "B")

    print("=== held-out separation (mean-diff, k=4, real fastembed) ===")
    for name, XA, XB in [
        ("(2) search_text  LABEL PRESENT   ", A2,  B2),
        ("(2) LABEL STRIPPED (object only) ", A2n, B2n),
        ("(2) centroid (verbs, NO label)   ", A2c, B2c),
        ("(1) NULL (same topic same valence)", A1, B1),
        ("(3) topic tautology              ", A3,  B3),
    ]:
        acc = heldout(XA, XB)
        print(f"  {name}: acc={acc:.3f}  perm_p={perm_p(XA, XB, acc):.4f}")

    # calibrated same-distribution null band
    accs = []
    for trial in range(40):
        XA = np.vstack([rep_centroid(SHARED, 1, 40000 + trial * 100 + s) for s in range(N)])
        XB = np.vstack([rep_centroid(SHARED, 1, 50000 + trial * 100 + s) for s in range(N)])
        accs.append(heldout(XA, XB))
    accs = np.array(accs)
    print(f"=== null band (same-dist poles): mean={accs.mean():.3f} sd={accs.std():.3f} "
          f"95pct={np.percentile(accs, 95):.3f} ===")
    print(f"[elapsed {time.time()-t0:.1f}s; strip-label 0.688 sits on the null 95th-pct -> statistically null]")
