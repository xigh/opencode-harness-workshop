# Projet : harnais de démonstration et assistant documentaire

Ce dépôt sert à une formation (équipe infrastructure). Le code doit se lire à l'écran : court, commenté en français, sans magie.

## Contraintes fixes

- Python 3.11+, bibliothèque standard uniquement (`urllib.request`, `json`), sauf indication contraire dans la demande.
- Le serveur du modèle est compatible OpenAI. Son adresse se lit dans la variable d'environnement `LLM_URL` (défaut `http://127.0.0.1:8800/v1`), le nom du modèle dans `LLM_MODELE` (défaut `qwen3.8-27b`).
- Chaque étape du harnais est visible : le programme affiche (ou écrit dans un journal) le JSON exact envoyé au modèle et le JSON exact reçu.
- Un fichier par notion, des fonctions courtes, pas de classes inutiles.
- Après chaque modification, lancer le programme pour vérifier qu'il marche, et montrer la sortie.
- Ne jamais écrire en dehors de ce dossier.
