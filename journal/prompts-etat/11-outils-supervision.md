Étape 11, dans une session neuve. Commence par lire `ETAT.md` (où en est le projet, laissé par l'étape précédente) et `AGENTS.md` (la définition du projet). Les adresses, les clés et les jetons ne s'écrivent jamais dans le code : ils sont dans `.env` ou dans les variables d'environnement, chargés par `config.charger()` au début de chaque programme. Ne lis jamais `.env` avec tes outils.

Écris `outils_supervision.py` : les outils d'un assistant d'astreinte, branchés sur les API de supervision de l'équipe. Pour la formation, ces API sont simulées par un serveur local (adresse dans `SERVICES_URL`, défaut `http://127.0.0.1:8904`) qui imite Instana, Loki (Grafana), JIRA et Teams. Bibliothèque standard uniquement.

Pour chaque outil : une fonction Python et sa définition JSON Schema au format des outils OpenAI (comme dans `etape3_outil.py`), réunies dans une liste `OUTILS` et un dictionnaire `FONCTIONS` utilisables par `harnais.py`.

Outils en lecture :
- `lister_alertes()` : `GET /instana/api/events` ; renvoie pour chaque alerte l'identifiant, la gravité, le début, le problème, l'entité et le détail.
- `lire_journaux(service, debut, fin, motif=None, limite=50)` : `GET /loki/api/v1/query_range` avec `query={service="<service>"}` (et `|= "<motif>"` si un motif est donné), `start`, `end`, `limit` (100 au plus) ; renvoie une liste de lignes `{horodatage, service, niveau, message}` triées par heure.
- `chercher_tickets()` : `GET /jira/rest/api/2/search` ; renvoie clé, résumé, statut.

Outils en écriture, soumis à confirmation humaine :
- `creer_ticket(resume, description, priorite)` : `POST /jira/rest/api/2/issue` dans le projet `INFRA`.
- `poster_teams(texte)` : `POST /teams/webhook`.
Avant toute écriture, une fonction `confirmer(action, details)` affiche ce qui va être fait et demande « Confirmer ? (o/n) ». La variable d'environnement `CONFIRMATION` peut valoir `oui` (tout accepter, pour une démonstration enregistrée), `non` (tout refuser) ou être absente (demander au clavier). En cas de refus, l'outil n'appelle pas l'API et renvoie au modèle `{"refuse": true, "raison": "refusé par l'opérateur"}`.

Il n'y a volontairement aucun outil pour fermer ou modifier un ticket existant.

Teste chaque outil de lecture directement (sans modèle) et montre la sortie, puis teste `creer_ticket` avec `CONFIRMATION=non` et montre qu'aucun ticket n'est créé (route `GET /etat` du serveur).

Pour clore l'étape :
1. Mets à jour `ETAT.md` (sections de l'étape 00) : ce qui a été fait, les fichiers créés ou modifiés, les commandes lancées et leur résultat, l'état des services utilisés, les variables utilisées (leurs noms, jamais leurs valeurs), ce qui ne marche pas encore, la prochaine étape.
2. Si l'étape utilise une variable nouvelle, ajoute-la à `.env.example` avec une valeur d'exemple, jamais la vraie.
3. Si l'étape change le projet (fichier nouveau, règle nouvelle), mets à jour `AGENTS.md`.
4. Vérifie qu'aucune clé n'apparaît dans `ETAT.md`, `AGENTS.md`, `.env.example`, le code ni la sortie.
