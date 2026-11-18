"""Le harnais : la boucle complète, réutilisable.

Le modèle ne peut pas exécuter un outil : c'est le harnais qui l'exécute.
Chaque tour, le modèle renvoie soit un texte (fin de la boucle), soit des
tool_calls : le harnais exécute alors chaque outil, ajoute au fil le message
de l'assistant puis un message « tool » (résultat en JSON, relié par
tool_call_id), et rappelle le modèle avec le fil grossi.
Garde-fou : max_tours tours au maximum, sinon on s'arrête.

Chaque tour est écrit dans une trace lisible par un humain,
traces/AAAAMMJJ-HHMMSS.md : la requête JSON complète, la réponse JSON
complète, chaque outil exécuté avec ses arguments et son résultat, la durée
de l'appel et les tokens consommés. Rien n'est tronqué.

Si un outil demandé n'existe pas, ou si ses arguments ne sont pas un JSON
valide, l'erreur est renvoyée au modèle dans un message « tool » : le modèle
peut se corriger, et la boucle ne plante pas.
"""

import datetime
import json
import time
from pathlib import Path

from etape1_appel import LLM_URL, MODELE, appeler


def executer_outil(appel, fonctions):
    """Exécute un seul tool_call.

    Les erreurs (outil inconnu, arguments non valides) sont renvoyées comme
    résultat : le harnais les renverra au modèle au lieu de planter.
    """
    nom = appel["function"]["name"]
    if nom not in fonctions:
        disponibles = ", ".join(fonctions)
        return {"erreur": f"Outil inconnu : {nom}. Outils disponibles : {disponibles}."}
    bruts = appel["function"].get("arguments") or "{}"
    try:
        arguments = json.loads(bruts)
    except json.JSONDecodeError as e:
        return {"erreur": f"Arguments non valides pour {nom} : {bruts} ({e})"}
    try:
        return fonctions[nom](**arguments)
    except TypeError as e:
        return {"erreur": f"Arguments inattendus pour {nom} : {e}"}


def _ecrire_tour(trace, tour, nb_messages, requete, recu, duree):
    """Écrit un tour dans la trace : durée, tokens, requête et réponse."""
    usage = recu.get("usage", {})
    trace.write(f"## Tour {tour} — {nb_messages} message(s) dans le fil\n\n")
    trace.write(f"Durée de l'appel : {duree:.2f} s\n\n")
    trace.write(f"Tokens : {json.dumps(usage, ensure_ascii=False)}\n\n")
    trace.write("### Requête JSON\n\n```json\n")
    trace.write(json.dumps(requete, ensure_ascii=False, indent=2))
    trace.write("\n```\n\n")
    trace.write("### Réponse JSON\n\n```json\n")
    trace.write(json.dumps(recu, ensure_ascii=False, indent=2))
    trace.write("\n```\n\n")


def _ecrire_outil(trace, appel, resultat):
    """Écrit dans la trace l'exécution d'un outil : arguments et résultat."""
    nom = appel["function"]["name"]
    trace.write(f"- `{nom}`\n")
    trace.write(f"  - arguments : {appel['function'].get('arguments') or '{}'}\n")
    trace.write(f"  - résultat  : {json.dumps(resultat, ensure_ascii=False)}\n")


def executer(question, outils, fonctions, systeme=None, max_tours=5):
    """Fait tourner la boucle : question → modèle → outils → modèle…

    outils : liste des définitions JSON des outils (format OpenAI).
    fonctions : dictionnaire nom de l'outil → fonction Python à exécuter.
    Renvoie la réponse finale et le chemin de la trace.
    """
    fil = []
    if systeme:
        fil.append({"role": "system", "content": systeme})
    fil.append({"role": "user", "content": question})

    trace_chemin = Path("traces") / f"{datetime.datetime.now():%Y%m%d-%H%M%S}.md"
    trace_chemin.parent.mkdir(parents=True, exist_ok=True)

    reponse_finale = None
    with trace_chemin.open("w", encoding="utf-8") as trace:
        trace.write(f"# Trace du harnais — {trace_chemin.stem}\n\n")
        trace.write(f"Question : {question}\n\n")
        trace.write(f"Modèle : {MODELE} — {LLM_URL}\n\n")

        for tour in range(1, max_tours + 1):
            # La requête exacte envoyée (appeler() l'affiche aussi à l'écran).
            requete = {"model": MODELE, "messages": fil}
            if outils:
                requete["tools"] = outils

            debut = time.monotonic()
            recu = appeler(fil, outils=outils)
            duree = time.monotonic() - debut

            _ecrire_tour(trace, tour, len(fil), requete, recu, duree)
            trace.flush()  # si ce tour plante, les tours précédents sont gardés

            message = recu["choices"][0]["message"]
            fil.append(message)  # le message de l'assistant, tel quel

            if not message.get("tool_calls"):
                reponse_finale = message.get("content")
                break  # réponse sans appel d'outil : la boucle est finie

            # Le harnais exécute chaque outil et ajoute le résultat au fil.
            trace.write("### Outils exécutés\n\n")
            for appel in message["tool_calls"]:
                resultat = executer_outil(appel, fonctions)
                fil.append({
                    "role": "tool",
                    "tool_call_id": appel["id"],
                    "content": json.dumps(resultat, ensure_ascii=False),
                })
                _ecrire_outil(trace, appel, resultat)
            trace.write("\n")
            trace.flush()

        if reponse_finale is None:
            reponse_finale = f"(aucune réponse finale : {max_tours} tours atteints)"
            trace.write(f"\nArrêt : {max_tours} tours atteints sans réponse finale du modèle.\n")

    return reponse_finale, trace_chemin


if __name__ == "__main__":
    # Rejoue la question de l'étape 4, avec l'outil de l'étape 3 et la
    # fausse fonction de l'étape 4 (données des services inventées).
    from etape3_outil import ETAT_SERVICE
    from etape4_boucle import etat_service

    reponse, trace = executer(
        "nginx et postgresql tournent-ils ? Si l'un est en échec, dis-moi depuis quand.",
        outils=[ETAT_SERVICE],
        fonctions={"etat_service": etat_service},
    )
    print()
    print("Trace :", trace)
    print()
    print("RÉPONSE")
    print(reponse)
