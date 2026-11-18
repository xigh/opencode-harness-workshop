Écris `etape3_outil.py`, qui réutilise `appeler` de `etape1_appel.py`.

- Définis un outil `etat_service(nom)` au format JSON Schema des outils OpenAI (type `function`, description, paramètres). Description : « Donne l'état d'un service système (actif, arrêté, en échec) et l'heure de son dernier redémarrage. »
- Envoie la question « Le service nginx tourne-t-il ? » avec cet outil.
- N'exécute rien : affiche seulement ce que le modèle a renvoyé. On doit voir que le modèle ne répond pas en texte mais demande un appel d'outil (`tool_calls`, avec le nom et les arguments en JSON), et que `finish_reason` vaut `tool_calls`.
- Pose ensuite une question sans rapport (« Quelle est la capitale du Portugal ? ») avec le même outil, et montre que cette fois le modèle répond directement.

Lance-le et montre la sortie.
