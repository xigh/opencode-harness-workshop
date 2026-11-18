"""Les outils de supervision de l'astreinte.

Cinq outils branchés sur les API de supervision de l'équipe : Instana
(alertes), Loki (journaux), JIRA (tickets) et Teams (annonces). Pour la
formation, ces API sont simulées par un serveur local dont l'adresse se
lit dans SERVICES_URL (défaut http://127.0.0.1:8904).

Chaque outil est une fonction Python et une définition JSON Schema au
format des outils OpenAI (comme dans etape3_outil.py). La liste OUTILS
et le dictionnaire FONCTIONS sont prêts à passer à harnais.executer.

Les écritures (créer un ticket, poster dans Teams) sont soumises à
confirmation humaine : la variable CONFIRMATION vaut « oui » (tout
accepter, pour une démo enregistrée), « non » (tout refuser) ou est
absente (demande au clavier). Il n'y a volontairement aucun outil pour
fermer ou modifier un ticket existant.
"""

import json
import os
import urllib.parse
import urllib.request

# Adresse du serveur qui simule les API de l'équipe.
SERVICES_URL = os.environ.get("SERVICES_URL", "http://127.0.0.1:8904")


def appeler_service(methode, chemin, parametres=None, corps=None):
    """Envoie une requête au serveur de services et renvoie le JSON reçu.

    L'URL, le corps envoyé et le JSON reçu sont affichés : chaque étape
    de l'appel est visible à l'écran.
    """
    if parametres is not None:
        chemin = chemin + "?" + urllib.parse.urlencode(parametres)
    url = SERVICES_URL + chemin
    print(f">>> {methode} {url}")
    data = None
    if corps is not None:
        data = json.dumps(corps).encode("utf-8")
        print(json.dumps(corps, ensure_ascii=False, indent=2))
    demande = urllib.request.Request(
        url,
        data=data,
        method=methode,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(demande) as reponse:
        recu = json.loads(reponse.read().decode("utf-8"))
    print("<<< RÉPONSE")
    print(json.dumps(recu, ensure_ascii=False, indent=2))
    return recu


# ------------------------------------------------------------------ lecture


def lister_alertes():
    """Liste les alertes ouvertes (Instana)."""
    recu = appeler_service("GET", "/instana/api/events")
    return [
        {
            "identifiant": alerte["eventId"],
            "gravite": alerte["severity"],
            "debut": alerte["start"],
            "probleme": alerte["problem"],
            "entite": alerte["entityName"],
            "detail": alerte["detail"],
        }
        for alerte in recu["items"]
    ]


def lire_journaux(service, debut, fin, motif=None, limite=50):
    """Lit les journaux d'un service dans Loki, entre deux heures ISO 8601.

    Si motif est donné, ne renvoie que les lignes qui le contiennent.
    Le nombre de lignes est plafonné à 100. Les lignes sont triées
    par horodatage.
    """
    requete_logql = '{service="%s"}' % service
    if motif:
        requete_logql += ' |= "%s"' % motif
    recu = appeler_service(
        "GET",
        "/loki/api/v1/query_range",
        parametres={
            "query": requete_logql,
            "start": debut,
            "end": fin,
            "limit": min(limite, 100),
        },
    )
    lignes = []
    for flux in recu["data"]["result"]:
        for horodatage, message in flux["values"]:
            lignes.append({
                "horodatage": horodatage,
                "service": flux["stream"]["service"],
                "niveau": flux["stream"]["level"],
                "message": message,
            })
    lignes.sort(key=lambda ligne: ligne["horodatage"])
    return lignes


def chercher_tickets():
    """Liste les tickets JIRA du projet INFRA : clé, résumé, statut."""
    recu = appeler_service("GET", "/jira/rest/api/2/search")
    return [
        {
            "cle": ticket["key"],
            "resume": ticket["fields"]["summary"],
            "statut": ticket["fields"]["status"]["name"],
        }
        for ticket in recu["issues"]
    ]


# ----------------------------------------------------------------- écriture


def confirmer(action, details):
    """Demande à l'opérateur de valider une écriture avant de l'effectuer.

    La variable CONFIRMATION pilote le mode :
      « oui »   : tout accepter (démo enregistrée)
      « non »   : tout refuser
      absente   : demande au clavier, « Confirmer ? (o/n) »
    """
    print()
    print(f"Action à confirmer : {action}")
    print(f"Détails : {json.dumps(details, ensure_ascii=False)}")
    mode = os.environ.get("CONFIRMATION")
    if mode == "oui":
        print("CONFIRMATION=oui : action acceptée.")
        return True
    if mode == "non":
        print("CONFIRMATION=non : action refusée.")
        return False
    return input("Confirmer ? (o/n) ").strip().lower() in ("o", "oui")


def creer_ticket(resume, description, priorite):
    """Crée un ticket JIRA dans le projet INFRA (écriture, à confirmer)."""
    details = {"resume": resume, "description": description, "priorite": priorite}
    if not confirmer("créer un ticket JIRA dans le projet INFRA", details):
        return {"refuse": True, "raison": "refusé par l'opérateur"}
    corps = {
        "fields": {
            "project": {"key": "INFRA"},
            "summary": resume,
            "description": description,
            "priority": {"name": priorite},
        }
    }
    return appeler_service("POST", "/jira/rest/api/2/issue", corps=corps)


def poster_teams(texte):
    """Poste un message dans le canal d'astreinte Teams (écriture, à confirmer)."""
    if not confirmer("poster un message dans le canal d'astreinte Teams", {"texte": texte}):
        return {"refuse": True, "raison": "refusé par l'opérateur"}
    return appeler_service("POST", "/teams/webhook", corps={"text": texte})


# ---------------------------------------------------- définitions pour le modèle

OUTILS = [
    {
        "type": "function",
        "function": {
            "name": "lister_alertes",
            "description": (
                "Liste les alertes de supervision ouvertes (Instana) : gravité, "
                "heure de début, problème, entité concernée et détail."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lire_journaux",
            "description": (
                "Lit les journaux d'un service dans Loki sur une plage horaire, "
                "éventuellement filtrés par un motif. Renvoie les lignes triées "
                "par heure."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Le nom du service, par exemple « nginx ».",
                    },
                    "debut": {
                        "type": "string",
                        "description": (
                            "Début de la plage, heure ISO 8601, "
                            "par exemple « 2026-11-16T07:40:00Z »."
                        ),
                    },
                    "fin": {
                        "type": "string",
                        "description": "Fin de la plage, heure ISO 8601.",
                    },
                    "motif": {
                        "type": "string",
                        "description": "Optionnel : ne renvoyer que les lignes "
                                       "contenant ce motif.",
                    },
                    "limite": {
                        "type": "integer",
                        "description": "Nombre maximum de lignes, 100 au plus "
                                       "(défaut 50).",
                    },
                },
                "required": ["service", "debut", "fin"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "chercher_tickets",
            "description": (
                "Liste les tickets JIRA du projet INFRA : clé, résumé et statut."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "creer_ticket",
            "description": (
                "Crée un ticket JIRA dans le projet INFRA. Écriture soumise "
                "à confirmation humaine avant exécution."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "resume": {
                        "type": "string",
                        "description": "Résumé court du ticket.",
                    },
                    "description": {
                        "type": "string",
                        "description": "Description détaillée du problème.",
                    },
                    "priorite": {
                        "type": "string",
                        "description": "Priorité, par exemple « Haute ».",
                    },
                },
                "required": ["resume", "description", "priorite"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "poster_teams",
            "description": (
                "Poste un message dans le canal d'astreinte Teams. Écriture "
                "soumise à confirmation humaine avant exécution."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "texte": {
                        "type": "string",
                        "description": "Le texte du message à envoyer.",
                    },
                },
                "required": ["texte"],
            },
        },
    },
]

FONCTIONS = {
    "lister_alertes": lister_alertes,
    "lire_journaux": lire_journaux,
    "chercher_tickets": chercher_tickets,
    "creer_ticket": creer_ticket,
    "poster_teams": poster_teams,
}


if __name__ == "__main__":
    # Test des outils de lecture, directement, sans modèle.

    print("=" * 62)
    print("1) lister_alertes()")
    print("=" * 62)
    print(json.dumps(lister_alertes(), ensure_ascii=False, indent=2))

    print()
    print("=" * 62)
    print("2) lire_journaux(« qdrant », 07:33 → 07:43) — la panne de mémoire")
    print("=" * 62)
    print(json.dumps(
        lire_journaux("qdrant", "2026-11-16T07:33:00Z", "2026-11-16T07:43:00Z"),
        ensure_ascii=False, indent=2))

    print()
    print("=" * 62)
    print("3) lire_journaux(« nginx », 07:41 → 07:44, motif « 502 »)")
    print("=" * 62)
    print(json.dumps(
        lire_journaux("nginx", "2026-11-16T07:41:00Z", "2026-11-16T07:44:00Z", motif="502"),
        ensure_ascii=False, indent=2))

    print()
    print("=" * 62)
    print("4) chercher_tickets()")
    print("=" * 62)
    print(json.dumps(chercher_tickets(), ensure_ascii=False, indent=2))

    print()
    print("=" * 62)
    print("5) creer_ticket(...) — écriture soumise à confirmation")
    print("=" * 62)
    print(json.dumps(creer_ticket(
        resume="Qdrant OOMKilled en boucle : recherche dégradée",
        description=(
            "Depuis 07:33, qdrant (docs-qdrant-0) est tué par OOM (code 137) "
            "toutes les ~90 s ; docs-api renvoie 503 et nginx 502."
        ),
        priorite="Haute",
    ), ensure_ascii=False, indent=2))

    print()
    print("=" * 62)
    print("6) État du serveur : aucun ticket ne doit avoir été créé")
    print("=" * 62)
    appeler_service("GET", "/etat")
