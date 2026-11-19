#!/bin/sh
# Usage : ./etape-etat.sh DOSSIER NN slug     (DOSSIER : projet ou maquette ; consigne : journal/prompts-etat/NN-slug.md)
# La série « état » : chaque étape est une session neuve d'OpenCode, qui lit ETAT.md et AGENTS.md puis met ETAT.md à jour.
# OpenCode minimal : seulement ses outils et ses skills intégrés (rien de Claude Code, pas de plugin, pas de MCP).
# Variables : OPENCODE (le binaire, défaut : opencode) ; OPENCODE_HOME (si définie, sert de HOME à OpenCode : aucune
# configuration, aucun plugin ni skill du poste n'est lu). Écrit par Claude (outillage), pas par OpenCode.
set -e
cd "$(dirname "$0")"
D=$1; N=$2; S=$3; P=journal/prompts-etat/$N-$S.md
[ -d "$D" ] && [ -f "$P" ] || { echo "usage : ./etape-etat.sh projet|maquette NN slug (consigne absente : $P)"; exit 1; }
OC=${OPENCODE:-opencode}
# Couper tout ce qui ne vient pas d'OpenCode (noms de la 2.x, puis ceux de la 1.x).
export OPENCODE_DISABLE_CLAUDE_CODE=1 OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1 OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1
export OPENCODE_DISABLE_EXTERNAL_SKILLS=1 OPENCODE_DISABLE_AUTOUPDATE=1 OPENCODE_DISABLE_FREE_MODELS=1
[ -n "$OPENCODE_HOME" ] && export HOME="$OPENCODE_HOME"
# --pure n'existe qu'en 1.x : la 2.3.2 le refuse et affiche son aide.
case "$($OC --version 2>/dev/null)" in 1.*) PUR=--pure ;; *) PUR= ;; esac
J=journal/etat-$D; mkdir -p $J
echo "etat-$D-$N-$S" > journal/ETAPE
date '+%Y-%m-%dT%H:%M:%S' > $J/$N-$S.debut
# stdin fermé : sinon « opencode run » attend une entrée et ne démarre jamais
(cd "$D" && $OC run $PUR --auto --format json --title "etat-$D-$N-$S" "$(cat ../$P)" < /dev/null) 2>&1 | tee $J/$N-$S.opencode.jsonl
date '+%Y-%m-%dT%H:%M:%S' > $J/$N-$S.fin
echo "" > journal/ETAPE
[ -f "$D/ETAT.md" ] && cp "$D/ETAT.md" $J/ETAT-$N.md && echo "état gardé : $J/ETAT-$N.md"
