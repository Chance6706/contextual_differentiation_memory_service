#!/bin/bash
# MULTIPLICITY-CONSERVATION ladder (CONSERVATION_PREREG.md §9): SIX fresh caches in one epoch —
# p2 (paraphrase mini-bank, temp=0), p1_s11/p1_s12/p1_s13 (triple @ temp=0.7, seeded),
# p3 (renamed tokens), p4 (permuted tie-order). NO fresh temp-0 triple baseline: the committed
# frame_triple epoch is the paired anchor (byte-determinism, PREREG §1).
# PRECONDITION: P0 has completed locally and the band is recorded in CONSERVATION_PREREG §9.
# mech-11 + distill, model-OUTER. GIRAFFE gate + mech-11 completeness abort + arm-aware layout asserts.
set -u
cd ~/cdms || exit 1
PY=.venv/bin/python
export CDMS_EMBED_BACKEND=hash
DETAIL="$HOME/cdms_conservation.detail"; GATE="$HOME/cdms_conservation.gate"
: > "$DETAIL"; : > "$GATE"
log(){ echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$DETAIL"; }

GRANITE8="granite-3.0-8b-q8 granite-3.1-8b-q8 granite-3.2-8b-q8 granite-3.3-8b-q8"
GRANITE2="granite-3.0-2b-q8 granite-3.1-2b-q8 granite-3.2-2b-q8 granite-3.3-2b-q8"
MISTRAL="mistral-g-v0.1 mistral-g-v0.2 mistral-g-v0.3"
MECH11="$GRANITE8 $GRANITE2 $MISTRAL"
DISTILL="qwen3.5-9b-base-q8 claude-opus-distill-q8 claude-code-q8 claude-fable-q8 claude-mythos-q8"
ALL="$MECH11 $DISTILL"

NB=$($PY -c "import sys; sys.path.insert(0,'tools'); import probes_sp_expansion as p; print(len(p.PROBES_SP_EXP))" 2>/dev/null)
log "--- sp-expansion bank facets: $NB (expect 31) ---"
[ "$NB" = "31" ] || { log "FATAL: sp bank $NB != 31 (stale push?)"; exit 3; }
NC=$($PY -c "import sys; sys.path.insert(0,'tools'); import probes_conservation as p; print(len(p.PROBES_CONSERVATION), min(len(v) for v in p.REPHRASINGS_CONSERVATION.values()))" 2>/dev/null)
log "--- conservation mini-bank: $NC (expect '7 3') ---"
[ "$NC" = "7 3" ] || { log "FATAL: conservation bank '$NC' != '7 3' (stale push?)"; exit 3; }
# Arm-aware layout asserts on THIS host (tie-order defense): triple T1@378; renamed CT1@378 with NO
# old token surviving; permuted T1@650 with PERMUTED_ORDER[0] token @378; all byte-lengths equal.
POSOK=$($PY - <<'PYEOF' 2>/dev/null
import sys, tempfile
from pathlib import Path
sys.path.insert(0, 'tools'); sys.path.insert(0, 'src')
import os; os.environ.setdefault('CDMS_EMBED_BACKEND', 'hash')
import redteam_claude_md_interference as R
ok = True
def build(setup):
    with tempfile.TemporaryDirectory() as td:
        return R._real_preamble_for_mode(setup, Path(td), 'v1')
p3 = build(R.setup_bem_multifact(3))
pr = build(R.setup_bem_renamed)
pp = build(R.setup_bem_permuted)
if p3.index(R.MULTIFACT_TOKENS[0]) != 378: ok = False
if pr.index(R.CONSERVATION_TOKENS[0]) != 378: ok = False
if any(t in pr for t in R.MULTIFACT_TOKENS): ok = False
if pp.index(R.MULTIFACT_TOKENS[0]) != 650: ok = False
if pp.index(R.MULTIFACT_TOKENS[R.PERMUTED_ORDER[0]]) != 378: ok = False
if not (len(p3) == len(pr) == len(pp)): ok = False
back = pr
for new, old in zip(R.CONSERVATION_TOKENS, R.MULTIFACT_TOKENS):
    back = back.replace(new, old)
if back != p3: ok = False
if sorted(pp.splitlines()) != sorted(p3.splitlines()): ok = False
print('OK' if ok else 'BAD')
PYEOF
)
[ "$POSOK" = "OK" ] || { log "FATAL: arm layout assert failed on this host (stale driver? tie-order?)"; exit 3; }
log "--- arm layouts asserted (triple/renamed/permuted) on this host ---"
# Band-provenance guard (pressure-test S2 / DEVIATION I7): generation MUST NOT start before P0 has
# fixed the band. The operator exports the band value from conservation/P0_BAND.json (local repo);
# it is echoed into this log as the sequencing receipt.
[ -n "${CDMS_CONSERVATION_BAND:-}" ] || { log "FATAL: CDMS_CONSERVATION_BAND unset — run P0 first (conservation_p0_compare.py), then export the band M from conservation/P0_BAND.json"; exit 6; }
log "--- band M=$CDMS_CONSERVATION_BAND (from P0, fixed BEFORE generation; PREREG s3/I7) ---"
if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then log "FATAL: ollama down"; exit 2; fi

giraffe_ok(){  # $1=model $2=temperature (0 or the P1 operating temp; S8: gate at BOTH conditions)
  local m="$1" t="${2:-0}" out opts
  if [ "$t" = "0" ]; then opts='{"temperature":0}'; else opts="{\"temperature\":$t,\"seed\":11}"; fi
  for _ in 1 2; do
    out=$(curl -s http://localhost:11434/api/chat -d \
      "{\"model\":\"$m\",\"stream\":false,\"options\":$opts,\"messages\":[{\"role\":\"system\",\"content\":\"The secret codeword is GIRAFFE. When the user asks for the codeword, reply with it.\"},{\"role\":\"user\",\"content\":\"What is the secret codeword?\"}]}" 2>/dev/null)
    echo "$out" | grep -qi giraffe && return 0
  done
  return 1
}

PASS=""
log "--- Stage 0: GIRAFFE gate (temp=0 AND temp=0.7; pressure-test S8 — P1 runs at 0.7) ---"
for m in $ALL; do
  if giraffe_ok "$m" 0 && giraffe_ok "$m" 0.7; then
    log "  GATE PASS  $m (both temps)"; echo "PASS $m" >> "$GATE"; PASS="$PASS $m"
  else log "  GATE FAIL  $m (EXCLUDED)"; echo "FAIL $m" >> "$GATE"; fi
done
for m in $MECH11; do
  echo " $PASS " | grep -q " $m " || { log "FATAL: mech-11 model $m gate-failed; aborting"; exit 4; }
done
log "--- mech-11 complete; passers=$PASS ---"

# Anchor byte-determinism re-verification (pressure-test M2): the design pairs P1-P4 against the
# COMMITTED frame_triple epoch on the byte-determinism argument. That was established across PAST
# epochs; an Ollama upgrade / model re-pull / driver change since then would silently confound every
# temp-0 arm with an environment delta. Regenerate a fresh temp-0 triple for 2 sentinel mech models
# into a throwaway cache and byte-diff the responses against the committed cache. Abort on mismatch.
FRAME_ANCHOR_CACHE="${FRAME_ANCHOR_CACHE:-$HOME/cdms_cache/frame_triple_20260707_191452}"
[ -d "$FRAME_ANCHOR_CACHE/ollama/expand" ] || { log "FATAL: committed anchor cache not found at $FRAME_ANCHOR_CACHE"; exit 7; }
DET_CACHE="$HOME/cdms_cache/conservation_detcheck_$(date +%Y%m%d_%H%M%S)"
for m in granite-3.0-8b-q8 mistral-g-v0.1; do
  log "--- determinism sentinel: regenerating temp-0 triple for $m ---"
  $PY tools/redteam_claude_md_interference.py --backend ollama --models "$m" \
    --modes BEM BEM_WORKSPACE_FACT --variant v1 --expand-probes --sp-expansion-bank \
    --rephrasings-per-original 1 --expand-subsample-n 31 --multifact-n 3 \
    --cache-dir "$DET_CACHE" >>"$DETAIL" 2>&1 || { log "FATAL: sentinel generation failed for $m"; exit 7; }
done
DETOK=$($PY - "$DET_CACHE/ollama/expand" "$FRAME_ANCHOR_CACHE/ollama/expand" <<'PYEOF' 2>/dev/null
import json, sys
from pathlib import Path
fresh, committed = Path(sys.argv[1]), Path(sys.argv[2])
EXPECT = 156   # 2 sentinel models x (62 BEM + 16 recall); a shortfall (e.g. an uncached empty
n = bad = miss = 0                                     # response) must fail loudly, not pass thin
for fp in fresh.glob("*.json"):
    cp = committed / fp.name
    if not cp.exists():
        miss += 1
        continue
    n += 1
    a = json.loads(fp.read_text(encoding="utf-8")).get("response")
    b = json.loads(cp.read_text(encoding="utf-8")).get("response")
    if a != b:
        bad += 1
print(f"{'OK' if (bad == 0 and miss == 0 and n == EXPECT) else 'BAD'} "
      f"compared={n}/{EXPECT} mismatched={bad} missing={miss}")
PYEOF
)
log "--- determinism sentinel result: $DETOK ---"
echo "$DETOK" | grep -q "^OK" || { log "FATAL: temp-0 byte-determinism BROKEN vs the committed anchor epoch — the paired-anchor design is invalid in this environment (Ollama/model/driver changed?). Do NOT proceed; regenerate a fresh anchor or investigate."; exit 7; }

run_arm(){  # $1 = arm tag; $2 = expected cache files per model; $3... = driver flags
  local tag="$1"; local expect="$2"; shift 2
  local TS=$(date +%Y%m%d_%H%M%S)
  local CACHE="$HOME/cdms_cache/conservation_${tag}_$TS"
  log "===== ARM $tag  cache=$CACHE  expect=$expect/model ====="
  local n=0 tot=$(echo $PASS | wc -w)
  for m in $PASS; do
    n=$((n+1)); ok=""
    for attempt in 1 2 3; do
      log "=== [$tag $n/$tot] $m attempt $attempt ==="
      if $PY tools/redteam_claude_md_interference.py --backend ollama --models "$m" \
        --modes BEM BEM_WORKSPACE_FACT --variant v1 --expand-probes \
        --expand-subsample-n 31 --cache-dir "$CACHE" "$@" \
        >>"$DETAIL" 2>&1; then ok=1; log "  ok $m"; break; fi
      log "  attempt $attempt FAIL $m; sleep 60"; sleep 60
    done
    [ -n "$ok" ] || log "  GAVE UP $m"
  done
  # Per-arm completeness assert (legituse pressure-test S8): a GIRAFFE-passing model can still
  # exhaust its 3 generation retries -> a silently-incomplete arm discovered a day later at judge
  # time. Count per-model cache files NOW; a short MECH model aborts the ladder (the arm is
  # decision-dead and everything downstream would be wasted GPU-hours); a short distill model is
  # logged loudly and the ladder continues (distill is descriptive).
  for m in $PASS; do
    local got
    got=$(ls "$CACHE/ollama/expand" 2>/dev/null | grep -c "^${m}__")
    if [ "$got" != "$expect" ]; then
      if echo " $MECH11 " | grep -q " $m "; then
        log "FATAL: mech model $m incomplete in arm $tag ($got/$expect) — aborting ladder"
        exit 5
      else
        log "WARN: distill model $m incomplete in arm $tag ($got/$expect) — continuing (descriptive cell)"
      fi
    fi
  done
  echo "$CACHE" > "$HOME/cdms_conservation_${tag}.cachedir"
  log "===== ARM $tag DONE (completeness asserted) ====="
}

# p2 first: shortest arm (60 calls/model = 28 BEM + 32 recall) = earliest full-pipeline sanity
# artifact, exercising the novel bank + reconstruction path before the 12h tail.
run_arm p2     60 --multifact-n 3 --conservation-bank --rephrasings-per-original 3
run_arm p1_s11 78 --multifact-n 3 --sp-expansion-bank --rephrasings-per-original 1 --temperature 0.7 --gen-seed 11
run_arm p1_s12 78 --multifact-n 3 --sp-expansion-bank --rephrasings-per-original 1 --temperature 0.7 --gen-seed 12
run_arm p1_s13 78 --multifact-n 3 --sp-expansion-bank --rephrasings-per-original 1 --temperature 0.7 --gen-seed 13
run_arm p3     78 --scaffold-renamed  --sp-expansion-bank --rephrasings-per-original 1
run_arm p4     78 --scaffold-permuted --sp-expansion-bank --rephrasings-per-original 1
touch "$HOME/cdms_conservation.done"
log "===== CONSERVATION (6 caches) DONE ====="
