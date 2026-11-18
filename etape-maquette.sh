#!/bin/sh
# Usage : ./etape-maquette.sh NN slug   (prompt dans journal/prompts-maquette/NN-slug.md, projet dans maquette/)
# Même principe que etape.sh : OpenCode sur le modèle local, sortie JSON complète, instantané et diff. Écrit par Claude.
set -e
cd "$(dirname "$0")"
N=$1; S=$2; P=journal/prompts-maquette/$N-$S.md
[ -f "$P" ] || { echo "prompt absent : $P"; exit 1; }
mkdir -p journal/instantanes-maquette/base
PREC=$(ls journal/instantanes-maquette | grep -E "^[0-9]+$" | awk -v n="$N" '$1 < n' | sort -n | tail -1); [ -n "$PREC" ] || PREC=base
echo "maquette-$N-$S" > journal/ETAPE
date '+%Y-%m-%dT%H:%M:%S' > journal/maquette-$N-$S.debut
export OPENCODE_DISABLE_CLAUDE_CODE=1 OPENCODE_DISABLE_EXTERNAL_SKILLS=1
(cd maquette && opencode run --pure --auto --format json --title "maquette-$N-$S" "$(cat ../$P)" < /dev/null) 2>&1 | tee journal/maquette-$N-$S.opencode.jsonl
date '+%Y-%m-%dT%H:%M:%S' > journal/maquette-$N-$S.fin
echo "" > journal/ETAPE
rsync -a --delete --exclude .opencode --exclude __pycache__ --exclude .venv --exclude donnees --exclude traces maquette/ journal/instantanes-maquette/$N/
diff -ruN journal/instantanes-maquette/$PREC journal/instantanes-maquette/$N > journal/maquette-$N-$S.diff || true
echo "diff : journal/maquette-$N-$S.diff ($(wc -l < journal/maquette-$N-$S.diff) lignes)"
