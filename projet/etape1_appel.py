"""Étape 1 : le plus petit client possible pour le serveur du modèle.

Un appel à /chat/completions, sans streaming. La requête et la réponse
sont affichées telles quelles pour que chaque étape du harnais soit visible.
"""

import json
import os
import urllib.request

# Adresse et nom du modèle, lisibles dans l'environnement.
LLM_URL = os.environ.get("LLM_URL", "http://127.0.0.1:8800/v1")
MODELE = os.environ.get("LLM_MODELE", "qwen3.8-27b")


def appeler(messages, outils=None):
    """Envoie les messages au modèle et renvoie la réponse JSON.

    Si outils est fourni (liste de dictionnaires, format OpenAI),
    il est ajouté à la requête sous la clé "tools".
    """
    requete = {
        "model": MODELE,
        "messages": messages,
    }
    if outils is not None:
        requete["tools"] = outils

    print(">>> REQUÊTE")
    print(json.dumps(requete, ensure_ascii=False, indent=2))

    corps = json.dumps(requete).encode("utf-8")
    demande = urllib.request.Request(
        LLM_URL + "/chat/completions",
        data=corps,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(demande) as reponse:
        recu = json.loads(reponse.read().decode("utf-8"))

    print("<<< RÉPONSE")
    print(json.dumps(recu, ensure_ascii=False, indent=2))
    return recu


if __name__ == "__main__":
    messages = [
        {"role": "user", "content": "En une phrase, qu'est-ce qu'un reverse proxy ?"},
    ]
    recu = appeler(messages)
    texte = recu["choices"][0]["message"]["content"]
    usage = recu.get("usage", {})
    print()
    print(texte)
    print(f"Tokens consommés : {usage}")
