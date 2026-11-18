# Projet : harnais de démonstration et assistant documentaire

Ce dépôt sert à une formation (équipe infrastructure). Le code doit se lire à l'écran : court, commenté en français, sans magie.

## Contraintes fixes

- Python 3.11+, bibliothèque standard uniquement (`urllib.request`, `json`), sauf indication contraire dans la demande.
- Le serveur du modèle est compatible OpenAI. Sa configuration et ses identifiants se lisent dans des variables d'environnement, jamais en dur dans le code : l'adresse dans `LLM_URL` (défaut `http://127.0.0.1:8800/v1`), le nom du modèle dans `LLM_MODELE` (défaut `qwen3.8-27b`), la clé d'API dans `LLM_CLE` (facultative, envoyée en `Authorization: Bearer`, jamais affichée).
- Chaque étape du harnais est visible : le programme affiche (ou écrit dans un journal) le JSON exact envoyé au modèle et le JSON exact reçu.
- Un fichier par notion, des fonctions courtes, pas de classes inutiles.
- Après chaque modification, lancer le programme pour vérifier qu'il marche, et montrer la sortie.
- Ne jamais écrire en dehors de ce dossier. Ne rien lire en dehors du dépôt (pas de `~/.config`, pas de fichiers de clés, pas d'autres projets) : les adresses et les clés arrivent par les variables d'environnement, déjà définies au lancement. Si un service ne répond pas, le dire et s'arrêter, sans le chercher ailleurs sur la machine.
