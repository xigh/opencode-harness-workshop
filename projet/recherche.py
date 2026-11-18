"""La recherche : pour une question, retrouver les morceaux qui y répondent, en trois étages.

1) L'embedding de la question, avec le même serveur que l'ingestion.
   Qwen3-Embedding attend une instruction devant les questions
   (les documents, eux, sont envoyés sans préfixe, cf. ingestion.py) ;
2) Les k_vecteur morceaux les plus proches dans Qdrant (distance Cosine) ;
3) Le reranking de ces morceaux par un serveur dédié : on garde les k_final.

Chaque étape affiche la requête JSON envoyée, le JSON reçu (abrégé)
et sa durée. Usage : python3 recherche.py « la question »
"""

import json
import os
import sys
import time
import urllib.request

# Les adresses se lisent dans l'environnement, avec des défauts de démo.
EMBED_URL = os.environ.get("EMBED_URL", "http://127.0.0.1:8801/v1")
EMBED_MODELE = os.environ.get("EMBED_MODELE", "qwen3-embedding-0.6b")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:8803")
RERANK_URL = os.environ.get("RERANK_URL", "http://127.0.0.1:8802/v1")
COLLECTION = "documents"

# L'instruction demandée par Qwen3-Embedding pour transformer une question.
# Elle s'ajoute à la question seule : les documents sont embeddés sans préfixe.
INSTRUCTION = (
    "Instruct: Étant donné une question, retrouver les passages "
    "de documents qui y répondent\nQuery: "
)


