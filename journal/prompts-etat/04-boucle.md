Étape 04, dans une session neuve. Commence par lire `ETAT.md` (où en est le projet, laissé par l'étape précédente) et `AGENTS.md` (la définition du projet). Les adresses, les clés et les jetons ne s'écrivent jamais dans le code : ils sont dans `.env` ou dans les variables d'environnement, chargés par `config.charger()` au début de chaque programme. Ne lis jamais `.env` avec tes outils.

Écris `etape4_boucle.py`, qui réutilise `appeler` et l'outil de `etape3_outil.py`.

C'est la boucle d'un harnais :
1. On envoie la question avec la liste des outils.
2. Si la réponse contient des `tool_calls`, le harnais exécute chaque outil lui-même (ici une fausse fonction Python `etat_service` qui renvoie un dictionnaire inventé, par exemple nginx en échec depuis 03:12), ajoute au fil le message de l'assistant puis un message `role: tool` avec le `tool_call_id` et le résultat en JSON, et rappelle le modèle.
3. On recommence jusqu'à une réponse sans appel d'outil.
4. Garde-fou : 5 tours au maximum, puis on s'arrête avec un message clair.

Question : « nginx et postgresql tournent-ils ? Si l'un est en échec, dis-moi depuis quand. »

À chaque tour, affiche un titre « TOUR n », le nombre de messages dans le fil et les tokens consommés, pour qu'on voie le fil grossir. À la fin, affiche la réponse.

Lance-le et montre la sortie.

Pour clore l'étape :
1. Mets à jour `ETAT.md` (sections de l'étape 00) : ce qui a été fait, les fichiers créés ou modifiés, les commandes lancées et leur résultat, l'état des services utilisés, les variables utilisées (leurs noms, jamais leurs valeurs), ce qui ne marche pas encore, la prochaine étape.
2. Si l'étape utilise une variable nouvelle, ajoute-la à `.env.example` avec une valeur d'exemple, jamais la vraie.
3. Si l'étape change le projet (fichier nouveau, règle nouvelle), mets à jour `AGENTS.md`.
4. Vérifie qu'aucune clé n'apparaît dans `ETAT.md`, `AGENTS.md`, `.env.example`, le code ni la sortie.
