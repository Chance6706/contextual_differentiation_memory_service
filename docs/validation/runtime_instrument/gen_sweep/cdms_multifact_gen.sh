#!/bin/bash
# MULTI-FACT scaffold run (MULTIFACT_PREREG.md §10): TWO arms, single (n=1) + triple (n=3), each a fresh
# cache, over mech-11 + distill. Clean-strata bank (65 facets, 130 variants), v1, temp=0, model-OUTER,
# BEM + BEM_WORKSPACE_FACT. GIRAFFE gate + mech-11 completeness abort. gemma/eco/single EXCLUDED
# (under-surfaced in clean-strata; can't inform dilution).
set -u
cd ~/cdms || exit 1
PY=.venv/bin/python
export CDMS_EMBED_BACKEND=hash
DETAIL="$HOME/cdms_multifact.detail"; GATE="$HOME/cdms_multifact.gate"
: > "$DETAIL"; : > "$GATE"
log(){ echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$DETAIL"; }

GRANITE8="granite-3.0-8b-q8 granite-3.1-8b-q8 granite-3.2-8b-q8 granite-3.3-8b-q8"
GRANITE2="granite-3.0-2b-q8 granite-3.1-2b-q8 granite-3.2-2b-q8 granite-3.3-2b-q8"
MISTRAL="mistral-g-v0.1 mistral-g-v0.2 mistral-g-v0.3"
MECH11="$GRANITE8 $GRANITE2 $MISTRAL"
DISTILL="qwen3.5-9b-base-q8 claude-opus-distill-q8 claude-code-q8 claude-fable-q8 claude-mythos-q8"
ALL="$MECH11 $DISTILL"

NBANK=$($PY -c "import sys; sys.path.insert(0,'tools'); import probes_cleanstrata as p; print(len(p.PROBES_CLEANSTRATA))" 2>/dev/null)
log "--- bank originals: $NBANK (expect 65) ---"
[ "$NBANK" = "65" ] || { log "FATAL: bank $NBANK != 65 (stale push?)"; exit 3; }
NTOK=$($PY -c "import sys; sys.path.insert(0,'tools'); import redteam_claude_md_interference as R; print(len(R.MULTIFACT_TOKENS))" 2>/dev/null)
log "--- multifact tokens: $NTOK (expect 3) ---"
[ "$NTOK" = "3" ] || { log "FATAL: MULTIFACT_TOKENS $NTOK != 3"; exit 3; }
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
  echo " $PASS " | grep -q " $m " || { log "FATAL: mech-11 model $m gate-failed; decision cell incomplete"; exit 4; }
done
log "--- mech-11 decision cell complete; passers=$PASS ---"

for ARM in 1 3; do
  TS=$(date +%Y%m%d_%H%M%S)
  CACHE="$HOME/cdms_cache/multifact_$([ $ARM = 1 ] && echo single || echo triple)_$TS"
  log "===== ARM n=$ARM  cache=$CACHE ====="
  n=0; tot=$(echo $PASS | wc -w)
  for m in $PASS; do
    n=$((n+1)); ok=""
    for attempt in 1 2 3; do
      log "=== [n=$ARM $n/$tot] $m attempt $attempt ==="
      if $PY tools/redteam_claude_md_interference.py --backend ollama --models "$m" \
        --modes BEM BEM_WORKSPACE_FACT --variant v1 --expand-probes --cleanstrata-bank \
        --multifact-n $ARM --expand-subsample-n 130 --rephrasings-per-original 1 --cache-dir "$CACHE" \
        >>"$DETAIL" 2>&1; then ok=1; log "  ok $m"; break; fi
      log "  attempt $attempt FAIL $m; sleep 60"; sleep 60
    done
    [ -n "$ok" ] || log "  GAVE UP $m (analyzer completeness assert will catch it)"
  done
  echo "$CACHE" > "$HOME/cdms_multifact_$([ $ARM = 1 ] && echo single || echo triple).cachedir"
  log "===== ARM n=$ARM DONE ====="
done
touch "$HOME/cdms_multifact.done"
log "===== MULTIFACT BOTH ARMS DONE ====="
