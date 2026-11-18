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
