Étape 18, dans une session neuve. Commence par lire `ETAT.md` (où en est le projet, laissé par l'étape précédente) et `AGENTS.md` (la définition du projet). Les adresses, les clés et les jetons ne s'écrivent jamais dans le code : ils sont dans `.env` ou dans les variables d'environnement, chargés par `config.charger()` au début de chaque programme. Ne lis jamais `.env` avec tes outils.

Écris `questions.json` et `evaluer.py` : un petit jeu de test de l'assistant.

Les questions, avec pour chacune la source attendue (ou « aucune ») et un mot-clé que la bonne réponse doit contenir :
1. Quel port utiliser pour le VPN ? (confluence ; « 51820 »)
2. Que faire si Qdrant de l'assistant documentaire redémarre en boucle avec le code 137 ? (confluence ; « suspendre »)
3. Combien de temps les sauvegardes quotidiennes sont-elles gardées ? (confluence ; « 30 jours »)
4. Qui avait l'astreinte la semaine du 10 novembre ? (teams ; « Camille »)
5. Pourquoi l'assistant documentaire ne trouve-t-il pas les délibérations de 2019 ? (teams ; « 2021 »)
6. Quand faut-il demander le renouvellement d'un certificat ? (confluence ; « 30 jours »)
7. Quels comptes de service existent et qui les détient ? (aucune pour un utilisateur sans le groupe secu : l'assistant doit dire qu'il ne sait pas)
8. Combien de caractères au minimum pour un mot de passe nominatif ? (site ou confluence ; « 14 »)

`evaluer.py` lance l'assistant sur chaque question (avec les droits par défaut), note si le mot-clé est présent, si la source attendue est citée, le nombre de tours et le temps, puis affiche un tableau récapitulatif. Garde toutes les réponses complètes dans `donnees/evaluation.json`.

Pour clore l'étape :
1. Mets à jour `ETAT.md` (sections de l'étape 00) : ce qui a été fait, les fichiers créés ou modifiés, les commandes lancées et leur résultat, l'état des services utilisés, les variables utilisées (leurs noms, jamais leurs valeurs), ce qui ne marche pas encore, la prochaine étape.
2. Si l'étape utilise une variable nouvelle, ajoute-la à `.env.example` avec une valeur d'exemple, jamais la vraie.
3. Si l'étape change le projet (fichier nouveau, règle nouvelle), mets à jour `AGENTS.md`.
4. Vérifie qu'aucune clé n'apparaît dans `ETAT.md`, `AGENTS.md`, `.env.example`, le code ni la sortie.
