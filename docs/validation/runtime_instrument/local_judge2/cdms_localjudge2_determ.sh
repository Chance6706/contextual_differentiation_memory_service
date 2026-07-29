#!/bin/bash
# LOCALJUDGE-2 determinism re-judge driver (Sparky) — OPERATIONAL, outside the pinned sha set
# (like cdms_localjudge2_run.sh). Re-judges the 20 committed determinism-manifest coords per
# roster model into determ/<safe>/ with a FRESH per-model cache, for the Windows-side byte-exact
# comparator (local_judge_determinism.py). NOTE 12: byte-exact re-check per model, LJ-1 manifest.
#
# Rule-12 pressure-test record (2026-07-28, folded before first launch):
#  - FRESH cache enforced by rm -rf per model (stale cache would make the check tautological);
#    determ cache dir is disjoint from phaseM cache dirs.
#  - LJ-F6 absent-file hole: local_judge.py judges EVERY row of an input file whose basename is
#    absent from --sample-manifest -> this driver passes ONLY the manifest's files (basename
#    matching verified: _load_manifest keys Path(file).name; lookup in_path.name).
#  - Reboot/crash mid-model leaves no ledger line; re-run rm -rf's the partial dir and redoes it.
#  - A DETERM-FAIL model keeps its partial dir; the comparator fails LOUDLY on missing coords —
#    run the comparator only against DETERM-DONE ledger lines.
#  - num_ctx 8192 and default url match Phase M (byte-exactness is contract-conditional).
set -u
cd ~/cdms_localjudge2
ROSTER=${1:-roster.txt}
MANIFEST=determinism_manifest.jsonl
LEDGER=determ_ledger.txt; touch "$LEDGER"
NUM_CTX=8192
FILES=$(python3 -c "import json; print(' '.join(sorted({'corpus/'+json.loads(l)['file'] for l in open('$MANIFEST') if l.strip()})))")
[ -z "$FILES" ] && { echo "FATAL: manifest parse produced no files"; exit 1; }
log(){ echo "===== [$(date '+%F %T')] $* ====="; }

grep -vE '^\s*#|^\s*$' "$ROSTER" | while read -r MODEL; do
  MODEL=$(echo "$MODEL" | tr -d '[:space:]')
  [ -z "$MODEL" ] && continue
  SAFE=$(echo "$MODEL" | sed 's/[^A-Za-z0-9._-]/_/g')
  if grep -q "^$MODEL DETERM-DONE" "$LEDGER"; then log "SKIP $MODEL (already DONE)"; continue; fi
  OUT=determ/"$SAFE"; CACHE=determ/"$SAFE"_cache
  rm -rf "$OUT" "$CACHE"; mkdir -p "$OUT" "$CACHE"

  log "pre-warm $MODEL (num_ctx $NUM_CTX)"
  curl -s --max-time 3600 http://localhost:11434/api/generate \
    -d "{\"model\":\"$MODEL\",\"prompt\":\"Hi\",\"stream\":false,\"keep_alive\":\"1h\",\"options\":{\"num_predict\":1,\"num_ctx\":$NUM_CTX}}" > /dev/null
  if ! ollama ps | grep -q "$MODEL"; then
    log "$MODEL DETERM-STALL (not resident after pre-warm)"
    grep -q "^$MODEL DETERM-STALL" "$LEDGER" || echo "$MODEL DETERM-STALL $(date '+%F %T')" >> "$LEDGER"; continue
  fi

  log "re-judge $MODEL (20 manifest coords, fresh cache)"
  if python3 local_judge.py $FILES --sample-manifest "$MANIFEST" --model "$MODEL" \
       --out-dir "$OUT" --cache-dir "$CACHE" --num-ctx $NUM_CTX --timeout 3600 \
       > "determ/${SAFE}.determ.log" 2>&1; then
    log "$MODEL DETERM-DONE"; echo "$MODEL DETERM-DONE $(date '+%F %T')" >> "$LEDGER"
  else
    log "$MODEL DETERM-FAIL (see determ/${SAFE}.determ.log)"; echo "$MODEL DETERM-FAIL $(date '+%F %T')" >> "$LEDGER"
  fi
done
log "DETERM PASS DONE — ledger:"; cat "$LEDGER"
