#!/bin/bash
# POWERED FILLER control (FILLER_PREREG.md §8): THREE arms all FRESH in one epoch on the SP-OPEN EXPANSION
# bank (31 facets, 62 BEM variants) — single (--multifact-n 1), triple (--multifact-n 3), filler
# (--scaffold-filler). mech-11 + distill, temp=0, model-OUTER. GIRAFFE gate + mech-11 completeness abort.
set -u
cd ~/cdms || exit 1
PY=.venv/bin/python
export CDMS_EMBED_BACKEND=hash
DETAIL="$HOME/cdms_filler.detail"; GATE="$HOME/cdms_filler.gate"
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
[ "$NB" = "31" ] || { log "FATAL: bank $NB != 31 (stale push?)"; exit 3; }
if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then log "FATAL: ollama down"; exit 2; fi

giraffe_ok(){
  local m="$1" out
  for _ in 1 2; do
    out=$(curl -s http://localhost:11434/api/chat -d \
      "{\"model\":\"$m\",\"stream\":false,\"options\":{\"temperature\":0},\"messages\":[{\"role\":\"system\",\"content\":\"The secret codeword is GIRAFFE. When the user asks for the codeword, reply with it.\"},{\"role\":\"user\",\"content\":\"What is the secret codeword?\"}]}" 2>/dev/null)
    echo "$out" | grep -qi giraffe && return 0
  done
  return 1
}

PASS=""
log "--- Stage 0: GIRAFFE gate ---"
for m in $ALL; do
  if giraffe_ok "$m"; then log "  GATE PASS  $m"; echo "PASS $m" >> "$GATE"; PASS="$PASS $m"
  else log "  GATE FAIL  $m (EXCLUDED)"; echo "FAIL $m" >> "$GATE"; fi
done
for m in $MECH11; do
  echo " $PASS " | grep -q " $m " || { log "FATAL: mech-11 model $m gate-failed; aborting"; exit 4; }
done
log "--- mech-11 complete; passers=$PASS ---"

run_arm(){  # $1 = arm tag (single/triple/filler); $2... = driver scaffold flags
  local tag="$1"; shift
  local TS=$(date +%Y%m%d_%H%M%S)
  local CACHE="$HOME/cdms_cache/filler_${tag}_$TS"
  log "===== ARM $tag  cache=$CACHE ====="
  local n=0 tot=$(echo $PASS | wc -w)
  for m in $PASS; do
    n=$((n+1)); ok=""
    for attempt in 1 2 3; do
      log "=== [$tag $n/$tot] $m attempt $attempt ==="
      if $PY tools/redteam_claude_md_interference.py --backend ollama --models "$m" \
        --modes BEM BEM_WORKSPACE_FACT --variant v1 --expand-probes --sp-expansion-bank "$@" \
        --expand-subsample-n 31 --rephrasings-per-original 1 --cache-dir "$CACHE" \
        >>"$DETAIL" 2>&1; then ok=1; log "  ok $m"; break; fi
      log "  attempt $attempt FAIL $m; sleep 60"; sleep 60
    done
    [ -n "$ok" ] || log "  GAVE UP $m"
  done
  echo "$CACHE" > "$HOME/cdms_filler_${tag}.cachedir"
  log "===== ARM $tag DONE ====="
}

run_arm single  --multifact-n 1
run_arm triple  --multifact-n 3
run_arm filler  --scaffold-filler
touch "$HOME/cdms_filler.done"
log "===== POWERED FILLER (3 arms) DONE ====="
