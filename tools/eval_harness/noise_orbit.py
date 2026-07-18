"""NOISE-ORBIT characterization — "did we ever check whether the noise itself orbits?" (Josh, 2026-07-18).

EXPLORATORY (not confirmatory; no thesis claim; HALT untouched). The program's nulls were permutations
OF THE REAL DATA — they inherit every unlabeled structure the corpus has. This run builds genuinely
STRUCTURELESS surrogate corpora and asks which "noise-floor" structures are real orbits vs artifacts.

DATA ($0): the 960 cached TOST-main eliciting deeds (cache HITS only; CostGuard cap $0.50 fails loudly
on any miss — no silent spend). Stripped with masker v3 (the confirmatory representation).

SURROGATE TIERS (classic surrogate-data method):
  W = within-deed word shuffle  (kills order/syntax/style; preserves each deed's exact bag + length)
  R = corpus bag-resample       (kills per-deed vocabulary identity; preserves length dist + pooled unigram stats)

PINNED METRICS + PREDICTIONS (committed before running):
  M1 FINGERPRINT ORBIT — same-(dispo,seed) embedding separation (mean within-pair cos − across cos) +
     nearest-neighbor same-author accuracy, per corpus. P1: REAL > W > R. If REAL ≈ W → the 0.958
     fingerprint is lexical-bag; if REAL > W → order/style carries it.
  M2 CONE ORBIT — embedding geometry per corpus: mean pairwise cos, sd, PCA participation ratio.
     P2: if R shows the same narrow cone → the 0.07 cone is embedder-intrinsic, not text-coherence.
  M3 NULL-BAND ORBIT (the headline question) — width of a balanced pseudo-label permutation band
     (200 shuffles of seed-level labels; embedding-centroid separation stat) on REAL vs R.
     P3: REAL band WIDER than R band = quantified proof our nulls inherited data structure.
  M4 BOW DISPOSITION LOSO on REAL vs R (sanity anchor: the 0.75 trace should survive REAL, die on R).
Tri-reference: R = the true structureless floor; REAL-unstripped = known-structure anchor (M2 only).

Run: python tools/eval_harness/noise_orbit.py   (~30-40 min: payload rebuild + embeds; $0)
"""
from __future__ import annotations

import json, os, re, sys, time
from itertools import combinations
from pathlib import Path

os.environ.setdefault("CDMS_EVAL_MODE", "1")
os.environ.setdefault("CDMS_EMBED_BACKEND", "fastembed")

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "src")); sys.path.insert(0, str(REPO / "tools"))

from openrouter_chat import openrouter_chat
from openrouter_cost_guard import CostGuard
import tools.eval_harness.differentiation_experiment as fixture
from tools.eval_harness.provenance import assert_worktree_cdms
from tools.eval_harness.tost_pilot import READER, reader_system
from tools.eval_harness.tost_pilot2 import build_payloads
from tools.eval_harness.tost_pilot3 import MATCHED_SUCCESS, strip_v3, bow_2afc
from tools.eval_harness.tost_main import TASKS20, SEEDS
from cdms.config import Config
from cdms.embeddings import Embedder

assert_worktree_cdms()
RNG = np.random.default_rng(20260718)


def load_deeds():
    cache = sorted((Path.home() / "cdms_cache").glob("tost_main_*"))[-1]
    guard = CostGuard(cap_usd=0.005, state_file=Path(os.environ.get("TEMP", "/tmp")) / "noise_orbit_guard2.json")
    from openrouter_cost_guard import BudgetExceededError
    old = fixture._ENTITY_SUCCESS
    try:
        fixture._ENTITY_SUCCESS = MATCHED_SUCCESS
        pay = build_payloads(40, SEEDS)
    finally:
        fixture._ENTITY_SUCCESS = old
    deeds, missed = {}, 0
    for d in ("A", "C"):
        for s in SEEDS:
            sysp = reader_system(pay[(d, s)])
            for ti, task in enumerate(TASKS20):
                try:
                    deeds[(d, s, ti)] = openrouter_chat(READER, sysp, task, cache,
                                                        n_predict=550, cost_guard=guard)
                except BudgetExceededError:
                    missed += 1   # cache miss refused BEFORE any HTTP call — zero spend
    print(f"loaded {len(deeds)} deeds, skipped {missed} misses  [guard spent ${guard._spent:.4f}]", flush=True)
    assert guard._spent < 0.001 and len(deeds) >= 850, "unexpected spend or too few deeds"
    return deeds


