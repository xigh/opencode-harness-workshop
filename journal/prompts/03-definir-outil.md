Écris `etape3_outil.py`, qui réutilise `appeler` de `etape1_appel.py`.

- Définis un outil `etat_service(nom)` au format JSON Schema des outils OpenAI (type `function`, description, paramètres). Description : « Donne l'état d'un service système (actif, arrêté, en échec) et l'heure de son dernier redémarrage. »
- Envoie la question « Le service nginx tourne-t-il ? » avec cet outil.
- Affiche ce que le modèle a renvoyé. On doit voir qu'il ne répond pas en texte mais demande un appel d'outil (`tool_calls`, avec le nom et les arguments en JSON), que `finish_reason` vaut `tool_calls`, enfin que `content` est vide (`null` ou chaîne vide) : c'est normal, le modèle attend le résultat de l'outil avant d'écrire. Explique-le dans un commentaire et dans la sortie.
- L'outil n'est pas encore branché : n'exécute aucune commande. Renvoie au modèle le fil complet, c'est-à-dire la question, sa demande d'appel telle quelle (le message `assistant` avec ses `tool_calls`), puis un message `role: tool` avec le même `tool_call_id` et ce contenu : `{"erreur": "outil non branché : l'état du service est inconnu"}`. Montre la réponse finale : le modèle doit dire qu'il ne connaît pas l'état de nginx, sans l'inventer.
- Pose ensuite une question sans rapport (« Quelle est la capitale du Portugal ? ») avec le même outil ; montre que cette fois le modèle répond directement.

Lance-le et montre la sortie.
