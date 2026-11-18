#!/usr/bin/env python3
"""Un pseudo-Qdrant : la petite partie de l'API REST de Qdrant dont l'atelier se sert, en Python standard.

Pour les postes où l'on ne peut pas installer Qdrant. Les programmes de l'atelier (`projet/ingestion.py`,
`projet/recherche.py`) s'en servent sans changer une ligne : même port par défaut (8803 dans l'atelier), mêmes routes,
mêmes réponses JSON.

Ce qu'il sait faire :
- GET    /                                     version (le serveur répond-il ?)
- GET    /collections                          liste des collections
- PUT    /collections/{nom}                    créer : {"vectors": {"size": 4096, "distance": "Cosine"}}
- GET    /collections/{nom}                    décrire (dont points_count) ; 404 si elle n'existe pas
- DELETE /collections/{nom}                    supprimer
- PUT    /collections/{nom}/points             ajouter ou remplacer : {"points": [{"id", "vector", "payload"}]}
- POST   /collections/{nom}/points/query       chercher : {"query": [vecteur], "limit": k, "with_payload": true}
- POST   /collections/{nom}/points/search      l'ancienne forme : {"vector": [...], "limit": k}
- POST   /collections/{nom}/points/scroll      parcourir : {"limit": n, "offset": id}
- POST   /collections/{nom}/points/count       compter
- POST   /collections/{nom}/points/delete      supprimer : {"points": [ids]} ou {"filter": {...}} (filtre vide : tout)
- un filtre simple dans query, search, scroll et count : {"must": [{"key": "...", "match": {"value": ...}}]}
  ou {"match": {"any": [...]}} ; aussi "should" et "must_not".

Ce qu'il ne fait pas : pas d'index HNSW (la recherche compare la question à TOUS les vecteurs, ce qui reste rapide
jusqu'à quelques dizaines de milliers de morceaux), pas de vecteurs nommés ni creux, pas de quantification, pas de
gRPC, pas de clé d'API. Une requête qu'il ne comprend pas reçoit une erreur 400 qui le dit, jamais une réponse fausse.

Les collections sont gardées dans un dossier (--donnees) : pour chacune, sa configuration, ses payloads (une ligne
JSON par point) et ses vecteurs en float32. Un ajout s'écrit à la fin des fichiers. On peut donc arrêter le serveur
entre l'ingestion et la recherche sans tout recalculer.

Usage : python3 services-simules/pseudo-qdrant.py [--port 8803] [--donnees services-simules/pseudo-qdrant-donnees]

Écrit par Claude (outillage), pas par OpenCode.
"""
import argparse, json, math, operator, os, re, threading, time
from array import array
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlsplit

VERSION = "pseudo-qdrant 0.1 (sous-ensemble de l'API REST de Qdrant 1.x)"
DISTANCES = ("Cosine", "Dot", "Euclid")

verrou = threading.Lock()
collections = {}   # nom -> {"size", "distance", "points": {id: {"vector", "payload"}}}
DOSSIER = None
operation = 0


class Erreur(Exception):
    """Une erreur rendue au client, avec son code HTTP (le texte suit la forme des messages de Qdrant)."""
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


# --- Les calculs -------------------------------------------------------------------------------------------------

def normaliser(vecteur):
    """Ramène le vecteur à une longueur 1 : le cosinus devient un simple produit scalaire (Qdrant fait pareil)."""
    norme = math.sqrt(sum(x * x for x in vecteur))
    return [x / norme for x in vecteur] if norme else list(vecteur)


def score(distance, requete, vecteur):
    """Le score d'un point : plus grand = plus proche pour Cosine et Dot ; pour Euclid, la distance (plus petit = plus proche)."""
    if distance == "Euclid":
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(requete, vecteur)))
    return math.fsum(map(operator.mul, requete, vecteur))


def valeur(payload, cle):
    """Lit une clé du payload ; « a.b » descend dans les objets."""
    for morceau in cle.split("."):
        if not isinstance(payload, dict) or morceau not in payload:
            return None
        payload = payload[morceau]
    return payload


