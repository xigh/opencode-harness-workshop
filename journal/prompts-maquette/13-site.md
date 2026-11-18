Écris `source_site.py` : le connecteur du site « base de connaissance » (adresse dans `SITE_URL`).

- Lis `robots.txt`, respecte ses `Disallow`, et trouve le plan du site (`Sitemap:`).
- Parcours le `sitemap.xml` : pour chaque page, garde l'adresse et la date `lastmod`.
- Télécharge chaque page et garde seulement le texte de l'article (balise `<article>`), sans le menu ni le pied de page.
- Produis des documents au format commun, un par page : `{"id", "source": "site", "url", "titre", "texte", "maj", "droits": ["tous"]}`.
- Écris-les dans `donnees/documents-site.jsonl` et affiche le nombre de documents et le début du premier.
