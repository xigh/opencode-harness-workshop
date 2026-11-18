"""Étape 3 : les outils.

On donne au modèle un outil (ici : lire l'état d'un service système) et on
regarde ce qu'il renvoie. Quand la question nécessite l'outil, il ne répond
pas en texte : il demande un « appel d'outil » (tool_calls, nom + arguments
en JSON). Quand la question ne l'exige pas, il répond directement.
On n'exécute rien : on affiche seulement la réponse du modèle.
"""

import json

from etape1_appel import appeler

# L'outil au format JSON Schema des outils OpenAI.
ETAT_SERVICE = {
    "type": "function",
    "function": {
        "name": "etat_service",
        "description": (
            "Donne l'état d'un service système (actif, arrêté, en échec) "
            "et l'heure de son dernier redémarrage."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "nom": {
                    "type": "string",
                    "description": "Le nom du service, par exemple « nginx ».",
                },
            },
            "required": ["nom"],
        },
    },
}


def afficher(reponse):
    """Affiche le choix du modèle : raison de fin et message complet."""
    choix = reponse["choices"][0]
    print()
    print("finish_reason :", choix.get("finish_reason"))
    print("message du modèle (JSON) :")
    print(json.dumps(choix["message"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    # 1) Question qui nécessite l'outil : le modèle doit demander un appel.
    print("=" * 62)
    print("1) « Le service nginx tourne-t-il ? » (outil fourni)")
    print("=" * 62)
    afficher(appeler(
        [{"role": "user", "content": "Le service nginx tourne-t-il ?"}],
        outils=[ETAT_SERVICE],
    ))

    # 2) Question sans rapport : le modèle doit répondre directement.
    print()
    print("=" * 62)
    print("2) « Quelle est la capitale du Portugal ? » (même outil)")
    print("=" * 62)
    afficher(appeler(
        [{"role": "user", "content": "Quelle est la capitale du Portugal ?"}],
        outils=[ETAT_SERVICE],
    ))
