#!/bin/bash
# LOCALJUDGE-2 Phase M run driver (Sparky) — pressure-test MUST_FIX 2.
# Operational, NOT results-determining. Iterates the LOCKED roster model-OUTER, judges the full
# corpus per model, captures digest, audits, determinism-checks, and appends a PASS/FAIL line to a
# committed LEDGER — SKIPPING any model already green so a mid-run reboot resumes cleanly.
#
# Setup on Sparky (~/cdms_localjudge2/): scp the LJ-2 tools (local_judge.py, ownership_judge.py,
# local_judge_score.py, local_judge_audit.py, local_judge_determinism.py, local_judge2_*.py,
# localjudge2_digest.py), corpus/ (37 gen_sweep *_JUDGE.jsonl), gold/gold_set_a4.jsonl,
# confirmation_holdout.json, and a fresh determinism_manifest.jsonl. Analysis runs HERE (Sparky),
# not on the 16 GB Windows box — only receipts are pulled to the repo.
#
# ROSTER order = heavyweight tier + the two new pulls FIRST (early ballpark signal on selection),
# then the mid/small difficulty-map judges. One model tag per line in roster.txt.
set -u
cd ~/cdms_localjudge2
ROSTER=${1:-roster.txt}
LEDGER=ledger.txt; touch "$LEDGER"
NUM_CTX=8192
CORPUS=$(ls corpus/*_JUDGE.jsonl)

log(){ echo "===== [$(date '+%F %T')] $* ====="; }

while read -r MODEL; do
  [ -z "$MODEL" ] && continue
  case "$MODEL" in \#*) continue;; esac
  SAFE=$(echo "$MODEL" | sed 's/[^A-Za-z0-9._-]/_/g')
  if grep -q "^$MODEL PASS" "$LEDGER"; then log "SKIP $MODEL (already PASS)"; continue; fi
  OUT=phaseM/"$SAFE"; CACHE=phaseM/"$SAFE"_cache; mkdir -p "$OUT" "$CACHE"

  log "pre-warm $MODEL (num_ctx $NUM_CTX, keep_alive 4h)"
  curl -s --max-time 3600 http://localhost:11434/api/generate \
    -d "{\"model\":\"$MODEL\",\"prompt\":\"Hi\",\"stream\":false,\"keep_alive\":\"4h\",\"options\":{\"num_predict\":1,\"num_ctx\":$NUM_CTX}}" > /dev/null
  # load-stall screen: if the model isn't resident after pre-warm, mark STALL and move on.
  if ! ollama ps | grep -q "$MODEL"; then log "$MODEL STALL (not resident after pre-warm)"; echo "$MODEL STALL $(date '+%F %T')" >> "$LEDGER"; continue; fi

  log "judge $MODEL full corpus"
  if ! python3 local_judge.py $CORPUS --model "$MODEL" --out-dir "$OUT" --cache-dir "$CACHE" \
       --num-ctx $NUM_CTX --timeout 3600 > "phaseM/${SAFE}.judge.log" 2>&1; then
    log "$MODEL JUDGE-FAIL"; echo "$MODEL FAIL judge $(date '+%F %T')" >> "$LEDGER"; continue; fi

  python3 localjudge2_digest.py "$MODEL" --out "$OUT/digest.json"

  log "audit $MODEL"
  if ! python3 local_judge_audit.py --committed-dir corpus --local-dir "$OUT" --model "$MODEL" \
       > "phaseM/${SAFE}.audit.log" 2>&1; then
    log "$MODEL AUDIT-FAIL"; echo "$MODEL FAIL audit $(date '+%F %T')" >> "$LEDGER"; continue; fi

  log "determinism $MODEL (20 rows, fresh cache)"
  DFILES=$(python3 -c "import json;print(' '.join(sorted({'corpus/'+json.loads(l)['file'] for l in open('determinism_manifest.jsonl')})))")
  python3 local_judge.py $DFILES --model "$MODEL" --out-dir determinism/"$SAFE" \
    --cache-dir determinism/"$SAFE"_cache --sample-manifest determinism_manifest.jsonl --timeout 3600 \
    > "phaseM/${SAFE}.det.log" 2>&1
  if python3 local_judge_determinism.py --phaseb-dir "$OUT" --determinism-dir determinism/"$SAFE" \
     --manifest determinism_manifest.jsonl --model "$MODEL" >> "phaseM/${SAFE}.det.log" 2>&1; then
    log "$MODEL PASS"; echo "$MODEL PASS $(date '+%F %T')" >> "$LEDGER"
  else
    log "$MODEL DETERMINISM-FAIL"; echo "$MODEL FAIL determinism $(date '+%F %T')" >> "$LEDGER"
  fi
done < "$ROSTER"

log "PHASE M DONE — ledger:"; cat "$LEDGER"
# Analysis (on Sparky): after the roster is green, freeze selection then run
#   python3 local_judge2_matrix.py phaseM/*/ --pairwise-out pairwise.jsonl
#   python3 local_judge2_ensemble.py phaseM/*/
#   python3 local_judge2_labelnoise.py phaseM/*/ --k 5 --stamp localjudge2 --out labelnoise.md
# then per-nominee: local_judge2_score.py <nominee dir>/*_JUDGE__*.jsonl --partition confirmation \
#   --confirm-nominee <model> --enforce   (+ --recall-full-corpus for the recall gate)
