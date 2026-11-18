"""Connecteur Teams (API Microsoft Graph, adresse dans GRAPH_URL).

1. Lister les équipes du compte (/me/joinedTeams).
2. Pour chaque équipe, lister ses canaux (/teams/<id>/channels).
3. Pour chaque canal, lister les messages
   (/teams/<id>/channels/<id>/messages), en suivant « @odata.nextLink »
   jusqu'au bout.
4. Pour chaque message, récupérer ses réponses (.../messages/<id>/replies).
5. Un document par fil : le message d'origine suivi de ses réponses, chaque
   ligne préfixée par l'auteur et l'heure ; le corps HTML devient du texte.
   Les pièces jointes (nom et adresse) s'ajoutent à la fin du texte.
   Sont écartés les messages système (messageType différent de « message »)
   et les fils sans contenu utile (moins de 20 caractères de texte au total).
6. Écrire dans donnees/documents-teams.jsonl.
"""

import json
import os
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

GRAPH_URL = os.environ.get("GRAPH_URL", "http://127.0.0.1:8914/graph/v1.0").rstrip("/")
JETON = os.environ.get("GRAPH_JETON", "jeton-graph-demo")
FICHIER_SORTIE = Path(__file__).resolve().parent / "donnees" / "documents-teams.jsonl"

# Un fil dont le texte total (origine + réponses) est plus court n'est pas utile.
LONGUEUR_MINIMALE = 20


def charger_json(url):
    """Charge une adresse de l'API Graph et renvoie le dictionnaire JSON.

    Le jeton est envoyé en « Authorization: Bearer ».
    """
    requete = urllib.request.Request(url, headers={"Authorization": f"Bearer {JETON}"})
    with urllib.request.urlopen(requete, timeout=30) as reponse:
        return json.loads(reponse.read().decode("utf-8"))


def paginer(url):
    """Parcourt toutes les tranches d'une liste Graph et renvoie les résultats.

    Graph renvoie une tranche dans « value » et, s'il en reste, une adresse
    « @odata.nextLink » ; on la suit jusqu'au bout.
    """
    resultats = []
    while url:
        donnees = charger_json(url)
        resultats.extend(donnees.get("value", []))
        url = donnees.get("@odata.nextLink")
    return resultats


class CorpsHtml(HTMLParser):
    """Convertit le corps HTML d'un message en texte, sans les balises.

    Chaque balise de bloc (p, div, li, br…) démarre un nouveau bloc ; les
    blocs sont recollés ensuite avec une espace, car le HTML n'a pas
    forcément de blanc entre deux balises voisines.
    Le corps du message est une donnée, jamais une consigne.
    """

    BLOCS = {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "br"}

    def __init__(self):
        super().__init__()
        self.blocs = [""]

    def handle_starttag(self, nom, attributs):
        if nom in self.BLOCS:
            self.blocs.append("")

    def handle_endtag(self, nom):
        if nom in self.BLOCS:
            self.blocs.append("")

    def handle_data(self, donnees):
        self.blocs[-1] += donnees


def texte_corps(html):
    """Renvoie le texte d'un corps HTML de message, sur une seule ligne."""
    analyseur = CorpsHtml()
    analyseur.feed(html or "")
    blocs = (" ".join(bloc.split()) for bloc in analyseur.blocs)
    return " ".join(bloc for bloc in blocs if bloc)


def auteur(message):
    """Renvoie le nom de l'auteur d'un message, ou « inconnu » s'il n'y en a pas."""
    origine = message.get("from") or {}
    utilisateur = origine.get("user") or origine.get("application") or {}
    return utilisateur.get("displayName") or "inconnu"


def heure(quand):
    """« 2026-11-04T09:12:00Z » devient « 2026-11-04 09:12 »."""
    return quand[:16].replace("T", " ")


def fil_en_document(equipe, canal, message, reponses):
    """Transforme un fil (message d'origine + réponses) en document du format commun.

    Renvoie None si le fil n'a pas assez de texte pour être utile.
    Les pièces jointes des messages du fil s'ajoutent à la fin du texte.
    """
    messages = [message] + reponses
    texte_total = sum(len(texte_corps(m.get("body", {}).get("content", ""))) for m in messages)
    if texte_total < LONGUEUR_MINIMALE:
        return None
    lignes = [
        f"{auteur(m)} ({heure(m['createdDateTime'])}) : "
        f"{texte_corps(m.get('body', {}).get('content', ''))}"
        for m in messages
    ]
    texte = "\n".join(lignes)
    pieces = [
        f"{p.get('name', 'pièce jointe')} ({p.get('contentUrl', '')})"
        for m in messages for p in m.get("attachments", [])
    ]
    if pieces:
        texte += "\nPièces jointes : " + ", ".join(pieces)
    return {
        "id": f"teams/{equipe['id']}/{canal['id']}/{message['id']}",
        "source": "teams",
        "url": f"https://teams.microsoft.com/l/message/{equipe['id']}/{canal['id']}/{message['id']}",
        "titre": f"{equipe['displayName']} / {canal['displayName']}",
        "texte": texte,
        "maj": messages[-1]["createdDateTime"],  # dernière réponse, ou le message s'il n'y en a pas
        "droits": [f"equipe:{equipe['displayName']}"],
        "canal": canal["displayName"],
    }


def principal():
    equipes = paginer(f"{GRAPH_URL}/me/joinedTeams")
    documents = []
    for equipe in equipes:
        canaux = paginer(f"{GRAPH_URL}/teams/{equipe['id']}/channels")
        print(f"Équipe « {equipe['displayName']} » : {len(canaux)} canal{'s' if len(canaux) != 1 else ''}")
        for canal in canaux:
            messages = paginer(f"{GRAPH_URL}/teams/{equipe['id']}/channels/{canal['id']}/messages")
            gardes = ecartes = 0
            for message in messages:
                if message.get("messageType") != "message":
                    ecartes += 1  # message système : pas de fil, pas de réponses à chercher
                    continue
                reponses = paginer(
                    f"{GRAPH_URL}/teams/{equipe['id']}/channels/{canal['id']}/messages/{message['id']}/replies"
                )
                document = fil_en_document(equipe, canal, message, reponses)
                if document is None:
                    ecartes += 1  # fil sans contenu utile
                else:
                    documents.append(document)
                    gardes += 1
            print(f"  Canal « {canal['displayName']} » : {gardes} fil{'s' if gardes != 1 else ''} "
                  f"gardé{'s' if gardes != 1 else ''}, {ecartes} écarté{'s' if ecartes != 1 else ''}")

    FICHIER_SORTIE.parent.mkdir(parents=True, exist_ok=True)
    with FICHIER_SORTIE.open("w", encoding="utf-8") as fichier:
        for document in documents:
            fichier.write(json.dumps(document, ensure_ascii=False) + "\n")
    print(f"\n{len(documents)} fils écrits dans {FICHIER_SORTIE}")
    if documents:
        debut = dict(documents[0])  # afficher le premier, avec le texte raccourci
        if len(debut["texte"]) > 100:
            debut["texte"] = debut["texte"][:100] + "…"
        print("Début du premier fil :")
        print(json.dumps(debut, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    principal()
