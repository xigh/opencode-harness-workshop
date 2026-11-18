"""Étape 2 : le message système, c'est un message de plus en tête de liste.

La même question est posée deux fois : d'abord sans prompt système, puis avec.
Avant chaque appel, on affiche la liste exacte des messages envoyés, pour voir
que le prompt système n'est qu'un rôle de plus en première position.
"""

import json

from etape1_appel import appeler

QUESTION = "Mon serveur web répond 502, que faire ?"
SYSTEME = (
    "Tu es l'assistant de l'équipe infrastructure. "
    "Tu réponds en français, en cinq lignes au plus, et tu termines toujours "
    "par la commande à lancer en premier."
)


def poser(messages):
    """Affiche la liste des messages, appelle le modèle, renvoie son texte."""
    print("MESSAGES ENVOYÉS")
    print(json.dumps(messages, ensure_ascii=False, indent=2))
    recu = appeler(messages)
    return recu["choices"][0]["message"]["content"]


if __name__ == "__main__":
    # 1) Sans prompt système : un seul message, celui de l'utilisateur.
    print("=" * 62)
    print("1) SANS prompt système")
    print("=" * 62)
    sans = poser([
        {"role": "user", "content": QUESTION},
    ])

    # 2) Avec prompt système : un message de plus, en tête de liste.
    print()
    print("=" * 62)
    print("2) AVEC prompt système")
    print("=" * 62)
    avec = poser([
        {"role": "system", "content": SYSTEME},
        {"role": "user", "content": QUESTION},
    ])

    # Les deux réponses l'une sous l'autre, pour comparer.
    print()
    print("=" * 62)
    print("RÉPONSES")
    print("=" * 62)
    print("— Sans prompt système :")
    print(sans)
    print()
    print("— Avec prompt système :")
    print(avec)
