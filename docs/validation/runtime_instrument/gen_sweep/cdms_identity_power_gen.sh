#!/bin/bash
# Phase B — IDENTITY-POWER run: expanded 90-facet bank (180 variants), FRESH cache.
# Adds 36 uncurated-identity facets (54-89) to POWER the identity stratum + a curation-confound
# test (uncurated-identity vs curated-identity). Re-runs ALL generation-study models on the
# expanded bank, FRESH cache (CLAUDE.md rule 13), temp=0 (deterministic), model-OUTER (VRAM),
# BEM + BEM_WORKSPACE_FACT, variant v1. GIRAFFE gate auto-excludes template-fails (olmo3 etc.).
set -u
cd ~/cdms || exit 1
PY=.venv/bin/python
TS=$(date +%Y%m%d_%H%M%S)
CACHE="$HOME/cdms_cache/identity_power_$TS"
DETAIL="$HOME/cdms_identity_power.detail"
GATE="$HOME/cdms_identity_power.gate"
export CDMS_EMBED_BACKEND=hash
: > "$DETAIL"; : > "$GATE"
log(){ echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$DETAIL"; }

GRANITE8="granite-3.0-8b-q8 granite-3.1-8b-q8 granite-3.2-8b-q8 granite-3.3-8b-q8"
GRANITE2="granite-3.0-2b-q8 granite-3.1-2b-q8 granite-3.2-2b-q8 granite-3.3-2b-q8"
MISTRAL="mistral-g-v0.1 mistral-g-v0.2 mistral-g-v0.3"
MECH_QWEN="qwen1.5-7b-q8 qwen2-7b-q8 qwen2.5-7b-q8"
MECH_PHI="phi-3-mini-q8 phi-3.5-mini-q8 phi-4-mini-q8"
SINGLE="olmo3-7b-q8 internlm2.5-7b-q8"
ECO_GEMMA="gemma3:12b gemma4:31b"
DISTILL="qwen3.5-9b-base-q8 claude-opus-distill-q8 claude-code-q8 claude-fable-q8 claude-mythos-q8"
ALL="$GRANITE8 $GRANITE2 $MISTRAL $MECH_QWEN $MECH_PHI $SINGLE $ECO_GEMMA $DISTILL"

log "=== identity-power (EXPANDED 90-facet bank, 180 variants, fresh cache) start (cache=$CACHE) ==="
if ! curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then log "FATAL: ollama down"; exit 2; fi
NBANK=$($PY -c "import sys; sys.path.insert(0,'tools'); import probes_bem_facet as p; print(len(p.PROBES_BEM_FACET))" 2>/dev/null)
log "--- bank originals seen by harness: $NBANK (expect 90) ---"
if [ "$NBANK" != "90" ]; then log "FATAL: harness bank is $NBANK, not 90 (stale push?)"; exit 3; fi

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
log "--- gate done: passers =$PASS ---"

n=0; tot=$(echo $PASS | wc -w)
for m in $PASS; do
  n=$((n+1)); log "=== [$n/$tot] generating $m (180 variants, expanded bank) ==="
  $PY tools/redteam_claude_md_interference.py --backend ollama --models "$m" \
    --modes BEM BEM_WORKSPACE_FACT --variant v1 --expand-probes --bem-facet-bank \
    --expand-subsample-n 180 --rephrasings-per-original 1 --cache-dir "$CACHE" \
    >>"$DETAIL" 2>&1 && log "  ok $m" || log "  FAIL $m"
done
log "=== IDENTITY-POWER DONE (cache=$CACHE) ==="
echo "$CACHE" > "$HOME/cdms_identity_power.cachedir"
touch "$HOME/cdms_identity_power.done"
