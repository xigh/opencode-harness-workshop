"""Index local des documents : découpage, embeddings, recherche.

1. Lire les documents des trois fichiers donnees/documents-*.jsonl.
2. Découper chaque texte en morceaux d'environ 1 000 caractères, avec un
   recouvrement de 150, coupés de préférence en fin de paragraphe ou de
   phrase. Chaque morceau commence par le titre du document.
3. Calculer l'embedding de chaque morceau (API compatible OpenAI, en
   paquets de 16) et normaliser le vecteur.
4. Ranger le tout dans donnees/index.json (métadonnées + vecteurs).
5. Recherche d'essai par produit scalaire, en respectant les droits.

Le stockage est isolé dans ranger() et chercher() : pour passer à Qdrant,
seules ces deux fonctions changent, pas le reste du programme.
"""

import json
import math
import os
import time
import urllib.request
from pathlib import Path

DONNEES = Path(__file__).resolve().parent / "donnees"
FICHIER_INDEX = DONNEES / "index.json"

TAILLE_MORCEAU = 1000   # longueur visée d'un morceau, en caractères
RECOUVREMENT = 150      # caractères repris par le morceau suivant
TAILLE_PAQUET = 16      # morceaux envoyés à l'API d'embedding à la fois

EMB_URL = os.environ.get("EMB_URL", "http://127.0.0.1:8801/v1").rstrip("/")
EMB_MODELE = os.environ.get("EMB_MODELE", "qwen3-embedding-0.6b")
EMB_CLE = os.environ.get("EMB_CLE", "")  # facultatif


def lire_documents():
    """Lit tous les fichiers donnees/documents-*.jsonl, un document par ligne."""
    documents = []
    for fichier in sorted(DONNEES.glob("documents-*.jsonl")):
        with fichier.open(encoding="utf-8") as source:
            for ligne in source:
                if ligne.strip():
                    documents.append(json.loads(ligne))
    return documents


def decouper(texte):
    """Découpe `texte` en morceaux d'environ TAILLE_MORCEAU caractères.

    La coupure est cherchée de préférence en fin de paragraphe, à défaut
    en fin de phrase ; sinon on coupe à la taille visée. Chaque morceau
    reprend les RECOUVREMENT derniers caractères du précédent, pour ne
    pas perdre le fil au milieu d'une phrase.
    """
    morceaux = []
    debut = 0
    while debut < len(texte):
        fin = min(debut + TAILLE_MORCEAU, len(texte))
        if fin < len(texte):
            borne = debut + TAILLE_MORCEAU // 2  # jamais de coupure avant la moitié
            for marqueur in ("\n\n", "\n", ". ", "! ", "? "):
                indice = texte.rfind(marqueur, borne, fin)
                if indice != -1:
                    fin = indice + (2 if marqueur == "\n\n" else 1)
                    break
        morceau = texte[debut:fin].strip()
        if morceau:
            morceaux.append(morceau)
        if fin >= len(texte):
            break
        debut = max(fin - RECOUVREMENT, debut + 1)
    return morceaux


def normaliser(vecteur):
    """Divise le vecteur par sa norme : le produit scalaire devient un cosinus."""
    norme = math.sqrt(sum(c * c for c in vecteur))
    if norme == 0:
        return vecteur
    return [c / norme for c in vecteur]


def calculer_embeddings(textes):
    """Envoie `textes` à l'API d'embedding (POST /embeddings) et renvoie les vecteurs.

    L'API est compatible OpenAI. Les textes partent par paquets de
    TAILLE_PAQUET ; la clé, si elle est définie, est envoyée en
    « Authorization: Bearer ».
    """
    en_tetes = {"Content-Type": "application/json"}
    if EMB_CLE:
        en_tetes["Authorization"] = f"Bearer {EMB_CLE}"
    vecteurs = []
    for premier in range(0, len(textes), TAILLE_PAQUET):
        paquet = textes[premier:premier + TAILLE_PAQUET]
        corps = json.dumps({"model": EMB_MODELE, "input": paquet}).encode("utf-8")
        requete = urllib.request.Request(EMB_URL + "/embeddings", data=corps, headers=en_tetes)
        with urllib.request.urlopen(requete, timeout=120) as reponse:
            donnees = json.loads(reponse.read().decode("utf-8"))
        for element in sorted(donnees["data"], key=lambda e: e["index"]):
            vecteurs.append(element["embedding"])
    return vecteurs


