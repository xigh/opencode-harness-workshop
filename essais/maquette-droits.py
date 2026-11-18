"""Essai sur les droits de lecture de la maquette RAG (code d'OpenCode inchangé).

1. Copie de maquette/ dans journal/essai-maquette-droits/ (la maquette n'est pas touchée).
2. Ingestion Confluence avec un compte membre du groupe « secu » (en-tête X-Groupes
   du simulateur, ajouté autour de charger_json sans modifier source_confluence.py).
3. Réindexation dans la copie.
4. Mêmes questions posées avec deux profils : sans « secu », puis avec.
"""
import json, os, shutil, subprocess, sys, time
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
COPIE = RACINE / "journal" / "essai-maquette-droits"
ETAPE = RACINE / "journal" / "ETAPE"

QUESTIONS = [
    "Quels comptes de service existent et qui les détient ?",
    "Qui détient le compte svc-sauvegarde ?",
]
PROFILS = {
    "sans-secu": "tous,equipe:DSI - Infrastructure",
    "avec-secu": "tous,equipe:DSI - Infrastructure,secu",
}

PATCH = """
import source_confluence as s
orig = s.charger_json
def charger_json(url):
    import urllib.request, json
    r = urllib.request.Request(url, headers={"Authorization": f"Bearer {s.JETON}", "X-Groupes": "secu"})
    with urllib.request.urlopen(r, timeout=30) as rep:
        return json.loads(rep.read().decode("utf-8"))
s.charger_json = charger_json
s.principal()
"""


def lancer(args, env=None, etape=None):
    if etape:
        ETAPE.write_text(etape, encoding="utf-8")
    print(f"\n$ {' '.join(args)}", flush=True)
    t = time.time()
    r = subprocess.run(args, cwd=COPIE, env={**os.environ, **(env or {})}, capture_output=True, text=True)
    print(r.stdout, r.stderr, sep="\n", flush=True)
    print(f"[code {r.returncode}, {time.time() - t:.1f} s]", flush=True)
    return r


def main():
    if COPIE.exists():
        shutil.rmtree(COPIE)
    shutil.copytree(RACINE / "maquette", COPIE, ignore=shutil.ignore_patterns("__pycache__", "index.json", "evaluation.json"))
    lancer([sys.executable, "-c", PATCH], etape="maquette-essai-droits-ingestion")
    for l in (COPIE / "donnees" / "documents-confluence.jsonl").read_text(encoding="utf-8").splitlines():
        d = json.loads(l)
        print(" ", d["id"], d["droits"])
    lancer([sys.executable, "index.py"], etape="maquette-essai-droits-index")
    for nom, droits in PROFILS.items():
        for q in QUESTIONS:
            print(f"\n===== profil {nom} ({droits}) : {q}")
            lancer([sys.executable, "assistant.py", q], env={"UTILISATEUR_DROITS": droits}, etape=f"maquette-essai-droits-{nom}")
    ETAPE.write_text("", encoding="utf-8")
    print("fin essai droits")


if __name__ == "__main__":
    main()
