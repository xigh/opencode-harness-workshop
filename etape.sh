#!/bin/sh
# Usage : ./etape.sh NN slug   (le prompt est lu dans journal/prompts/NN-slug.md)
# Lance OpenCode sur le modèle local, garde la sortie JSON complète, l'instantané et le diff du projet.
# Écrit par Claude (outillage), pas par OpenCode.
set -e
cd "$(dirname "$0")"
N=$1; S=$2; P=journal/prompts/$N-$S.md
[ -f "$P" ] || { echo "prompt absent : $P"; exit 1; }
# instantané précédent : la dernière étape numérotée avant N, sinon l'état initial
PREC=$(ls journal/instantanes | grep -E "^[0-9]+$" | awk -v n="$N" '$1 < n' | sort | tail -1); [ -n "$PREC" ] || PREC=base
echo "$N-$S" > journal/ETAPE
date '+%Y-%m-%dT%H:%M:%S' > journal/$N-$S.debut
# stdin fermé : sinon « opencode run » attend une entrée et ne démarre jamais
# Depuis l'étape 07 : sans les compétences de Claude Code (OpenCode les injecte sinon dans son prompt système)
export OPENCODE_DISABLE_CLAUDE_CODE=1 OPENCODE_DISABLE_EXTERNAL_SKILLS=1
(cd projet && opencode run --pure --auto --format json --title "$N-$S" "$(cat ../$P)" < /dev/null) 2>&1 | tee journal/$N-$S.opencode.jsonl
date '+%Y-%m-%dT%H:%M:%S' > journal/$N-$S.fin
echo "" > journal/ETAPE
rsync -a --delete --exclude .opencode --exclude __pycache__ --exclude .venv --exclude traces projet/ journal/instantanes/$N/
diff -ruN journal/instantanes/$PREC journal/instantanes/$N > journal/$N-$S.diff || true
echo "diff : journal/$N-$S.diff ($(wc -l < journal/$N-$S.diff) lignes)"
