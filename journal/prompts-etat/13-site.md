Étape 13, dans une session neuve. Commence par lire `ETAT.md` (où en est le projet, laissé par l'étape précédente) et `AGENTS.md` (la définition du projet). Les adresses, les clés et les jetons ne s'écrivent jamais dans le code : ils sont dans `.env` ou dans les variables d'environnement, chargés par `config.charger()` au début de chaque programme. Ne lis jamais `.env` avec tes outils.

Écris `source_site.py` : le connecteur du site « base de connaissance » (adresse dans `SITE_URL`).

- Lis `robots.txt`, respecte ses `Disallow`, et trouve le plan du site (`Sitemap:`).
- Parcours le `sitemap.xml` : pour chaque page, garde l'adresse et la date `lastmod`.
- Télécharge chaque page et garde seulement le texte de l'article (balise `<article>`), sans le menu ni le pied de page.
- Produis des documents au format commun, un par page : `{"id", "source": "site", "url", "titre", "texte", "maj", "droits": ["tous"]}`.
- Écris-les dans `donnees/documents-site.jsonl` et affiche le nombre de documents et le début du premier.

Pour clore l'étape :
1. Mets à jour `ETAT.md` (sections de l'étape 00) : ce qui a été fait, les fichiers créés ou modifiés, les commandes lancées et leur résultat, l'état des services utilisés, les variables utilisées (leurs noms, jamais leurs valeurs), ce qui ne marche pas encore, la prochaine étape.
2. Si l'étape utilise une variable nouvelle, ajoute-la à `.env.example` avec une valeur d'exemple, jamais la vraie.
3. Si l'étape change le projet (fichier nouveau, règle nouvelle), mets à jour `AGENTS.md`.
4. Vérifie qu'aucune clé n'apparaît dans `ETAT.md`, `AGENTS.md`, `.env.example`, le code ni la sortie.
