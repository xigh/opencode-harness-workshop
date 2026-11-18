#!/usr/bin/env python3
"""Un pseudo-reranker : la route /v1/rerank de llama-server, dont la note vient d'un modèle de chat.

Pour les postes où l'on n'a pas de vrai reranker (un « cross-encoder » comme bge-reranker-v2-m3 ou
Qwen3-Reranker) et où l'on n'a accès qu'à un modèle de chat compatible OpenAI, chez un fournisseur ou en local.
`projet/recherche.py` s'en sert sans changer une ligne : RERANK_URL=http://127.0.0.1:8802/v1.

Pour chaque document (une requête par document, plusieurs en parallèle), deux méthodes :
- « oui-non » (par défaut) : le modèle répond oui ou non ; le score est la probabilité de « oui », lue dans les
  logprobs du premier jeton. Il faut un serveur qui renvoie les logprobs (Scaleway et llama-server le font) ;
- « note » : le modèle écrit une note de 0 à 10.
La réponse suit le format de llama-server : {"results": [{"index": 3, "relevance_score": 0.9}, ...]}, du plus
pertinent au moins pertinent.

Ce n'est pas un vrai reranker, et cela se voit :
- c'est plus lent et plus cher : une requête au modèle de chat par document (20 pour une question de recherche.py) ;
- avec la méthode « note », le score est grossier : 11 valeurs possibles, beaucoup d'ex aequo (départagés par
  l'ordre reçu, celui de la recherche vectorielle) ;
- la note dépend du modèle et de la consigne ; un modèle qui « réfléchit » avant de répondre coûte encore plus.
On le garde pour comparer avec un vrai reranker, pas pour la production.

Configuration (variables d'environnement, comme le reste de l'atelier) :
- RERANK_LLM_URL   l'adresse du modèle de chat (défaut : LLM_URL, sinon http://127.0.0.1:8800/v1)
- RERANK_LLM_MODELE le modèle (défaut : LLM_MODELE, sinon qwen3.8-27b)
- RERANK_LLM_CLE    la clé d'API (défaut : LLM_CLE ; facultative, jamais affichée)

Usage : python3 services-simules/pseudo-reranker.py [--port 8802] [--paralleles 8] [--methode oui-non|note]

Écrit par Claude (outillage), pas par OpenCode.
"""
import argparse, json, math, os, re, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlsplit

URL = os.environ.get("RERANK_LLM_URL") or os.environ.get("LLM_URL") or "http://127.0.0.1:8800/v1"
MODELE = os.environ.get("RERANK_LLM_MODELE") or os.environ.get("LLM_MODELE") or "qwen3.8-27b"
CLE = os.environ.get("RERANK_LLM_CLE") or os.environ.get("LLM_CLE") or ""

CONSIGNE_NOTE = (
    "Tu notes la pertinence d'un passage de document pour une question. "
    "Réponds par un seul nombre entier de 0 à 10, sans rien d'autre : "
    "10 si le passage répond directement à la question, 5 s'il en parle sans y répondre, 0 s'il n'a aucun rapport."
)
CONSIGNE_OUI_NON = (
    "Tu juges si un passage de document aide à répondre à une question. "
    "Réponds seulement par oui ou par non."
)
OUI = {"oui", "yes"}
NON = {"non", "no"}


def demander(question, document, methode):
    """Une requête au modèle de chat pour un document ; renvoie le JSON reçu."""
    consigne, fin = (CONSIGNE_NOTE, "Note de 0 à 10 :") if methode == "note" else (CONSIGNE_OUI_NON, "Oui ou non :")
    corps = {
        "model": MODELE,
        "messages": [
            {"role": "system", "content": consigne},
            {"role": "user", "content": f"Question : {question}\n\nPassage :\n{document}\n\n{fin}"},
        ],
        "temperature": 0,
        "max_tokens": 8 if methode == "note" else 2,
        # Pour les modèles qui réfléchissent avant de répondre (Qwen3, Gemma 4), on coupe la réflexion : sinon les
        # jetons partent dans le raisonnement et la réponse arrive vide. llama-server lit chat_template_kwargs ;
        # Scaleway l'ignore et lit reasoning_effort (constaté le 18/11/2026). Un serveur ignore le champ qu'il ne connaît pas.
        "chat_template_kwargs": {"enable_thinking": False},
        "reasoning_effort": "none",
    }
    if methode == "oui-non":
        corps["logprobs"] = True
        corps["top_logprobs"] = 10
    entetes = {"Content-Type": "application/json"}
    if CLE:
        entetes["Authorization"] = "Bearer " + CLE
    demande = urllib.request.Request(URL + "/chat/completions", data=json.dumps(corps).encode("utf-8"),
                                     method="POST", headers=entetes)
    with urllib.request.urlopen(demande, timeout=120) as reponse:
        return json.loads(reponse.read().decode("utf-8"))