def words(t):
    return re.findall(r"\S+", t)


def make_surrogates(stripped):
    keys = list(stripped)
    W, R = {}, {}
    pooled = [w for k in keys for w in words(stripped[k])]
    for k in keys:
        ws = words(stripped[k])
        w2 = list(ws); RNG.shuffle(w2)
        W[k] = " ".join(w2)
        R[k] = " ".join(RNG.choice(pooled, size=len(ws), replace=True))
    return W, R


def embed_corpus(emb, corpus):
    keys = list(corpus)
    vecs = np.vstack([np.asarray(emb.embed_one(corpus[k][:4000]), np.float64) for k in keys])
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
    return keys, vecs


def fingerprint(keys, V):
    """M1: same-(dispo,seed) separation + NN same-author accuracy."""
    author = [(k[0], k[1]) for k in keys]
    S = V @ V.T
    n = len(keys)
    same, diff = [], []
    for i, j in combinations(range(n), 2):
        (same if author[i] == author[j] else diff).append(S[i, j])
    np.fill_diagonal(S, -2)
    nn_acc = float(np.mean([author[int(np.argmax(S[i]))] == author[i] for i in range(n)]))
    return dict(sep=float(np.mean(same) - np.mean(diff)), nn_acc=nn_acc,
                within=float(np.mean(same)), across=float(np.mean(diff)))


def cone(V):
    S = V @ V.T
    iu = np.triu_indices(len(V), 1)
    lam = np.linalg.eigvalsh(np.cov(V.T))
    lam = lam[lam > 0]
    return dict(mean_cos=float(S[iu].mean()), sd_cos=float(S[iu].std()),
                participation_ratio=float(lam.sum() ** 2 / (lam ** 2).sum()))


def null_band(keys, V, n_shuf=200):
    """M3: seed-level balanced pseudo-label permutation band of centroid separation."""
    seeds_list = sorted({(k[0], k[1]) for k in keys})
    idx_by = {a: [i for i, k in enumerate(keys) if (k[0], k[1]) == a] for a in seeds_list}
    stats = []
    for _ in range(n_shuf):
        perm = RNG.permutation(len(seeds_list))
        g1 = [seeds_list[i] for i in perm[: len(seeds_list) // 2]]
        i1 = [i for a in g1 for i in idx_by[a]]
        i2 = [i for a in seeds_list if a not in g1 for i in idx_by[a]]
        c1, c2 = V[i1].mean(0), V[i2].mean(0)
        stats.append(float(np.dot(c1, c2) / (np.linalg.norm(c1) * np.linalg.norm(c2))))
    stats = np.array(stats)
    return dict(band_mean=float(stats.mean()), band_sd=float(stats.std()),
                band_width90=float(np.quantile(stats, 0.95) - np.quantile(stats, 0.05)))


def main():
    t0 = time.time()
    deeds = load_deeds()
    stripped = {k: strip_v3(v) for k, v in deeds.items()}
    W, R = make_surrogates(stripped)
    base = Path(os.environ.get("TEMP", "/tmp")) / "noise_orbit_emb"
    emb = Embedder(Config(home=base))
    out = {}
    for name, corpus in [("REAL", stripped), ("W_shuffle", W), ("R_resample", R),
                         ("REAL_unstripped", deeds)]:
        keys, V = embed_corpus(emb, corpus)
        res = dict(fingerprint=fingerprint(keys, V), cone=cone(V))
        if name in ("REAL", "R_resample"):
            res["null_band"] = null_band(keys, V)
        out[name] = res
        print(f"[{time.time()-t0:.0f}s] {name}: {json.dumps(res)}", flush=True)
    # M4: BOW disposition LOSO anchor on REAL vs R
    items = [(ti, SEEDS[k % 24], SEEDS[(k + 5) % 24]) for ti in range(20) for k in (0, 8)]
    out["bow_loso"] = dict(
        REAL=bow_2afc(stripped, items, lambda s, t, ti, sa, sc: s not in (sa, sc)),
        R_resample=bow_2afc(R, items, lambda s, t, ti, sa, sc: s not in (sa, sc)))
    print("M4 bow_loso:", out["bow_loso"], flush=True)
    dst = REPO / "docs/validation/eval_harness/noise_orbit_metrics.json"
    dst.write_text(json.dumps(out, indent=1))
    print(f"[total {time.time()-t0:.0f}s] -> {dst}")


if __name__ == "__main__":
    main()
