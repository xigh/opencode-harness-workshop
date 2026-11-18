"""L'ingestion des documents de l'assistant documentaire : PDF → morceaux → embeddings → Qdrant.

Chaque étape est affichée à l'écran, pour la formation :
- pour chaque fichier, les pages, caractères, morceaux et durées ;
- une seule fois, pour le premier morceau du premier fichier : son texte
  complet, la requête d'embedding envoyée (liste des textes abrégée), les
  8 premières valeurs du vecteur, et le point tel qu'envoyé à Qdrant ;
- à la fin, les totaux et le nombre de points relu depuis Qdrant.

Options :
  --limite N   ne traiter que les N premiers fichiers du manifeste
  --recreer    supprimer la collection avant de commencer
"""

import argparse
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parent
PDF_DIR = RACINE.parent / "corpus" / "pdf"
MANIFESTE = RACINE.parent / "corpus" / "manifeste.json"

# Les adresses se lisent dans l'environnement, avec des défauts de démo.
EMBED_URL = os.environ.get("EMBED_URL", "http://127.0.0.1:8801/v1")
EMBED_MODELE = os.environ.get("EMBED_MODELE", "qwen3-embedding-0.6b")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:8803")
COLLECTION = "documents"

TAILLE_MORCEAU = 1500  # longueur cible d'un morceau, en caractères
RECOUVREMENT = 200     # caractères partagés entre deux morceaux consécutifs
LOT_EMBEDDINGS = 32    # nombre de textes envoyés au serveur d'embedding à la fois


def envoyer(url, corps=None, method="GET"):
    """Envoie une requête JSON (bibliothèque standard) et renvoie le JSON reçu."""
    donnees = json.dumps(corps, ensure_ascii=False).encode("utf-8") if corps is not None else None
    demande = urllib.request.Request(
        url, data=donnees, method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(demande, timeout=120) as reponse:
        return json.loads(reponse.read().decode("utf-8"))


def extraire(chemin):
    """Extrait le texte du PDF, page par page.

    `pdftotext -layout` sépare les pages par le caractère \f (saut de page).
    Renvoie la liste des pages (texte brut) et la durée de l'extraction.
    """
    debut = time.monotonic()
    sortie = subprocess.run(
        ["pdftotext", "-layout", str(chemin), "-"],
        capture_output=True, check=True,
    ).stdout.decode("utf-8")
    pages = sortie.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()  # le dernier \f laisse un bout vide en fin de liste
    return pages, time.monotonic() - debut


def decouper(texte):
    """Découpe le texte en morceaux d'environ TAILLE_MORCEAU caractères.

    Deux morceaux consécutifs se recouvrent de RECOUVREMENT caractères,
    et la coupure se fait sur une espace pour ne jamais couper un mot.
    """
    morceaux = []
    debut = 0
    longueur = len(texte)
    while debut < longueur:
        fin = debut + TAILLE_MORCEAU
        if fin >= longueur:
            morceaux.append(texte[debut:].strip())
            break
        # La coupure va sur la dernière espace des RECOUVREMENT derniers
        # caractères : le morceau reste « environ 1500 » sans couper un mot.
        espace = texte.rfind(" ", debut + TAILLE_MORCEAU - RECOUVREMENT, fin)
        if espace == -1:
            espace = fin  # un mot de plus de 200 caractères : coupure dure
        morceaux.append(texte[debut:espace].strip())
        debut = max(espace - RECOUVREMENT, debut + 1)  # recouvrement, sans boucle infinie
    return [m for m in morceaux if m]


def embedder(textes, detail=False):
    """Calcule les embeddings, par lots de LOT_EMBEDDINGS.

    Les textes s'envoient tels quels, sans préfixe. Renvoie la liste des
    vecteurs (même ordre) et la durée. Si detail est vrai, affiche une fois
    la requête (abrégée) et la tête du premier vecteur.
    """
    vecteurs = []
    debut = time.monotonic()
    for i in range(0, len(textes), LOT_EMBEDDINGS):
        lot = textes[i:i + LOT_EMBEDDINGS]
        requete = {"model": EMBED_MODELE, "input": lot}
        if detail and i == 0:
            # Affichage : la requête exacte, sans la liste complète des textes.
            abrgee = dict(requete)
            abrgee["input"] = [lot[0][:80] + "…", f"… {len(lot) - 1} autres textes dans ce lot"]
            print("REQUÊTE ENVOYÉE AU SERVEUR D'EMBEDDING (liste des textes abrégée)")
            print(json.dumps(abrgee, ensure_ascii=False, indent=2))
        recu = envoyer(EMBED_URL + "/embeddings", requete, method="POST")
        for donnee in recu["data"]:
            vecteurs.append(donnee["embedding"])
        if detail and i == 0:
            premier = vecteurs[0]
            print(f"PREMIER VECTEUR : {premier[:8]} … (taille : {len(premier)})")
    return vecteurs, time.monotonic() - debut


def collection_existe():
    """Vrai si la collection existe déjà dans Qdrant."""
    try:
        envoyer(f"{QDRANT_URL}/collections/{COLLECTION}")
        return True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        raise


def qdrant_creer_collection(taille):
    """Crée la collection : taille du vecteur en paramètre, distance Cosine."""
    corps = {"vectors": {"size": taille, "distance": "Cosine"}}
    envoyer(f"{QDRANT_URL}/collections/{COLLECTION}", corps, method="PUT")
    print(f"Collection « {COLLECTION} » créée (vecteurs de {taille} dimensions, distance Cosine).")


def qdrant_supprimer_collection():
    try:
        envoyer(f"{QDRANT_URL}/collections/{COLLECTION}", method="DELETE")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"Collection « {COLLECTION} » : rien à supprimer, elle n'existait pas.")
            return
        raise
    print(f"Collection « {COLLECTION} » supprimée.")