def noter(question, document, methode):
    """Renvoie le score (0 à 1), le texte reçu et les compteurs de jetons.

    Méthode « note » : le modèle écrit une note de 0 à 10, divisée par 10.
    Méthode « oui-non » : on lit les probabilités du premier jeton de la réponse (logprobs) et on renvoie
    P(oui) / (P(oui) + P(non)). C'est le principe de Qwen3-Reranker (logit de « yes » contre celui de « no ») :
    un score continu, presque sans ex aequo, là où la note n'a que 11 valeurs.
    """
    recu = demander(question, document, methode)
    choix = recu["choices"][0]
    texte = choix["message"].get("content") or ""
    usage = recu.get("usage") or {}
    if methode == "note":
        trouve = re.search(r"\d+", texte)
        return (min(10, int(trouve.group())) / 10 if trouve else 0.0), texte, usage  # sans nombre : 0, visible dans le journal
    premiers = ((choix.get("logprobs") or {}).get("content") or [{}])[0].get("top_logprobs")
    if not premiers:
        raise ValueError("le serveur ne renvoie pas les logprobs : relancer avec --methode note")
    p_oui = sum(math.exp(t["logprob"]) for t in premiers if t["token"].strip().lower() in OUI)
    p_non = sum(math.exp(t["logprob"]) for t in premiers if t["token"].strip().lower() in NON)
    if p_oui + p_non == 0:
        return 0.0, texte, usage  # ni oui ni non parmi les jetons les plus probables : se voit dans le journal
    return p_oui / (p_oui + p_non), texte, usage


def reranker(corps, paralleles, methode):
    question = corps.get("query")
    documents = corps.get("documents")
    if not isinstance(question, str) or not isinstance(documents, list):
        raise ValueError('attendu {"query": "...", "documents": ["...", ...]}')
    documents = [d if isinstance(d, str) else json.dumps(d, ensure_ascii=False) for d in documents]
    with ThreadPoolExecutor(max_workers=paralleles) as groupe:
        scores = list(groupe.map(lambda d: noter(question, d, methode), documents))
    for i, (score, texte, _) in enumerate(scores):
        print(f"  document {i:2d} : score {score:.4f}  (reçu : {texte.strip()[:20]!r})", flush=True)
    ordre = sorted(range(len(documents)), key=lambda i: -scores[i][0])  # tri stable : à score égal, l'ordre reçu
    top_n = corps.get("top_n") or len(documents)
    entree = sum(u.get("prompt_tokens", 0) for _, _, u in scores)
    sortie = sum(u.get("completion_tokens", 0) for _, _, u in scores)
    return {"model": MODELE, "object": "list",
            "usage": {"prompt_tokens": entree, "total_tokens": entree + sortie},
            "results": [{"index": i, "relevance_score": scores[i][0]} for i in ordre[:top_n]]}


class Gestionnaire(BaseHTTPRequestHandler):
    def do_POST(self):
        debut = time.monotonic()
        chemin = urlsplit(self.path).path.rstrip("/")
        try:
            if chemin not in ("/v1/rerank", "/rerank", "/v1/reranking", "/reranking"):
                code, reponse = 404, {"error": {"message": f"pseudo-reranker : route non prise en charge : {chemin}"}}
            else:
                n = int(self.headers.get("Content-Length") or 0)
                corps = json.loads(self.rfile.read(n) or b"{}")
                print(f"rerank : {len(corps.get('documents') or [])} documents, modèle {MODELE}", flush=True)
                code, reponse = 200, reranker(corps, A.paralleles, A.methode)
        except (ValueError, json.JSONDecodeError) as e:
            code, reponse = 400, {"error": {"message": str(e)}}
        except urllib.error.HTTPError as e:
            code, reponse = 502, {"error": {"message": f"le modèle de chat a répondu {e.code} : {e.read()[:300].decode('utf-8', 'replace')}"}}
        except (urllib.error.URLError, TimeoutError) as e:
            code, reponse = 502, {"error": {"message": f"le modèle de chat ne répond pas ({URL}) : {e}"}}
        brut = json.dumps(reponse, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(brut)))
        self.end_headers()
        self.wfile.write(brut)
        print(f"POST {chemin} -> {code} en {time.monotonic() - debut:.2f} s", flush=True)

    def do_GET(self):
        brut = json.dumps({"status": "ok", "pseudo_reranker": True, "modele": MODELE}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(brut)))
        self.end_headers()
        self.wfile.write(brut)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--port", type=int, default=8802)
    p.add_argument("--hote", default="127.0.0.1")
    p.add_argument("--paralleles", type=int, default=8, help="requêtes envoyées en même temps au modèle de chat")
    p.add_argument("--methode", choices=("oui-non", "note"), default="oui-non",
                   help="oui-non : probabilité de « oui » lue dans les logprobs (score continu) ; note : note de 0 à 10 écrite par le modèle")
    A = p.parse_args()
    print(f"pseudo-reranker sur http://{A.hote}:{A.port}/v1/rerank, méthode {A.methode}, modèle {MODELE} ({URL})", flush=True)
    ThreadingHTTPServer((A.hote, A.port), Gestionnaire).serve_forever()
