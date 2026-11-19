Étape 02, dans une session neuve. Commence par lire `ETAT.md` (où en est le projet, laissé par l'étape précédente) et `AGENTS.md` (la définition du projet). Les adresses, les clés et les jetons ne s'écrivent jamais dans le code : ils sont dans `.env` ou dans les variables d'environnement, chargés par `config.charger()` au début de chaque programme. Ne lis jamais `.env` avec tes outils.

Écris `etape2_systeme.py`, qui réutilise `appeler` de `etape1_appel.py`.

Il pose la même question deux fois : « Mon serveur web répond 502, que faire ? »
- d'abord sans prompt système ;
- puis avec ce prompt système : « Tu es l'assistant de l'équipe infrastructure. Tu réponds en français, en cinq lignes au plus, et tu termines toujours par la commande à lancer en premier. »

Affiche les deux réponses l'une sous l'autre, avec la liste exacte des messages envoyés à chaque fois, pour qu'on voie que le prompt système n'est qu'un message de plus en tête de liste.

Lance-le et montre la sortie.

Pour clore l'étape :
1. Mets à jour `ETAT.md` (sections de l'étape 00) : ce qui a été fait, les fichiers créés ou modifiés, les commandes lancées et leur résultat, l'état des services utilisés, les variables utilisées (leurs noms, jamais leurs valeurs), ce qui ne marche pas encore, la prochaine étape.
2. Si l'étape utilise une variable nouvelle, ajoute-la à `.env.example` avec une valeur d'exemple, jamais la vraie.
3. Si l'étape change le projet (fichier nouveau, règle nouvelle), mets à jour `AGENTS.md`.
4. Vérifie qu'aucune clé n'apparaît dans `ETAT.md`, `AGENTS.md`, `.env.example`, le code ni la sortie.
