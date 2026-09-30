"""
Smoke test — vérifie rapidement que les endpoints principaux de l'API répondent
correctement avant un déploiement. Ne remplace pas des tests unitaires complets,
juste un filet de sécurité rapide (quelques secondes) avant de pousser en prod.

Usage :
    python test_smoke.py
    python test_smoke.py --url https://app.stackgestion.sarl   (pour tester la prod)

Prérequis : l'API doit tourner (localement ou en prod), et un compte doit déjà
exister (voir create_user.py).
"""

import argparse
import getpass
import sys

import requests

OK = "\033[92mOK\033[0m"
FAIL = "\033[91mECHEC\033[0m"
WARN = "\033[93mATTENTION\033[0m"


def tester(nom, fonction):
    try:
        resultat = fonction()
        print(f"[{OK}] {nom}" + (f" — {resultat}" if resultat else ""))
        return True
    except AssertionError as e:
        print(f"[{FAIL}] {nom} — {e}")
        return False
    except Exception as e:
        print(f"[{FAIL}] {nom} — erreur inattendue : {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000", help="URL de base de l'API")
    args = parser.parse_args()
    base = args.url.rstrip("/")

    print(f"Test de l'API sur {base}\n")

    email = input("Email du compte de test : ").strip()
    mot_de_passe = getpass.getpass("Mot de passe : ")

    echecs = 0
    token = {}

    # --- 1. Connexion ---
    def test_login():
        r = requests.post(
            f"{base}/login",
            data={"username": email, "password": mot_de_passe},
            timeout=10,
        )
        assert r.status_code == 200, f"statut {r.status_code} (identifiants corrects ?)"
        data = r.json()
        assert "access_token" in data, "pas de jeton dans la réponse"
        token["valeur"] = data["access_token"]
        return "jeton obtenu"

    if not tester("Connexion (/login)", test_login):
        print("\nImpossible de continuer sans jeton valide. Arrêt.")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token['valeur']}"}

    # --- 2. Endpoints de lecture simples ---
    def test_get(endpoint):
        def _test():
            r = requests.get(f"{base}{endpoint}", headers=headers, timeout=10)
            assert r.status_code == 200, f"statut {r.status_code}"
            return f"{len(r.json())} élément(s)" if isinstance(r.json(), list) else "OK"
        return _test

    for endpoint in ["/appels-offres/pertinents?seuil=7", "/appels-offres/nouveaux?heures=24",
                      "/clients", "/produits", "/devis", "/surveillance/stats"]:
        if not tester(f"GET {endpoint}", test_get(endpoint)):
            echecs += 1

    # --- 3. Génération de devis : cas normal (produit avec prix) ---
    produit_avec_prix = {}
    produit_sans_prix = {}

    def test_chercher_produits():
        r = requests.get(f"{base}/produits", headers=headers, timeout=10)
        assert r.status_code == 200
        produits = r.json()
        for p in produits:
            if p.get("prix_unitaire") is not None and "id" not in produit_avec_prix:
                produit_avec_prix["id"] = p["id"]
            if p.get("prix_unitaire") is None and "id" not in produit_sans_prix:
                produit_sans_prix["id"] = p["id"]
        assert produit_avec_prix.get("id"), "aucun produit avec prix trouvé pour tester"
        trouve = "avec ET sans prix" if produit_sans_prix.get("id") else "avec prix seulement"
        return f"produits de test trouvés ({trouve})"

    tester("Recherche de produits de test", test_chercher_produits)

    def test_chercher_client():
        r = requests.get(f"{base}/clients", headers=headers, timeout=10)
        clients = r.json()
        assert clients, "aucun client en base pour tester (crée-en un d'abord)"
        return clients[0]["id"]

    client_id = None
    try:
        client_id = test_chercher_client()
        print(f"[{OK}] Recherche d'un client de test — client #{client_id}")
    except Exception as e:
        print(f"[{WARN}] Recherche d'un client de test — {e}, tests de devis ignorés")

    if client_id and produit_avec_prix.get("id"):
        def test_devis_avec_prix():
            r = requests.post(
                f"{base}/devis",
                headers=headers,
                json={"client_id": client_id, "produits": [
                    {"produit_id": produit_avec_prix["id"], "quantite": 1}
                ]},
                timeout=30,
            )
            assert r.status_code == 200, f"statut {r.status_code} — {r.text[:200]}"
            return "devis créé"

        tester("POST /devis (produit avec prix)", test_devis_avec_prix)

    # --- 4. Cas limite : produit SANS prix, doit échouer proprement (400), pas planter (500) ---
    if client_id and produit_sans_prix.get("id"):
        def test_devis_sans_prix():
            r = requests.post(
                f"{base}/devis",
                headers=headers,
                json={"client_id": client_id, "produits": [
                    {"produit_id": produit_sans_prix["id"], "quantite": 1}
                ]},
                timeout=30,
            )
            assert r.status_code != 500, (
                "l'API a planté (500) au lieu de renvoyer une erreur propre — "
                "voir le correctif discuté pour devis.py"
            )
            assert r.status_code == 400, f"statut inattendu {r.status_code} (400 attendu)"
            return "rejeté proprement (400), comme attendu"

        tester("POST /devis (produit SANS prix → doit être rejeté proprement)", test_devis_sans_prix)
    else:
        print(f"[{WARN}] Pas de produit sans prix trouvé en base — test du cas limite ignoré")

    print("\nTerminé.")


if __name__ == "__main__":
    main()