def condition_vraie(payload, condition):
    """Une condition {"key", "match": {"value"} | {"any"} | {"text"}} ; une valeur liste vaut si un de ses éléments convient."""
    if "must" in condition or "should" in condition or "must_not" in condition:
        return filtre_vrai(payload, condition)
    if "key" not in condition or "match" not in condition:
        raise Erreur(400, f"Format error in JSON body: condition non prise en charge par le pseudo-Qdrant : {json.dumps(condition)}")
    lu = valeur(payload, condition["key"])
    lus = lu if isinstance(lu, list) else [lu]
    m = condition["match"]
    if "value" in m:
        return m["value"] in lus
    if "any" in m:
        return any(v in lus for v in m["any"])
    if "except" in m:
        return not any(v in lus for v in m["except"])
    if "text" in m:
        return any(isinstance(v, str) and m["text"] in v for v in lus)
    raise Erreur(400, f"Format error in JSON body: match non pris en charge : {json.dumps(m)}")


def filtre_vrai(payload, filtre):
    """must : toutes vraies ; should : au moins une ; must_not : aucune."""
    if not filtre:
        return True
    inconnues = set(filtre) - {"must", "should", "must_not"}
    if inconnues:
        raise Erreur(400, f"Format error in JSON body: clé de filtre non prise en charge : {sorted(inconnues)}")
    liste = lambda c: c if isinstance(c, list) else [c]
    if "must" in filtre and not all(condition_vraie(payload, c) for c in liste(filtre["must"])):
        return False
    if filtre.get("should") and not any(condition_vraie(payload, c) for c in liste(filtre["should"])):
        return False
    if "must_not" in filtre and any(condition_vraie(payload, c) for c in liste(filtre["must_not"])):
        return False
    return True


def choisir_payload(payload, with_payload):
    """with_payload : true, false, ou une liste de clés à garder."""
    if with_payload is True:
        return payload
    if isinstance(with_payload, list):
        return {k: v for k, v in payload.items() if k in with_payload}
    return None


# --- Le stockage -------------------------------------------------------------------------------------------------

def fichiers(nom):
    """Trois fichiers par collection : la configuration, les identifiants et payloads (une ligne JSON par point),
    les vecteurs en binaire (float32, dans le même ordre que les lignes)."""
    base = os.path.join(DOSSIER, nom)
    return base + ".config.json", base + ".points.jsonl", base + ".vecteurs.f32"


def sauver_config(nom):
    c = collections[nom]
    config, points, vecteurs = fichiers(nom)
    with open(config, "w", encoding="utf-8") as f:
        json.dump({"size": c["size"], "distance": c["distance"]}, f)
    open(points, "w").close()
    open(vecteurs, "wb").close()


def sauver_points(nom, nouveaux):
    """Ajoute les points à la fin des fichiers, sans réécrire le reste : un ajout coûte la taille du lot,
    pas celle de la collection. Un point remplacé laisse son ancienne version dans le fichier ; à la relecture,
    la dernière version gagne."""
    _, points, vecteurs = fichiers(nom)
    with open(points, "a", encoding="utf-8") as fp, open(vecteurs, "ab") as fv:
        for i, p in nouveaux:
            fp.write(json.dumps({"id": i, "payload": p["payload"]}, ensure_ascii=False) + "\n")
            p["vector"].tofile(fv)


def charger():
    for nom_fichier in sorted(os.listdir(DOSSIER)):
        if not nom_fichier.endswith(".config.json"):
            continue
        nom = nom_fichier[:-len(".config.json")]
        config, points, vecteurs = fichiers(nom)
        with open(config, encoding="utf-8") as f:
            d = json.load(f)
        c = {"size": d["size"], "distance": d["distance"], "points": {}}
        with open(points, encoding="utf-8") as fp, open(vecteurs, "rb") as fv:
            for ligne in fp:
                lu = json.loads(ligne)
                vecteur = array("f")
                vecteur.fromfile(fv, d["size"])
                c["points"][lu["id"]] = {"vector": vecteur, "payload": lu["payload"]}
        collections[nom] = c
        print(f"collection « {nom} » relue : {len(c['points'])} points de {d['size']} dimensions", flush=True)


def collection(nom):
    if nom not in collections:
        raise Erreur(404, f"Not found: Collection `{nom}` doesn't exist!")
    return collections[nom]


# --- Les routes --------------------------------------------------------------------------------------------------

def creer(nom, corps):
    v = (corps or {}).get("vectors")
    if not isinstance(v, dict) or "size" not in v or "distance" not in v:
        raise Erreur(400, 'Format error in JSON body: attendu {"vectors": {"size": N, "distance": "Cosine"}} (vecteurs nommés non pris en charge)')
    if v["distance"] not in DISTANCES:
        raise Erreur(400, f"Format error in JSON body: distance inconnue « {v['distance']} », attendu {DISTANCES}")
    if nom in collections:
        raise Erreur(409, f"Wrong input: Collection `{nom}` already exists!")
    collections[nom] = {"size": int(v["size"]), "distance": v["distance"], "points": {}}
    sauver_config(nom)
    return True


