"""Évalue l'assistant sur le jeu de test questions.json.

Pour chaque question :
1. Lancer l'assistant (assistant.repondre) avec les droits par défaut.
2. Noter : le mot-clé est-il dans la réponse ? La source attendue est-elle
   citée (ou, pour « aucune », aucune source n'est-elle citée) ?
3. Noter le nombre de tours (appels au modèle) et le temps écoulé.
En fin de course : afficher un tableau récapitulatif et garder les
réponses complètes dans donnees/evaluation.json.
"""

import json
import time
from datetime import datetime
from pathlib import Path

import assistant

QUESTIONS = Path(__file__).resolve().parent / "questions.json"
RESULTAT = Path(__file__).resolve().parent / "donnees" / "evaluation.json"

# « aucune » : l'assistant doit dire qu'il ne sait pas, sans citer de source.
AUCUNE = "aucune"


def lire_questions():
    """Lit le jeu de test questions.json (liste de questions)."""
    with QUESTIONS.open(encoding="utf-8") as fichier:
        return json.load(fichier)


def mots_cles(test):
    """Renvoie la liste des formulations acceptables du mot-clé d'un test.

    Le mot-clé est soit un seul texte, soit une liste de formulations
    (cas de la question « je ne sais pas » : plusieurs tournures valent).
    """
    mot_cle = test["mot_cle"]
    return [mot_cle] if isinstance(mot_cle, str) else mot_cle


def source_attendue(test):
    """Renvoie la liste des sources acceptables pour un test.

    « aucune » est conservé tel quel ; un nom simple devient une liste
    à un élément ; « site ou confluence » reste une liste.
    """
    source = test["source"]
    return [source] if isinstance(source, str) else source


def mot_cle_trouve(test, reponse):
    """Vrai si l'une des formulations du mot-clé figure dans la réponse."""
    reponse_basse = reponse.lower()
    return any(variante.lower() in reponse_basse for variante in mots_cles(test))


def source_ok(test, sources_citees, reponse):
    """Vrai si la réponse respecte la source attendue du test.

    Pour « aucune » : l'utilisateur n'a accès à aucun document pertinent,
    l'assistant ne doit donc pas répondre en s'appuyant sur une source :
    il doit dire qu'il ne sait pas. Le critère est porté par le mot-clé
    (la formulation de refus) qu'on renvoie ici. Les sources qu'il cite
    pour expliquer ce qu'il n'a pas trouvé ne comptent pas comme une
    réponse appuyée sur une source.
    Sinon : au moins une des sources citées doit être l'une des attendues.
    """
    attendues = source_attendue(test)
    if AUCUNE in attendues:
        return mot_cle_trouve(test, reponse)
    citees = {extrait["source"] for extrait in sources_citees}
    return bool(citees & set(attendues))


def evaluer(test):
    """Lance l'assistant sur une question et note le résultat.

    Le nombre de tours est compté en enveloppant assistant.appeler_llm :
    chaque appel au modèle incrémente le compteur. Les droits de
    l'utilisateur sont ceux par défaut (variable UTILISATEUR_DROITS).
    """
    compteur = {"tours": 0}
    appeler_origine = assistant.appeler_llm

    def appeler_compte(messages):
        compteur["tours"] += 1
        return appeler_origine(messages)

    assistant.appeler_llm = appeler_compte
    debut = time.perf_counter()
    try:
        reponse, extraits_consultes = assistant.repondre(test["question"])
    finally:
        assistant.appeler_llm = appeler_origine  # rendre la fonction d'origine
    duree = time.perf_counter() - debut
    citees = assistant.sources_citees(reponse, extraits_consultes)
    return {
        "question": test["question"],
        "source_attendue": test["source"],
        "mot_cle": test["mot_cle"],
        "reponse": reponse,
        "sources_citees": [
            {cle: extrait[cle] for cle in ("source", "titre", "url", "maj")}
            for extrait in citees
        ],
        "mot_cle_present": mot_cle_trouve(test, reponse),
        "source_ok": source_ok(test, citees, reponse),
        "tours": compteur["tours"],
        "duree_s": round(duree, 1),
    }


def afficher_tableau(resultats):
    """Affiche le tableau récapitulatif, une ligne par question."""
    en_tete = f"{'N°':<3} {'Question':<45} {'Mot-clé':<9} {'Source':<9} {'Tours':<6} {'Durée':<7}"
    print(en_tete)
    print("-" * len(en_tete))
    for numero, resultat in enumerate(resultats, 1):
        question = resultat["question"]
        if len(question) > 44:
            question = question[:43] + "…"
        mot_cle = "oui" if resultat["mot_cle_present"] else "NON"
        source = "oui" if resultat["source_ok"] else "NON"
        print(
            f"{numero:<3} {question:<45} {mot_cle:<9} {source:<9} "
            f"{resultat['tours']:<6} {resultat['duree_s']:<6.1f}s"
        )
    reussites = sum(1 for r in resultats if r["mot_cle_present"] and r["source_ok"])
    print("-" * len(en_tete))
    print(f"Réussite : {reussites}/{len(resultats)} (mot-clé et source conformes)")


def ecrire_resultats(resultats):
    """Garde les réponses complètes dans donnees/evaluation.json."""
    resultat = {
        "date": datetime.now().isoformat(timespec="seconds"),
        "droits": assistant.DROITS,
        "resultats": resultats,
    }
    with RESULTAT.open("w", encoding="utf-8") as fichier:
        json.dump(resultat, fichier, ensure_ascii=False, indent=2)


def principal():
    tests = lire_questions()
    resultats = []
    for test in tests:
        print(f"Question : « {test['question']} »", flush=True)
        resultats.append(evaluer(test))
    afficher_tableau(resultats)
    ecrire_resultats(resultats)
    print(f"Réponses complètes dans {RESULTAT}")


if __name__ == "__main__":
    principal()