def qdrant_ajouter_points(points, detail=False):
    """Envoie les points dans la collection (wait=true : écriture confirmée)."""
    if detail:
        # Affichage : le point tel qu'envoyé, vecteur abrégé.
        affichage = dict(points[0])
        affichage["vector"] = affichage["vector"][:8] + [f"… ({len(affichage['vector'])} dimensions)"]
        print("POINT ENVOYÉ À QDRANT (vecteur abrégé)")
        print(json.dumps(affichage, ensure_ascii=False, indent=2))
    envoyer(
        f"{QDRANT_URL}/collections/{COLLECTION}/points?wait=true",
        {"points": points}, method="PUT",
    )


def qdrant_nombre_points():
    """Relit le nombre de points de la collection depuis Qdrant."""
    recu = envoyer(f"{QDRANT_URL}/collections/{COLLECTION}")
    return recu["result"]["points_count"]


def charger_manifeste():
    """Le manifeste donne, pour chaque PDF, son titre (champ fichier → titre)."""
    with MANIFESTE.open(encoding="utf-8") as f:
        return json.load(f)


def analyser_arguments():
    analyseur = argparse.ArgumentParser(description="Ingestion des PDF de l'assistant documentaire.")
    analyseur.add_argument("--limite", type=int, default=None,
                           help="ne traiter que les N premiers fichiers du manifeste")
    analyseur.add_argument("--recreer", action="store_true",
                           help="supprimer la collection avant de commencer")
    return analyseur.parse_args()


def main():
    args = analyser_arguments()
    entrees = charger_manifeste()
    if args.limite is not None:
        entrees = entrees[:args.limite]

    if args.recreer:
        qdrant_supprimer_collection()

    print(f"Serveur d'embedding : {EMBED_URL} (modèle {EMBED_MODELE})")
    print(f"Qdrant              : {QDRANT_URL} (collection « {COLLECTION} »)")
    print()

    total_morceaux = 0
    prochain_id = 1  # des identifiants entiers qui se suivent
    debut_total = time.monotonic()

    for num, entree in enumerate(entrees, start=1):
        fichier = entree["fichier"]
        chemin = PDF_DIR / fichier
        if not chemin.exists():
            raise SystemExit(f"PDF introuvable : {chemin}")

        detail = num == 1  # le premier morceau du premier fichier, une seule fois
        print(f"=== Fichier {num}/{len(entrees)} : {fichier}")
        print(f"    « {entree['titre']} »")

        # 1) Extraction page par page.
        pages, duree_extraction = extraire(chemin)
        nb_caracteres = sum(len(page) for page in pages)

        # 2) Découpage, page par page.
        morceaux = []
        for num_page, page in enumerate(pages, start=1):
            for num_morceau, texte in enumerate(decouper(page), start=1):
                morceaux.append({
                    "fichier": fichier,
                    "titre": entree["titre"],
                    "page": num_page,
                    "morceau": num_morceau,
                    "texte": texte,
                })

        if detail and morceaux:
            premier = morceaux[0]
            print(f"PREMIER MORCEAU (page {premier['page']}, morceau {premier['morceau']})")
            print(premier["texte"])
            print()

        # 3) Embeddings par lots de 32.
        vecteurs, duree_embedding = embedder([m["texte"] for m in morceaux], detail=detail)

        # La collection est créée quand on connaît la taille du premier vecteur.
        if vecteurs and not collection_existe():
            qdrant_creer_collection(len(vecteurs[0]))

        # 4) Envoi dans Qdrant : le vecteur, et le reste du morceau en payload.
        points = [
            {"id": i, "vector": vecteur, "payload": morceau}
            for i, (morceau, vecteur) in enumerate(zip(morceaux, vecteurs), start=prochain_id)
        ]
        prochain_id += len(points)
        qdrant_ajouter_points(points, detail=detail)
        total_morceaux += len(points)

        print(f"    {len(pages)} pages, {nb_caracteres} caractères, {len(points)} morceaux")
        print(f"    extraction : {duree_extraction:.2f} s — embeddings : {duree_embedding:.2f} s")
        print()

    duree_total = time.monotonic() - debut_total
    nb_points = qdrant_nombre_points()
    print("=" * 62)
    print(f"TOTAL : {total_morceaux} morceaux en {duree_total:.2f} s")
    print(f"Points dans la collection « {COLLECTION} » (relu depuis Qdrant) : {nb_points}")


if __name__ == "__main__":
    main()