def decrire(nom):
    c = collection(nom)
    n = len(c["points"])
    return {"status": "green", "optimizer_status": "ok", "indexed_vectors_count": 0, "points_count": n,
            "segments_count": 1,
            "config": {"params": {"vectors": {"size": c["size"], "distance": c["distance"]}}},
            "payload_schema": {}}


def supprimer(nom):
    collection(nom)
    del collections[nom]
    for f in fichiers(nom):
        os.remove(f)
    return True


def ajouter(nom, corps):
    global operation
    c = collection(nom)
    points = (corps or {}).get("points")
    if not isinstance(points, list):
        raise Erreur(400, 'Format error in JSON body: attendu {"points": [{"id", "vector", "payload"}]} (la forme « batch » n\'est pas prise en charge)')
    for p in points:
        if not isinstance(p.get("id"), (int, str)) or isinstance(p.get("id"), bool):
            raise Erreur(400, f"Format error in JSON body: identifiant invalide {p.get('id')!r} (entier ou UUID)")
        vecteur = p.get("vector")
        if not isinstance(vecteur, list):
            raise Erreur(400, "Format error in JSON body: « vector » doit être une liste de nombres (vecteurs nommés non pris en charge)")
        if len(vecteur) != c["size"]:
            raise Erreur(400, f"Wrong input: Vector dimension error: expected dim: {c['size']}, got {len(vecteur)}")
    nouveaux = []
    for p in points:
        vecteur = [float(x) for x in p["vector"]]
        if c["distance"] == "Cosine":
            vecteur = normaliser(vecteur)
        # En mémoire comme sur disque, un vecteur est un tableau de float32 : 4 octets par valeur,
        # là où une liste Python en prend environ 32.
        point = {"vector": array("f", vecteur), "payload": p.get("payload") or {}}
        c["points"][p["id"]] = point
        nouveaux.append((p["id"], point))
    sauver_points(nom, nouveaux)
    operation += 1
    return {"operation_id": operation, "status": "completed"}


def chercher(nom, corps, champ):
    """Compare la requête à tous les points (pas d'index), garde les meilleurs."""
    c = collection(nom)
    corps = corps or {}
    requete = corps.get(champ)
    if isinstance(requete, dict) and "nearest" in requete:
        requete = requete["nearest"]
    if not isinstance(requete, list):
        raise Erreur(400, f"Format error in JSON body: « {champ} » doit être un vecteur (liste de nombres) ; requêtes par identifiant, fusion et vecteurs nommés non prises en charge")
    if len(requete) != c["size"]:
        raise Erreur(400, f"Wrong input: Vector dimension error: expected dim: {c['size']}, got {len(requete)}")
    requete = [float(x) for x in requete]
    if c["distance"] == "Cosine":
        requete = normaliser(requete)
    limite = int(corps.get("limit", 10))
    decalage = int(corps.get("offset", 0))
    seuil = corps.get("score_threshold")
    filtre = corps.get("filter")
    trouves = []
    for i, p in c["points"].items():
        if filtre and not filtre_vrai(p["payload"], filtre):
            continue
        s = score(c["distance"], requete, p["vector"])
        if seuil is not None and (s > seuil if c["distance"] == "Euclid" else s < seuil):
            continue
        trouves.append((s, i, p))
    trouves.sort(key=lambda t: t[0], reverse=c["distance"] != "Euclid")
    with_payload = corps.get("with_payload", False)
    with_vector = corps.get("with_vector", corps.get("with_vectors", False))
    return [{"id": i, "version": 0, "score": s, "payload": choisir_payload(p["payload"], with_payload),
             "vector": list(p["vector"]) if with_vector else None}
            for s, i, p in trouves[decalage:decalage + limite]]


def parcourir(nom, corps):
    c = collection(nom)
    corps = corps or {}
    filtre = corps.get("filter")
    ids = sorted(c["points"], key=lambda i: (isinstance(i, str), i))
    if corps.get("offset") is not None:
        ids = [i for i in ids if (isinstance(i, str), i) >= (isinstance(corps["offset"], str), corps["offset"])]
    ids = [i for i in ids if not filtre or filtre_vrai(c["points"][i]["payload"], filtre)]
    limite = int(corps.get("limit", 10))
    with_payload = corps.get("with_payload", True)
    with_vector = corps.get("with_vector", corps.get("with_vectors", False))
    page = [{"id": i, "payload": choisir_payload(c["points"][i]["payload"], with_payload),
             "vector": list(c["points"][i]["vector"]) if with_vector else None} for i in ids[:limite]]
    return {"points": page, "next_page_offset": ids[limite] if len(ids) > limite else None}


