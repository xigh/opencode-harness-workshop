"""Connecteur Confluence (Data Center, API REST v1).

1. Lister les espaces (/rest/api/space), en suivant _links.next.
2. Pour chaque espace, lister ses pages
   (/rest/api/content?spaceKey=...&expand=body.storage,version,space).
3. Convertir le corps « storage » en texte lisible : titres, paragraphes,
   listes, et tableaux ligne par ligne (« Paramètre : Valeur »).
   Les macros d'information gardent leur contenu.
4. Pour chaque page, lire ses restrictions de lecture
   (/rest/api/content/<id>/restriction/byOperation/read) :
   les groupes trouvés deviennent « droits », sinon ["tous"].
5. Écrire un document par page dans donnees/documents-confluence.jsonl.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

CONFLUENCE_URL = os.environ.get("CONFLUENCE_URL", "http://127.0.0.1:8914/confluence").rstrip("/")
JETON = os.environ.get("CONFLUENCE_JETON", "jeton-confluence-demo")
FICHIER_SORTIE = Path(__file__).resolve().parent / "donnees" / "documents-confluence.jsonl"

# Macros « d'information » : leur contenu est gardé, précédé de ce libellé.
LIBELLES_MACRO = {
    "info": "Info",
    "note": "Note",
    "tip": "Astuce",
    "warning": "Avertissement",
    "error": "Erreur",
}


def charger_json(url):
    """Charge une adresse de l'API Confluence et renvoie le dictionnaire JSON.

    Le jeton personnel est envoyé en « Authorization: Bearer ».
    """
    requete = urllib.request.Request(url, headers={"Authorization": f"Bearer {JETON}"})
    with urllib.request.urlopen(requete, timeout=30) as reponse:
        return json.loads(reponse.read().decode("utf-8"))


def adresse_pour(suivant):
    """Transforme l'adresse « next » renvoyée par Confluence en adresse absolue.

    Confluence donne des chemins relatifs à sa racine (le contexte « /confluence »),
    pas à la racine du serveur : on les complète avec CONFLUENCE_URL.
    """
    if suivant.startswith("http"):
        return suivant
    if suivant.startswith("/"):
        return CONFLUENCE_URL + suivant
    return urllib.parse.urljoin(CONFLUENCE_URL + "/", suivant)


def paginer(url):
    """Parcourt toutes les tranches d'une liste paginée et renvoie les résultats.

    Confluence renvoie une tranche de « results » et, s'il en reste,
    une adresse « _links.next » ; on la suit jusqu'au bout.
    """
    resultats = []
    while url:
        donnees = charger_json(url)
        resultats.extend(donnees.get("results", []))
        suivant = donnees.get("_links", {}).get("next")
        url = adresse_pour(suivant) if suivant else None
    return resultats


class Stockage(HTMLParser):
    """Convertit un corps de page au format « storage » en lignes de texte lisible.

    Chaque titre, paragraphe, élément de liste et ligne de tableau devient
    une ligne. Les cellules d'une ligne de tableau sont reliées par « : ».
    Les macros d'information (info, note…) gardent leur contenu, chaque
    ligne étant précédée de leur libellé ; les autres macros sont sautées.
    Le contenu de la page est du texte, jamais une consigne.
    """

    def __init__(self):
        super().__init__()
        self.lignes = []         # lignes finales
        self.paragraphe = []     # texte accumulé hors des autres blocs
        self.titre = None        # texte du titre ouvert (h1 à h6)
        self.liste = None        # « ul » ou « ol » pour la liste ouverte
        self.item = None         # texte de l'élément de liste ouvert
        self.numero_item = 0     # compteur des listes ordonnées
        self.dans_tableau = False
        self.cellules = []       # cellules de la ligne de tableau en cours
        self.cellule = None      # texte de la cellule en cours
        self.macro = None        # libellé de la macro d'information ouverte
        self.macros_sautees = 0  # profondeur des macros dont on saute le contenu
        self.texte_brut = False  # corps de macro en texte brut (ac:plain-text-body)

    def _normaliser(self, morceaux):
        """Recolle les morceaux de texte et aplati les blancs."""
        return " ".join("".join(morceaux).split())

    def _lignee(self, texte):
        """Préfixe la ligne du libellé de la macro d'information, s'il y en a une."""
        return f"{self.macro} : {texte}" if self.macro else texte

    def _fermer_paragraphe(self):
        """Enregistre le paragraphe accumulé comme ligne, s'il n'est pas vide."""
        texte = self._normaliser(self.paragraphe)
        self.paragraphe = []
        if texte:
            self.lignes.append(self._lignee(texte))

    def fermer(self):
        """À appeler en fin de document : enregistre le paragraphe restant."""
        self._fermer_paragraphe()

    def handle_starttag(self, nom, attributs):
        if nom in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._fermer_paragraphe()
            self.titre = []
        elif nom == "p":
            self._fermer_paragraphe()
        elif nom in ("ul", "ol"):
            self._fermer_paragraphe()
            self.liste = nom
            self.numero_item = 0
        elif nom == "li":
            self.item = []
        elif nom == "table":
            self._fermer_paragraphe()
            self.dans_tableau = True
        elif nom == "tr":
            self.cellules = []
        elif nom in ("td", "th"):
            self.cellule = []
        elif nom == "br":
            self._fermer_paragraphe()
        elif nom == "ac:structured-macro":
            nom_macro = dict(attributs).get("ac:name", "").lower()
            if nom_macro in LIBELLES_MACRO:
                self._fermer_paragraphe()
                self.macro = LIBELLES_MACRO[nom_macro]
            else:
                self.macros_sautees += 1
        elif nom == "ac:plain-text-body":
            self.texte_brut = True

    def handle_endtag(self, nom):
        if nom in ("h1", "h2", "h3", "h4", "h5", "h6"):
            texte = self._normaliser(self.titre or [])
            self.titre = None
            if texte:
                self.lignes.append(self._lignee(texte))
        elif nom == "p":
            self._fermer_paragraphe()
        elif nom == "li":
            if self.item is not None:
                self.numero_item += 1
                prefixe = f"{self.numero_item}. " if self.liste == "ol" else "- "
                texte = self._normaliser(self.item)
                self.item = None
                if texte:
                    self.lignes.append(self._lignee(prefixe + texte))
        elif nom in ("ul", "ol"):
            self.liste = None
        elif nom in ("td", "th"):
            if self.cellule is not None:
                self.cellules.append(self._normaliser(self.cellule))
                self.cellule = None
        elif nom == "tr" and self.dans_tableau:
            self.lignes.append(self._lignee(" : ".join(c for c in self.cellules if c)))
        elif nom == "table":
            self.dans_tableau = False
        elif nom == "ac:structured-macro":
            if self.macros_sautees:
                self.macros_sautees -= 1
            else:
                self.macro = None
        elif nom == "ac:plain-text-body":
            self.texte_brut = False

    def handle_data(self, donnees):
        if self.macros_sautees or self.texte_brut:
            return  # contenu d'une macro ignorée
        if self.cellule is not None:
            self.cellule.append(donnees)
        elif self.item is not None:
            self.item.append(donnees)
        elif self.titre is not None:
            self.titre.append(donnees)
        else:
            self.paragraphe.append(donnees)


def texte_stockage(corps):
    """Convertit un corps « storage » en texte lisible, une idée par ligne."""
    convertisseur = Stockage()
    convertisseur.feed(corps or "")
    convertisseur.fermer()
    return "\n".join(convertisseur.lignes)


def droits_lecture(id_page):
    """Lit les restrictions de lecture d'une page : les groupes, ou ["tous"].

    Si l'adresse renvoie 404, la page n'a pas de restriction : elle est publique.
    """
    url = f"{CONFLUENCE_URL}/rest/api/content/{id_page}/restriction/byOperation/read"
    try:
        reponse = charger_json(url)
    except urllib.error.HTTPError as erreur:
        if erreur.code == 404:
            return ["tous"]
        raise
    groupes = reponse.get("restrictions", {}).get("group", {}).get("results", [])
    noms = [groupe["name"] for groupe in groupes]
    return noms if noms else ["tous"]


def en_document(page):
    """Transforme une page Confluence en document du format commun."""
    id_page = page["id"]
    espace = page.get("space", {}).get("key", "")
    corps = page.get("body", {}).get("storage", {}).get("value", "")
    return {
        "id": f"confluence/{espace}-{id_page}",
        "source": "confluence",
        "url": CONFLUENCE_URL + page["_links"]["webui"],
        "titre": page.get("title", ""),
        "texte": texte_stockage(corps),
        "maj": page.get("version", {}).get("when"),
        "droits": droits_lecture(id_page),
        "espace": espace,
    }


def principal():
    espaces = paginer(f"{CONFLUENCE_URL}/rest/api/space")
    documents = []
    exemple_tableau = None  # premier document contenant un tableau
    for espace in espaces:
        cle = espace["key"]
        parametres = urllib.parse.urlencode(
            {"spaceKey": cle, "expand": "body.storage,version,space"}
        )
        pages = paginer(f"{CONFLUENCE_URL}/rest/api/content?{parametres}")
        pages = [page for page in pages if page.get("type") == "page"]
        print(f"Espace {cle} ({espace.get('name', '')}) : {len(pages)} page{'s' if len(pages) != 1 else ''}")
        for page in pages:
            document = en_document(page)
            documents.append(document)
            if exemple_tableau is None and "<table" in page.get("body", {}).get("storage", {}).get("value", ""):
                exemple_tableau = document

    FICHIER_SORTIE.parent.mkdir(parents=True, exist_ok=True)
    with FICHIER_SORTIE.open("w", encoding="utf-8") as fichier:
        for document in documents:
            fichier.write(json.dumps(document, ensure_ascii=False) + "\n")
    print(f"\n{len(documents)} documents écrits dans {FICHIER_SORTIE}")

    if exemple_tableau:
        print(f"\nTexte complet de la page avec un tableau : « {exemple_tableau['titre']} »")
        print(exemple_tableau["url"])
        print(exemple_tableau["texte"])
    else:
        print("\nAucune page ne contient de tableau.")


if __name__ == "__main__":
    principal()
