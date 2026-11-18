# Le corpus des étapes 06 à 10

Mettez vos PDF dans `corpus/pdf/` (des documents publics : ce dossier n'est jamais versionné) et décrivez-les dans `corpus/manifeste.json`, une entrée par fichier :

```json
[
  {"fichier": "rapport-numerique-responsable-2025.pdf", "titre": "Le numérique responsable en 2025"},
  {"fichier": "guide-centres-de-donnees.pdf", "titre": "Guide des centres de données sobres"}
]
```

`projet/ingestion.py` lit le manifeste, découpe chaque PDF en morceaux de 1 500 caractères, calcule leurs embeddings et les envoie dans la collection Qdrant `documents`.