def envoyer(url, corps=None, method="GET"):
    """Envoie une requête JSON (bibliothèque standard) et renvoie le JSON reçu."""
    donnees = json.dumps(corps, ensure_ascii=False).encode("utf-8") if corps is not None else None
    demande = urllib.request.Request(
        url, data=donnees, method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(demande, timeout=120) as reponse:
        return json.loads(reponse.read().decode("utf-8"))


def embedder_question(question):
    """Étage 1 : l'embedding de la question, avec l'instruction. Renvoie le vecteur et la durée."""
    requete = {"model": EMBED_MODELE, "input": [INSTRUCTION + question]}
    print("ÉTAGE 1 — EMBEDDING DE LA QUESTION")
    print("REQUÊTE ENVOYÉE AU SERVEUR D'EMBEDDING")
    print(json.dumps(requete, ensure_ascii=False, indent=2))
    debut = time.monotonic()
    recu = envoyer(EMBED_URL + "/embeddings", requete, method="POST")
    duree = time.monotonic() - debut
    vecteur = recu["data"][0]["embedding"]
    print(f"VECTOR REÇU : {vecteur[:8]} … (taille : {len(vecteur)})")
    print(f"Durée : {duree:.2f} s")
    return vecteur, duree


def qdrant_rechercher(vecteur, k):
    """Étage 2 : les k points les plus proches de la collection, avec leur payload.

    Sur /points/query, le vecteur de la requête va dans le champ « query »
    (et non « vector », comme sur l'ancien /points/search).
    """
    requete = {"query": vecteur, "limit": k, "with_payload": True}
    print()
    print("ÉTAGE 2 — RECHERCHE VECTORIELLE DANS QDRANT")
    # Affichage : le vecteur est trop long pour l'écran, on le tronque.
    abrgee = dict(requete)
    abrgee["query"] = vecteur[:8] + [f"… ({len(vecteur)} dimensions)"]
    print("REQUÊTE ENVOYÉE À QDRANT (vecteur abrégé)")
    print(json.dumps(abrgee, ensure_ascii=False, indent=2))
    debut = time.monotonic()
    recu = envoyer(f"{QDRANT_URL}/collections/{COLLECTION}/points/query", requete, method="POST")
    duree = time.monotonic() - debut
    points = recu["result"]["points"]
    # Affichage : les payloads (1500 caractères chacun) seraient illisibles.
    recu_abrege = [
        {"id": p["id"], "score": p["score"], "fichier": p["payload"]["fichier"], "page": p["payload"]["page"]}
        for p in points
    ]
    print("REPONSE RECUE DE QDRANT (payloads abrégés)")
    print(json.dumps(recu_abrege, ensure_ascii=False, indent=2))
    print(f"Durée : {duree:.2f} s")
    return points, duree


def reranker(question, points):
    """Étage 3 : reranking des k_vecteur morceaux. Renvoie les résultats et la durée.

    Le serveur renvoie, pour chaque document, son index (sa position dans la
    liste envoyée) et un score de pertinence entre 0 et 1.
    """
    documents = [p["payload"]["texte"] for p in points]
    requete = {"query": question, "documents": documents}
    print()
    print("ÉTAGE 3 — RERANKING")
    # Affichage : les documents sont longs, on n'en montre que le début.
    abrgee = dict(requete)
    abrgee["documents"] = [d[:60] + "…" for d in documents[:3]] + [f"… {len(documents) - 3} autres documents"]
    print("REQUÊTE ENVOYÉE AU SERVEUR DE RERANKING (documents abrégés)")
    print(json.dumps(abrgee, ensure_ascii=False, indent=2))
    debut = time.monotonic()
    recu = envoyer(RERANK_URL + "/rerank", requete, method="POST")
    duree = time.monotonic() - debut
    print("REPONSE RECUE DU SERVEUR DE RERANKING")
    print(json.dumps(recu, ensure_ascii=False, indent=2))
    print(f"Durée : {duree:.2f} s")
    return recu["results"], duree


def afficher_tableau_vecteur(points):
    """Le tableau des résultats Qdrant : rang, score cosinus, fichier, page, début du texte."""
    print()
    print("RÉSULTATS QDRANT (k plus proches)")
    print(f"{'rang':>4}  {'cosine':>7}  fichier / page / début du texte")
    print("-" * 100)
    for rang, point in enumerate(points, start=1):
        p = point["payload"]
        texte = " ".join(point["payload"]["texte"].split())  # une seule ligne
        debut_texte = texte[:70] + ("…" if len(texte) > 70 else "")
        print(f"{rang:>4}  {point['score']:>7.4f}  {p['fichier']} p.{p['page']} — {debut_texte}")


def afficher_tableau_rerank(points, resultats, k_final):
    """Le tableau après reranking : nouveau rang, ancien rang, score, fichier, page."""
    print()
    print(f"APRÈS RERANKING (les {k_final} meilleurs)")
    print(f"{'nouveau':>7}  {'ancien':>6}  {'rerank':>7}  fichier / page")
    print("-" * 80)
    for nouveau_rang, resultat in enumerate(resultats[:k_final], start=1):
        p = points[resultat["index"]]["payload"]
        # L'index du reranker est la position du document dans la liste envoyée :
        # l'ancien rang (celui de Qdrant) est donc index + 1.
        print(f"{nouveau_rang:>7}  {resultat['index'] + 1:>6}  {resultat['relevance_score']:>7.4f}  {p['fichier']} p.{p['page']}")


def rechercher(question, k_vecteur=20, k_final=5):
    """Les trois étages : embedding → recherche vectorielle → reranking.

    Renvoie les k_final meilleurs morceaux, chacun avec ses deux scores
    (le cosinus de l'étage 2, le reranking de l'étage 3).
    """
    vecteur, duree_1 = embedder_question(question)
    points, duree_2 = qdrant_rechercher(vecteur, k_vecteur)
    afficher_tableau_vecteur(points)
    resultats, duree_3 = reranker(question, points)
    afficher_tableau_rerank(points, resultats, k_final)
    print()
    print(f"Durées — embedding : {duree_1:.2f} s — Qdrant : {duree_2:.2f} s — reranking : {duree_3:.2f} s")

    gagnants = []
    for resultat in resultats[:k_final]:
        point = points[resultat["index"]]
        payload = point["payload"]
        gagnants.append({
            "fichier": payload["fichier"],
            "titre": payload["titre"],
            "page": payload["page"],
            "morceau": payload["morceau"],
            "texte": payload["texte"],
            "score_cosine": point["score"],
            "score_rerank": resultat["relevance_score"],
        })
    return gagnants


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage : python3 recherche.py « la question »")
    question = " ".join(sys.argv[1:])
    print(f"Question : {question}")
    print(f"Embedding : {EMBED_URL} (modèle {EMBED_MODELE})")
    print(f"Qdrant    : {QDRANT_URL} (collection « {COLLECTION} »)")
    print(f"Reranking : {RERANK_URL}")
    print()

    gagnants = rechercher(question)

    print()
    print(f"LES {len(gagnants)} MEILLEURS MORCEAUX")
    for rang, morceau in enumerate(gagnants, start=1):
        debut = " ".join(morceau["texte"].split())[:90]
        print(f"{rang}. {morceau['fichier']} p.{morceau['page']}")
        print(f"   (cosine {morceau['score_cosine']:.4f} — rerank {morceau['score_rerank']:.4f})")
        print(f"   « {debut}… »")
