Écris `etape4_boucle.py`, qui réutilise `appeler` et l'outil de `etape3_outil.py`.

C'est la boucle d'un harnais :
1. On envoie la question avec la liste des outils.
2. Si la réponse contient des `tool_calls`, le harnais exécute chaque outil lui-même (ici une fausse fonction Python `etat_service` qui renvoie un dictionnaire inventé, par exemple nginx en échec depuis 03:12), ajoute au fil le message de l'assistant puis un message `role: tool` avec le `tool_call_id` et le résultat en JSON, et rappelle le modèle.
3. On recommence jusqu'à une réponse sans appel d'outil.
4. Garde-fou : 5 tours au maximum, puis on s'arrête avec un message clair.

Question : « nginx et postgresql tournent-ils ? Si l'un est en échec, dis-moi depuis quand. »

À chaque tour, affiche un titre « TOUR n », le nombre de messages dans le fil et les tokens consommés, pour qu'on voie le fil grossir. À la fin, affiche la réponse.

Lance-le et montre la sortie.
