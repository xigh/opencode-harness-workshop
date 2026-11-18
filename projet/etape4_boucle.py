"""Étape 4 : la boucle, le cœur d'un harnais.

Le modèle ne peut pas exécuter un outil : c'est le harnais qui l'exécute.
Chaque tour, le modèle renvoie soit un texte (fin de la boucle), soit des
tool_calls : le harnais exécute alors chaque outil, ajoute au fil le message
de l'assistant puis un message « tool » (résultat en JSON, relié par
tool_call_id), et rappelle le modèle avec le fil grossi.
Garde-fou : 5 tours au maximum, sinon on s'arrête.
"""

import json

from etape1_appel import appeler
from etape3_outil import ETAT_SERVICE

QUESTION = "nginx et postgresql tournent-ils ? Si l'un est en échec, dis-moi depuis quand."
MAX_TOURS = 5

# Les états des services sont inventés : c'est le harnais qui « sait ».
ETATS = {
    "nginx": {"nom": "nginx", "etat": "echec", "en_echec_depuis": "03:12"},
    "postgresql": {"nom": "postgresql", "etat": "actif", "depuis": "hier 22:47"},
}


def etat_service(nom):
    """Fausse fonction : renvoie l'état d'un service (données inventées)."""
    return ETATS.get(nom, {"nom": nom, "etat": "inconnu"})


def executer(appel):
    """Exécute un tool_call : appelle la fausse fonction, renvoie le résultat."""
    nom = appel["function"]["name"]
    arguments = json.loads(appel["function"]["arguments"] or "{}")
    if nom != "etat_service":
        return {"erreur": f"outil inconnu : {nom}"}
    resultat = etat_service(**arguments)
    print(f"  harnais exécute {nom}({arguments}) → {resultat}")
    return resultat


if __name__ == "__main__":
    fil = [{"role": "user", "content": QUESTION}]
    reponse_finale = None

    for tour in range(1, MAX_TOURS + 1):
        print()
        print("=" * 62)
        print(f"TOUR {tour} — {len(fil)} message(s) dans le fil")
        print("=" * 62)

        recu = appeler(fil, outils=[ETAT_SERVICE])
        print(f"Tokens consommés : {recu.get('usage', {})}")

        message = recu["choices"][0]["message"]
        fil.append(message)  # le message de l'assistant, tel quel

        if not message.get("tool_calls"):
            reponse_finale = message.get("content")
            break  # réponse sans appel d'outil : la boucle est finie

        # Le harnais exécute chaque outil et ajoute le résultat au fil.
        for appel in message["tool_calls"]:
            resultat = executer(appel)
            fil.append({
                "role": "tool",
                "tool_call_id": appel["id"],
                "content": json.dumps(resultat, ensure_ascii=False),
            })

    print()
    print("=" * 62)
    if reponse_finale is None:
        print(f"Arrêt : {MAX_TOURS} tours atteints sans réponse finale du modèle.")
    else:
        print("RÉPONSE")
        print("=" * 62)
        print(reponse_finale)
