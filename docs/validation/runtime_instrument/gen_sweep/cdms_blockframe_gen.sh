#!/bin/bash
# BLOCK-frame decomposition + RECALL grid (BLOCK_PREREG.md / RECALL_PREREG.md): ONE epoch —
# arm b (filler @ --variant v2b), arm c (frozen -D worldblock fixture), then 5 recall-only cells.
# Arm A is the COMMITTED frame_filler epoch (NOT regenerated) — validated by the determinism
# sentinel below. mech-11 + distill, model-OUTER.
set -u
cd ~/cdms || exit 1
PY=.venv/bin/python
export CDMS_EMBED_BACKEND=hash
DETAIL="$HOME/cdms_blockframe.detail"; GATE="$HOME/cdms_blockframe.gate"
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
# Fixture presence + LOCKED sha (BLOCK_PREREG s9; normalized-newline content hash).
FIXOK=$($PY - <<'PYEOF' 2>/dev/null
import hashlib
t = open("docs/validation/runtime_instrument/blockframe/worldblock_fixture.txt", encoding="utf-8").read()
h = hashlib.sha256(t.replace("\r\n", "\n").encode()).hexdigest()
print("OK" if h == "8b54c73994d6a9fa5a8c96c43ec792cf093b6e67fd76d0f30b763be36657b830" else f"BAD {h}")
PYEOF
)
log "--- worldblock fixture sha: $FIXOK ---"
echo "$FIXOK" | grep -q "^OK" || { log "FATAL: fixture missing/modified on this host"; exit 3; }
# Arm layout asserts on THIS host: v1 filler T1@378 (anchor layout), v2b filler T1@486 +
# third-person header, permuted T1@650.
POSOK=$($PY - <<'PYEOF' 2>/dev/null
import sys, tempfile
from pathlib import Path
sys.path.insert(0, 'tools'); sys.path.insert(0, 'src')
import os; os.environ.setdefault('CDMS_EMBED_BACKEND', 'hash')
import redteam_claude_md_interference as R
ok = True
def build(setup, variant="v1"):
    with tempfile.TemporaryDirectory() as td:
        return R._real_preamble_for_mode(setup, Path(td), variant)
f1 = build(R.setup_bem_filler)
f2 = build(R.setup_bem_filler, "v2b")
pp = build(R.setup_bem_permuted)
if f1.index(R.MULTIFACT_TOKENS[0]) != 378: ok = False
if f2.index(R.MULTIFACT_TOKENS[0]) != 486: ok = False
if "NOT about you" not in f2: ok = False
if "What I've learned about this workspace/user" in f2: ok = False
if pp.index(R.MULTIFACT_TOKENS[0]) != 650: ok = False
print('OK' if ok else 'BAD')
PYEOF
)
[ "$POSOK" = "OK" ] || { log "FATAL: arm layout assert failed on this host"; exit 3; }
log "--- arm layouts asserted (v1 filler / v2b filler / permuted) on this host ---"
if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then log "FATAL: ollama down"; exit 2; fi

