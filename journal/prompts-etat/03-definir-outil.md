Étape 03, dans une session neuve. Commence par lire `ETAT.md` (où en est le projet, laissé par l'étape précédente) et `AGENTS.md` (la définition du projet). Les adresses, les clés et les jetons ne s'écrivent jamais dans le code : ils sont dans `.env` ou dans les variables d'environnement, chargés par `config.charger()` au début de chaque programme. Ne lis jamais `.env` avec tes outils.

Écris `etape3_outil.py`, qui réutilise `appeler` de `etape1_appel.py`.

- Définis un outil `etat_service(nom)` au format JSON Schema des outils OpenAI (type `function`, description, paramètres). Description : « Donne l'état d'un service système (actif, arrêté, en échec) et l'heure de son dernier redémarrage. »
- Envoie la question « Le service nginx tourne-t-il ? » avec cet outil.
- Affiche ce que le modèle a renvoyé. On doit voir qu'il ne répond pas en texte mais demande un appel d'outil (`tool_calls`, avec le nom et les arguments en JSON), que `finish_reason` vaut `tool_calls`, enfin que `content` est vide (`null` ou chaîne vide) : c'est normal, le modèle attend le résultat de l'outil avant d'écrire. Explique-le dans un commentaire et dans la sortie.
- L'outil n'est pas encore branché : n'exécute aucune commande. Renvoie au modèle le fil complet, avec ces trois messages et dans cet ordre :
  1. la question de l'utilisateur ;
  2. le message `assistant` reçu, recopié tel quel, avec ses `tool_calls` (sans lui, le modèle ne peut pas relier le résultat à sa demande) ;
  3. un message `role: tool` avec le même `tool_call_id` que dans ce message `assistant` ; son contenu : `{"erreur": "outil non branché : l'état du service est inconnu"}`.
- Vérifie la réponse finale dans le code, sans aucune phrase écrite d'avance : affiche son `finish_reason` et son `content`. Si `finish_reason` vaut `stop`, affiche le texte : le modèle doit dire qu'il ne connaît pas l'état de nginx, sans l'inventer. S'il vaut encore `tool_calls`, écris clairement que l'échange n'est pas bouclé.
- Pose ensuite une question sans rapport (« Quelle est la capitale du Portugal ? ») avec le même outil ; montre que cette fois le modèle répond directement, en vérifiant là aussi `finish_reason`.

Lance-le, relis la sortie, puis dis en une phrase si le modèle a bien reconnu qu'il ne connaissait pas l'état de nginx.

Pour clore l'étape :
1. Mets à jour `ETAT.md` (sections de l'étape 00) : ce qui a été fait, les fichiers créés ou modifiés, les commandes lancées et leur résultat, l'état des services utilisés, les variables utilisées (leurs noms, jamais leurs valeurs), ce qui ne marche pas encore, la prochaine étape.
2. Si l'étape utilise une variable nouvelle, ajoute-la à `.env.example` avec une valeur d'exemple, jamais la vraie.
3. Si l'étape change le projet (fichier nouveau, règle nouvelle), mets à jour `AGENTS.md`.
4. Vérifie qu'aucune clé n'apparaît dans `ETAT.md`, `AGENTS.md`, `.env.example`, le code ni la sortie.
