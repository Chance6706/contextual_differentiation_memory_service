#!/bin/bash
# LOCALJUDGE-2 Phase M run driver (Sparky) — pressure-test MUST_FIX 2. Operational, NOT
# results-determining. JUDGES the full corpus per roster model + captures its digest, appending a
# JUDGED/STALL/FAIL line to a committed ledger — SKIPPING any model already JUDGED so a mid-run
# reboot (or a re-run after a late `ollama create`) resumes cleanly. Idempotent via the ledger.
#
# Audit + determinism + the matrix/ensemble/scorer analysis run WINDOWS-side against pulled outputs
# (the proven LJ-1 model; the LJ-2 tools carry repo-relative default paths). Only judging is here.
#
# Setup (~/cdms_localjudge2/): local_judge.py + ownership_judge.py (reused from ~/cdms_localjudge/),
# localjudge2_digest.py, corpus/ (37 gen_sweep *_JUDGE.jsonl), roster.txt.
set -u
cd ~/cdms_localjudge2
ROSTER=${1:-roster.txt}
LEDGER=ledger.txt; touch "$LEDGER"
NUM_CTX=8192
CORPUS=$(ls corpus/*_JUDGE.jsonl)
log(){ echo "===== [$(date '+%F %T')] $* ====="; }

grep -vE '^\s*#|^\s*$' "$ROSTER" | while read -r MODEL; do
  MODEL=$(echo "$MODEL" | tr -d '[:space:]')
  [ -z "$MODEL" ] && continue
  SAFE=$(echo "$MODEL" | sed 's/[^A-Za-z0-9._-]/_/g')
  if grep -q "^$MODEL JUDGED" "$LEDGER"; then log "SKIP $MODEL (already JUDGED)"; continue; fi
  OUT=phaseM/"$SAFE"; CACHE=phaseM/"$SAFE"_cache; mkdir -p "$OUT" "$CACHE"

  log "pre-warm $MODEL (num_ctx $NUM_CTX, keep_alive 4h)"
  curl -s --max-time 3600 http://localhost:11434/api/generate \
    -d "{\"model\":\"$MODEL\",\"prompt\":\"Hi\",\"stream\":false,\"keep_alive\":\"4h\",\"options\":{\"num_predict\":1,\"num_ctx\":$NUM_CTX}}" > /dev/null
  if ! ollama ps | grep -q "$MODEL"; then
    log "$MODEL STALL (not resident after pre-warm — missing model or load-stall)"
    grep -q "^$MODEL STALL" "$LEDGER" || echo "$MODEL STALL $(date '+%F %T')" >> "$LEDGER"; continue
  fi

  log "judge $MODEL full corpus"
  if python3 local_judge.py $CORPUS --model "$MODEL" --out-dir "$OUT" --cache-dir "$CACHE" \
       --num-ctx $NUM_CTX --timeout 3600 > "phaseM/${SAFE}.judge.log" 2>&1; then
    python3 localjudge2_digest.py "$MODEL" --out "$OUT/digest.json" 2>/dev/null || true
    log "$MODEL JUDGED"; echo "$MODEL JUDGED $(date '+%F %T')" >> "$LEDGER"
  else
    log "$MODEL JUDGE-FAIL (see phaseM/${SAFE}.judge.log)"; echo "$MODEL FAIL $(date '+%F %T')" >> "$LEDGER"
  fi
done
log "PHASE M PASS DONE — ledger:"; cat "$LEDGER"