giraffe_ok(){  # $1=model $2=temperature
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
log "--- Stage 0: GIRAFFE gate (temp=0 AND temp=0.7 — recall grid has 0.7 cells) ---"
for m in $ALL; do
  if giraffe_ok "$m" 0 && giraffe_ok "$m" 0.7; then
    log "  GATE PASS  $m"; echo "PASS $m" >> "$GATE"; PASS="$PASS $m"
  else log "  GATE FAIL  $m (EXCLUDED)"; echo "FAIL $m" >> "$GATE"; fi
done
for m in $MECH11; do
  echo " $PASS " | grep -q " $m " || { log "FATAL: mech-11 model $m gate-failed; aborting"; exit 4; }
done
log "--- mech-11 complete; passers=$PASS ---"

# Anchor determinism sentinel (BLOCK_PREREG s2/s4): arm A is the COMMITTED frame_filler epoch;
# regenerate 2 sentinel mech models' filler arm at temp 0 and byte-diff vs the committed cache.
FILLER_ANCHOR_CACHE="${FILLER_ANCHOR_CACHE:-$HOME/cdms_cache/frame_filler_20260707_113512}"
[ -d "$FILLER_ANCHOR_CACHE/ollama/expand" ] || { log "FATAL: committed filler anchor cache not found at $FILLER_ANCHOR_CACHE"; exit 7; }
DET_CACHE="$HOME/cdms_cache/blockframe_detcheck_$(date +%Y%m%d_%H%M%S)"
for m in granite-3.0-8b-q8 mistral-g-v0.1; do
  log "--- determinism sentinel: regenerating temp-0 filler for $m ---"
  $PY tools/redteam_claude_md_interference.py --backend ollama --models "$m" \
    --modes BEM BEM_WORKSPACE_FACT --variant v1 --expand-probes --sp-expansion-bank \
    --rephrasings-per-original 1 --expand-subsample-n 31 --scaffold-filler \
    --cache-dir "$DET_CACHE" >>"$DETAIL" 2>&1 || { log "FATAL: sentinel generation failed for $m"; exit 7; }
done
DETOK=$($PY - "$DET_CACHE/ollama/expand" "$FILLER_ANCHOR_CACHE/ollama/expand" <<'PYEOF' 2>/dev/null
import json, sys
from pathlib import Path
fresh, committed = Path(sys.argv[1]), Path(sys.argv[2])
EXPECT = 156
n = bad = miss = 0
for fp in fresh.glob("*.json"):
    cp = committed / fp.name
    if not cp.exists():
        miss += 1
        continue
    n += 1
    if json.loads(fp.read_text(encoding="utf-8")).get("response") != \
       json.loads(cp.read_text(encoding="utf-8")).get("response"):
        bad += 1
print(f"{'OK' if (bad == 0 and miss == 0 and n == EXPECT) else 'BAD'} "
      f"compared={n}/{EXPECT} mismatched={bad} missing={miss}")
PYEOF
)
log "--- determinism sentinel result: $DETOK ---"
echo "$DETOK" | grep -q "^OK" || { log "FATAL: byte-determinism BROKEN vs the committed filler anchor — do NOT proceed"; exit 7; }

run_arm(){  # $1 = arm tag; $2 = expected cache files per model; $3... = driver flags
  local tag="$1"; local expect="$2"; shift 2
  local TS=$(date +%Y%m%d_%H%M%S)
  local CACHE="$HOME/cdms_cache/blockframe_${tag}_$TS"
  log "===== ARM $tag  cache=$CACHE  expect=$expect/model ====="
  local n=0 tot=$(echo $PASS | wc -w)
  for m in $PASS; do
    n=$((n+1)); ok=""
    for attempt in 1 2 3; do
      log "=== [$tag $n/$tot] $m attempt $attempt ==="
      if $PY tools/redteam_claude_md_interference.py --backend ollama --models "$m" \
        --expand-probes --expand-subsample-n 31 --cache-dir "$CACHE" "$@" \
        >>"$DETAIL" 2>&1; then ok=1; log "  ok $m"; break; fi
      log "  attempt $attempt FAIL $m; sleep 60"; sleep 60
    done
    [ -n "$ok" ] || log "  GAVE UP $m"
  done
  for m in $PASS; do
    local got
    got=$(ls "$CACHE/ollama/expand" 2>/dev/null | grep -c "^${m}__")
    if [ "$got" != "$expect" ]; then
      if echo " $MECH11 " | grep -q " $m "; then
        log "FATAL: mech model $m incomplete in arm $tag ($got/$expect) — aborting"
        exit 5
      else
        log "WARN: distill model $m incomplete in arm $tag ($got/$expect) — continuing"
      fi
    fi
  done
  echo "$CACHE" > "$HOME/cdms_blockframe_${tag}.cachedir"
  log "===== ARM $tag DONE (completeness asserted) ====="
}

# BLOCK arms (78/model: 62 BEM + 16 recall)
run_arm b 78 --modes BEM BEM_WORKSPACE_FACT --variant v2b --scaffold-filler \
             --sp-expansion-bank --rephrasings-per-original 1
run_arm c 78 --modes BEM BEM_WORKSPACE_FACT --variant v1 --scaffold-worldblock \
             --sp-expansion-bank --rephrasings-per-original 1
# RECALL grid (32/model: recall-only at cap 3)
run_arm r_t0  32 --modes BEM_WORKSPACE_FACT --variant v1 --multifact-n 3 --rephrasings-per-original 3
run_arm r_s11 32 --modes BEM_WORKSPACE_FACT --variant v1 --multifact-n 3 --rephrasings-per-original 3 --temperature 0.7 --gen-seed 11
run_arm r_s12 32 --modes BEM_WORKSPACE_FACT --variant v1 --multifact-n 3 --rephrasings-per-original 3 --temperature 0.7 --gen-seed 12
run_arm r_s13 32 --modes BEM_WORKSPACE_FACT --variant v1 --multifact-n 3 --rephrasings-per-original 3 --temperature 0.7 --gen-seed 13
run_arm r_perm 32 --modes BEM_WORKSPACE_FACT --variant v1 --scaffold-permuted --rephrasings-per-original 3
touch "$HOME/cdms_blockframe.done"
log "===== BLOCKFRAME + RECALL (7 caches) DONE ====="
