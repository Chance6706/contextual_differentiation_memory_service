#!/usr/bin/env bash
# LOCALJUDGE Sparky driver (LOCALJUDGE_PREREG.md). Runs ON Sparky.
#
# Ship set (scp from the repo to ~/cdms_localjudge/):
#   tools/local_judge.py tools/ownership_judge.py tools/openrouter_chat.py
#   tools/openrouter_cost_guard.py            (stdlib-only import chain, verified)
#   inputs/  = the *_JUDGE.jsonl files (or gold_set_a4.jsonl) for this phase
#   manifest.jsonl (optional, Phase B tiers)
#
# Usage:  ./cdms_localjudge_run.sh <model> <phase-tag> [--gold] [--sample-manifest manifest.jsonl] [--limit N]
# Output: ~/cdms_localjudge/out_<phase-tag>/<input>__<model>.jsonl + localjudge_meta__<model>.json
#         log: ~/cdms_localjudge/<phase-tag>_<model>.log ; done marker: ~/cdms_localjudge/<phase-tag>_<model>.done
#
# Serial per model (keeps the constant rubric prefix hot in ollama's KV cache); chunked per file
# via the harness's per-file atomic outputs + response cache => kill/resume ad hoc for Nate's
# ComfyUI windows costs only the in-flight file's uncached rows.
set -euo pipefail
cd ~/cdms_localjudge

MODEL="$1"; TAG="$2"; shift 2
SAFE=$(echo "$MODEL" | tr -c 'A-Za-z0-9._-' '_')
OUT="out_${TAG}"; CACHE="cache_${SAFE}"
mkdir -p "$OUT"

echo "[$(date +%F' '%T)] LOCALJUDGE start model=$MODEL tag=$TAG extra=[$*]" | tee -a "${TAG}_${SAFE}.log"
python3 local_judge.py inputs/*.jsonl \
  --model "$MODEL" --out-dir "$OUT" --cache-dir "$CACHE" \
  --url "${CDMS_OLLAMA_URL:-http://localhost:11434}" "$@" 2>&1 | tee -a "${TAG}_${SAFE}.log"

echo "LOCALJUDGE_DONE $MODEL $TAG" > "${TAG}_${SAFE}.done"
echo "[$(date +%F' '%T)] done" | tee -a "${TAG}_${SAFE}.log"
