Étape 00 : définir le projet. C'est ce que fait la commande `/init` d'OpenCode, mais en français et avec les règles de cet atelier. Écris tout en français.

1. `AGENTS.md` : la définition du projet. S'il existe déjà, lis-le et complète-le sans rien perdre de ses règles. Il contient :
   - l'objet du projet en deux phrases (déduis-le des fichiers présents ; pour cet atelier : un harnais d'agent pour une formation d'équipe infrastructure, puis un assistant documentaire) ;
   - les contraintes fixes : Python 3.11+, bibliothèque standard seulement sauf demande contraire ; code court, commenté en français, sans magie ; le JSON exact envoyé au modèle et reçu de lui, toujours affiché ou journalisé ; un fichier par notion ; après chaque modification, lancer le programme et montrer la sortie ; ne rien lire ni écrire hors de ce dossier ; si un service ne répond pas, le dire et s'arrêter sans le chercher ailleurs sur la machine ;
   - la règle des secrets (ci-dessous) ;
   - la règle de l'état (ci-dessous) ;
   - la liste des fichiers du projet, une ligne chacun.
2. La règle des secrets : aucune adresse de service, aucune clé, aucun jeton n'est écrit dans le code. Ils vivent dans le fichier `.env` du dossier (jamais versionné, jamais affiché) ou dans les variables d'environnement, qui l'emportent sur `.env`. Écris `config.py` :
   - `charger()` lit `.env` s'il existe (lignes `NOM=valeur` ; lignes vides et lignes qui commencent par `#` ignorées ; guillemets autour de la valeur retirés) et place chaque valeur dans `os.environ`, sans écraser une variable déjà définie ;
   - `masquer(nom, valeur)` rend la valeur telle quelle, sauf si le nom contient `CLE`, `JETON`, `SECRET` ou `MOT_DE_PASSE` : alors « définie » ou « absente », jamais la valeur ;
   - chaque programme du projet appelle `config.charger()` avant de lire `os.environ`.
3. `.env.example` : toutes les variables de l'atelier, avec une valeur d'exemple, jamais une vraie clé : `LLM_URL`, `LLM_MODELE`, `LLM_CLE`, `EMBED_URL`, `EMBED_MODELE`, `EMBED_CLE`, `QDRANT_URL`, `QDRANT_CLE`, `QDRANT_COLLECTION`, `RERANK_URL`, `RERANK_CLE`, `SERVICES_URL`, `CONFLUENCE_URL`, `CONFLUENCE_COMPTE`, `CONFLUENCE_JETON`, `CONFLUENCE_ESPACES`, plus celles que cite déjà `AGENTS.md`. Une ligne de commentaire au-dessus de chaque groupe dit à quoi il sert.
4. `.gitignore` : `.env`, `traces/`, `__pycache__/`.
5. Si `.env` n'existe pas, ne le crée pas et n'y écris jamais de clé : dis au formateur de copier `.env.example` en `.env` et de le remplir. Si `.env` existe, ne le lis pas avec tes outils : seuls les programmes le lisent, par `config.charger()`.
6. La règle de l'état : chaque étape se fait dans une session neuve d'OpenCode, qui ne se souvient de rien. Le fichier `ETAT.md` fait le lien : chaque étape commence par le lire et finit par le mettre à jour. Crée-le avec ces sections : « Projet » (une phrase), « Où on en est » (la dernière étape faite et son résultat en une ligne), « Étapes faites » (une ligne par étape : numéro, ce qui a été fait, fichiers, résultat), « Fichiers » (chacun avec son rôle), « Configuration » (les noms des variables utilisées et à quoi elles servent, jamais leurs valeurs), « Services » (adresse publique ou locale ; répondait-il à la dernière étape), « Ce qui ne marche pas encore », « Prochaine étape ».
7. `bonjour.py` : appelle `config.charger()`, affiche « Bonjour », puis, pour chaque variable de `.env.example`, son nom et `masquer(nom, valeur)`.

Lance `python3 bonjour.py` et montre la sortie. Termine en remplissant `ETAT.md` pour cette étape 00. Vérifie qu'aucune clé n'apparaît dans `ETAT.md`, `AGENTS.md`, `.env.example` ni dans la sortie.
