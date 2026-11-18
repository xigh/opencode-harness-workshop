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