def supprimer_points(nom, corps):
    """Supprime des points par identifiants ou par filtre ({} : tous). Réécrit les fichiers de la collection."""
    global operation
    c = collection(nom)
    corps = corps or {}
    if "points" in corps:
        ids = set(corps["points"])
    elif "filter" in corps:
        ids = {i for i, p in c["points"].items() if filtre_vrai(p["payload"], corps["filter"])}
    else:
        raise Erreur(400, 'Format error in JSON body: attendu {"points": [...]} ou {"filter": {...}}')
    for i in ids:
        c["points"].pop(i, None)
    reste = list(c["points"].items())
    sauver_config(nom)          # repart de fichiers vides…
    sauver_points(nom, reste)   # …et réécrit les points restants
    operation += 1
    return {"operation_id": operation, "status": "completed"}


def compter(nom, corps):
    c = collection(nom)
    filtre = (corps or {}).get("filter")
    return {"count": sum(1 for p in c["points"].values() if not filtre or filtre_vrai(p["payload"], filtre))}


ROUTES = [
    ("GET", r"/", lambda m, b: {"title": "qdrant - vector search engine", "version": VERSION}),
    ("GET", r"/collections", lambda m, b: {"collections": [{"name": n} for n in sorted(collections)]}),
    ("PUT", r"/collections/([^/]+)", lambda m, b: creer(m[1], b)),
    ("GET", r"/collections/([^/]+)", lambda m, b: decrire(m[1])),
    ("DELETE", r"/collections/([^/]+)", lambda m, b: supprimer(m[1])),
    ("PUT", r"/collections/([^/]+)/points", lambda m, b: ajouter(m[1], b)),
    ("POST", r"/collections/([^/]+)/points/query", lambda m, b: {"points": chercher(m[1], b, "query")}),
    ("POST", r"/collections/([^/]+)/points/search", lambda m, b: chercher(m[1], b, "vector")),
    ("POST", r"/collections/([^/]+)/points/scroll", lambda m, b: parcourir(m[1], b)),
    ("POST", r"/collections/([^/]+)/points/count", lambda m, b: compter(m[1], b)),
    ("POST", r"/collections/([^/]+)/points/delete", lambda m, b: supprimer_points(m[1], b)),
]


class Gestionnaire(BaseHTTPRequestHandler):
    def traiter(self):
        debut = time.monotonic()
        chemin = urlsplit(self.path).path.rstrip("/") or "/"
        n = int(self.headers.get("Content-Length") or 0)
        try:
            try:
                corps = json.loads(self.rfile.read(n)) if n else None
            except json.JSONDecodeError as e:
                raise Erreur(400, f"Format error in JSON body: {e}")
            for methode, motif, action in ROUTES:
                m = re.fullmatch(motif, chemin)
                if m and methode == self.command:
                    with verrou:
                        resultat = action(m, corps)
                    code, reponse = 200, {"result": resultat, "status": "ok"}
                    break
            else:
                raise Erreur(404, f"pseudo-Qdrant : route non prise en charge : {self.command} {chemin}")
        except Erreur as e:
            code, reponse = e.code, {"status": {"error": str(e)}}
        duree = time.monotonic() - debut
        reponse["time"] = round(duree, 6)
        brut = json.dumps(reponse, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(brut)))
        self.end_headers()
        self.wfile.write(brut)
        print(f"{self.command} {chemin} -> {code} en {duree * 1000:.1f} ms", flush=True)

    do_GET = do_PUT = do_POST = do_DELETE = traiter

    def log_message(self, *args):
        pass  # une ligne par requête suffit, écrite dans traiter()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--port", type=int, default=8803)
    p.add_argument("--hote", default="127.0.0.1")
    p.add_argument("--donnees", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "pseudo-qdrant-donnees"))
    A = p.parse_args()
    DOSSIER = A.donnees
    os.makedirs(DOSSIER, exist_ok=True)
    charger()
    print(f"pseudo-Qdrant sur http://{A.hote}:{A.port}, données dans {DOSSIER}", flush=True)
    ThreadingHTTPServer((A.hote, A.port), Gestionnaire).serve_forever()
