"""Connecteur du site « base de connaissance » (adresse dans SITE_URL).

1. robots.txt : respecter les règles « Disallow », trouver le plan du site (« Sitemap: »).
2. sitemap.xml : pour chaque page, garder l'adresse et la date « lastmod ».
3. Télécharger chaque page et garder seulement le texte de la balise <article>,
   sans le menu ni le pied de page.
4. Écrire un document par page dans donnees/documents-site.jsonl.
"""

import json
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

SITE_URL = os.environ.get("SITE_URL", "http://127.0.0.1:8914/kb").rstrip("/")
FICHIER_SORTIE = Path(__file__).resolve().parent / "donnees" / "documents-site.jsonl"


def telecharger(url):
    """Télécharge une adresse et renvoie le corps de la réponse, en texte."""
    with urllib.request.urlopen(url, timeout=30) as reponse:
        return reponse.read().decode("utf-8")


def lire_robots():
    """Lit robots.txt.

    Renvoie (chemins interdits, adresse du plan du site).
    On ne retient que les règles de « User-agent: * », qui s'appliquent à tous.
    """
    interdits, plan, agent = [], None, ""
    for ligne in telecharger(SITE_URL + "/robots.txt").splitlines():
        ligne = ligne.split("#", 1)[0].strip()  # retirer le commentaire éventuel
        if not ligne:
            continue
        cle, _, valeur = ligne.partition(":")
        cle, valeur = cle.strip().lower(), valeur.strip()
        if cle == "user-agent":
            agent = valeur
        elif cle == "disallow" and agent in ("", "*"):
            if valeur:  # un « Disallow: » vide n'interdit rien
                interdits.append(valeur)
        elif cle == "sitemap":
            plan = urllib.parse.urljoin(SITE_URL, valeur)
    return interdits, plan


def est_interdit(url, interdits):
    """Vrai si l'adresse commence par l'un des chemins interdits par robots.txt."""
    chemin = urllib.parse.urlparse(url).path
    return any(chemin.startswith(regle) for regle in interdits)


def sans_espace_noms(noeud):
    """Retire l'espace de noms XML des balises, pour les chercher par nom simple."""
    for element in noeud.iter():
        if "}" in element.tag:
            element.tag = element.tag.split("}", 1)[1]
    return noeud


def lire_sitemap(url):
    """Parcourt le sitemap.xml. Renvoie la liste des (adresse, date lastmod)."""
    racine = sans_espace_noms(ET.fromstring(telecharger(url)))
    pages = []
    for element in racine.iter("url"):
        adresse = element.findtext("loc")
        if adresse:
            pages.append((adresse, element.findtext("lastmod")))
    return pages


class Article(HTMLParser):
    """Lit le HTML d'une page et garde le texte de la balise <article>.

    Le menu (en tête) et le pied de page, qui sont hors de <article>, sont ignorés.
    Le premier <h1> de l'article sert de titre.
    """

    def __init__(self):
        super().__init__()
        self.profondeur = 0  # nombre de balises <article> ouvertes
        self.dans_titre = False
        self.morceaux = []  # texte de l'article
        self.titre = []  # texte du <h1>

    def handle_starttag(self, nom, attributs):
        if nom == "article":
            self.profondeur += 1
        if nom == "h1" and self.profondeur:
            self.dans_titre = True

    def handle_endtag(self, nom):
        if nom == "h1":
            self.dans_titre = False
        if nom == "article" and self.profondeur:
            self.profondeur -= 1

    def handle_data(self, donnees):
        if not self.profondeur:
            return  # hors de <article> : menu, pied de page
        self.morceaux.append(donnees)
        if self.dans_titre:
            self.titre.append(donnees)


def extraire_article(html):
    """Renvoie (titre, texte) d'une page : le contenu de <article>, sans le HTML."""
    analyseur = Article()
    analyseur.feed(html)
    titre = "".join(analyseur.titre).strip()
    # On normalise chaque fragment de texte, puis on les recolle avec une espace :
    # dans le HTML d'origine, il n'y a pas forcément de blanc entre deux balises voisines.
    blocs = (" ".join(morceau.split()) for morceau in analyseur.morceaux)
    return titre, " ".join(bloc for bloc in blocs if bloc)


def identifiant(url):
    """Identifiant du document : « site/ » + nom du fichier, sans son extension."""
    nom = urllib.parse.urlparse(url).path.rsplit("/", 1)[-1]
    if "." in nom:
        nom = nom.rsplit(".", 1)[0]
    return "site/" + nom


def principal():
    interdits, plan = lire_robots()
    if plan is None:
        raise SystemExit("robots.txt sans ligne « Sitemap: » : plan du site introuvable.")
    print(f"Site      : {SITE_URL}")
    print(f"Interdits : {interdits if interdits else 'aucun'}")
    print(f"Sitemap   : {plan}")

    pages = lire_sitemap(plan)
    documents = []
    for numero, (url, dernier_modification) in enumerate(pages, 1):
        if est_interdit(url, interdits):
            print(f"Page {numero}/{len(pages)} : ignorée (robots.txt) — {url}")
            continue
        titre, texte = extraire_article(telecharger(url))
        documents.append({
            "id": identifiant(url),
            "source": "site",
            "url": url,
            "titre": titre,
            "texte": texte,
            "maj": dernier_modification,
            "droits": ["tous"],  # site public : tout le monde peut le lire
        })
        print(f"Page {numero}/{len(pages)} : « {titre} » ({len(texte)} caractères)")

    FICHIER_SORTIE.parent.mkdir(parents=True, exist_ok=True)
    with FICHIER_SORTIE.open("w", encoding="utf-8") as fichier:
        for document in documents:
            fichier.write(json.dumps(document, ensure_ascii=False) + "\n")

    print(f"\n{len(documents)} documents écrits dans {FICHIER_SORTIE}")
    if documents:
        debut = dict(documents[0])  # afficher le premier, avec le texte raccourci
        if len(debut["texte"]) > 100:
            debut["texte"] = debut["texte"][:100] + "…"
        print("Début du premier document :")
        print(json.dumps(debut, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    principal()