def ranger(morceaux):
    """Écrit l'index (morceaux, vecteurs normalisés et métadonnées) dans
    donnees/index.json. Seule cette fonction écrit l'index : c'est elle
    qu'on changera pour passer à Qdrant.
    """
    with FICHIER_INDEX.open("w", encoding="utf-8") as fichier:
        json.dump({"morceaux": morceaux}, fichier, ensure_ascii=False)


def a_le_droit(morceau, droits_utilisateur):
    """Vrai si l'utilisateur a le droit de lire le morceau.

    Le morceau est lisible s'il est public (« tous » dans ses droits) ou
    si l'utilisateur fait partie d'au moins l'un des groupes exigés.
    """
    droits = morceau["droits"]
    return "tous" in droits or any(droit in droits_utilisateur for droit in droits)


def chercher(vecteur, k, droits_utilisateur):
    """Retourne les `k` morceaux de l'index les plus proches de `vecteur`.

    La proximité est un produit scalaire en Python pur (les vecteurs sont
    normalisés). Seuls les morceaux que l'utilisateur a le droit de lire
    sont retenus. Seule cette fonction lit l'index.
    """
    with FICHIER_INDEX.open(encoding="utf-8") as fichier:
        index = json.load(fichier)
    notes = []
    for morceau in index["morceaux"]:
        if not a_le_droit(morceau, droits_utilisateur):
            continue
        note = sum(a * b for a, b in zip(vecteur, morceau["vecteur"]))
        notes.append((note, morceau))
    notes.sort(key=lambda couple: couple[0], reverse=True)
    return [morceau for _, morceau in notes[:k]]


def principal():
    debut = time.perf_counter()

    # 1. Lire les documents et découper chaque texte.
    documents = lire_documents()
    morceaux = []
    for document in documents:
        preface = document["titre"] + " — "  # chaque morceau commence par le titre
        for fragment in decouper(document["texte"]):
            morceaux.append({
                "source": document["source"],
                "url": document["url"],
                "titre": document["titre"],
                "maj": document["maj"],
                "droits": document["droits"],
                "texte": preface + fragment,
            })

    # 2. Calculer les embeddings (par paquets de 16) et normaliser.
    vecteurs = calculer_embeddings([m["texte"] for m in morceaux])
    for morceau, vecteur in zip(morceaux, vecteurs):
        morceau["vecteur"] = normaliser(vecteur)

    # 3. Ranger l'index.
    ranger(morceaux)
    duree = time.perf_counter() - debut

    # 4. Bilan de l'indexation.
    par_source = {}
    for m in morceaux:
        par_source[m["source"]] = par_source.get(m["source"], 0) + 1
    print(f"Documents lus      : {len(documents)}")
    for source in ("confluence", "site", "teams"):
        print(f"  morceaux {source:<10} : {par_source.get(source, 0)}")
    print(f"Taille de l'index  : {FICHIER_INDEX.stat().st_size / 1024:.1f} Ko ({FICHIER_INDEX.name})")
    print(f"Temps d'indexation : {duree:.1f} s")

    # 5. Recherche d'essai, avec les droits d'un membre de l'équipe DSI.
    question = "Quel port pour le VPN ?"
    droits = ["equipe:DSI - Infrastructure"]
    vecteur = normaliser(calculer_embeddings([question])[0])
    print(f"\nRecherche d'essai : « {question} »")
    print(f"Droits de l'utilisateur : {droits}")
    for rang, morceau in enumerate(chercher(vecteur, 3, droits), 1):
        note = sum(a * b for a, b in zip(vecteur, morceau["vecteur"]))
        apercu = " ".join(morceau["texte"].split())
        if len(apercu) > 90:
            apercu = apercu[:90] + "…"
        print(f"{rang}. [{morceau['source']}] « {morceau['titre']} » (score {note:.3f})")
        print(f"   {apercu}")


if __name__ == "__main__":
    principal()
