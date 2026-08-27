"""
Récupération du catalogue produits réel d'Ecodelta via l'API JSON publique de
WooCommerce (Store API) — https://ecodelta.ma/wp-json/wc/store/v1/products

Version corrigée : le dédoublonnage se fait désormais sur source_id (l'ID
unique fourni par l'API WooCommerce), et non plus sur le nom du produit —
plusieurs produits distincts du catalogue Ecodelta partagent en effet des
noms identiques ou quasi identiques, ce qui faisait perdre à tort de vrais
produits différents lors de la première version du script.

Installation : pip install requests beautifulsoup4 psycopg2-binary python-dotenv
Prérequis : avoir exécuté migration_source_id.sql au préalable.
"""

import time
import requests
from bs4 import BeautifulSoup
from db import get_connection

API_URL = "https://ecodelta.ma/wp-json/wc/store/v1/products"
PER_PAGE = 50

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; EcodeltaCatalogBot/1.0; usage interne stage EMSI)"
}

DELAI_ENTRE_PAGES = 1.0


def nettoyer_html(texte_html):
    if not texte_html:
        return ""
    return BeautifulSoup(texte_html, "html.parser").get_text(separator="\n", strip=True)


def extraire_prix(prices_obj):
    if not prices_obj:
        return None
    prix_brut = prices_obj.get("price")
    if not prix_brut or prix_brut == "0":
        return None
    try:
        unite_mineure = int(prices_obj.get("currency_minor_unit", 2))
        return round(int(prix_brut) / (10 ** unite_mineure), 2)
    except (ValueError, TypeError):
        return None


def recuperer_tous_les_produits():
    tous_les_produits = []
    page = 1

    while True:
        params = {"page": page, "per_page": PER_PAGE}
        print(f"Récupération page {page} (API)...")

        try:
            resp = requests.get(API_URL, headers=HEADERS, params=params, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  (erreur sur la page {page}: {e})")
            break

        donnees = resp.json()
        if not donnees:
            print("  (page vide, fin de la pagination)")
            break

        tous_les_produits.extend(donnees)
        print(f"  -> {len(donnees)} produits récupérés sur cette page")

        total_pages = int(resp.headers.get("X-WP-TotalPages", page))
        if page >= total_pages:
            break

        page += 1
        time.sleep(DELAI_ENTRE_PAGES)

    print(f"\n{len(tous_les_produits)} produits au total récupérés depuis l'API.")
    return tous_les_produits


def transformer_produit(produit_api):
    source_id = produit_api.get("id")
    nom = produit_api.get("name", "").strip()
    if not nom or source_id is None:
        return None

    description = nettoyer_html(produit_api.get("description") or produit_api.get("short_description"))
    prix = extraire_prix(produit_api.get("prices"))

    images = produit_api.get("images", [])
    image_url = images[0]["src"] if images else None

    return {
        "source_id": source_id,
        "nom": nom,
        "description": description[:4000],
        "specs_techniques": "",
        "prix_unitaire": prix,
        "image_url": image_url,
    }


def sauvegarder_produits(produits):
    conn = get_connection()
    cur = conn.cursor()
    inseres = 0
    ignores = 0

    for p in produits:
        if p is None:
            continue

        # Anti-doublon fiable : basé sur l'ID WooCommerce, pas sur le nom
        cur.execute("SELECT id FROM produits WHERE source_id = %s", (p["source_id"],))
        if cur.fetchone():
            ignores += 1
            continue

        cur.execute(
            """INSERT INTO produits (nom, description, prix_unitaire, specs_techniques, source_id, image_url)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (p["nom"], p["description"], p["prix_unitaire"], p["specs_techniques"], p["source_id"], p["image_url"]),
        )
        inseres += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"\n{inseres} produits insérés, {ignores} déjà existants (ignorés).")


if __name__ == "__main__":
    produits_api = recuperer_tous_les_produits()

    print("\nTransformation des données...")
    produits = [transformer_produit(p) for p in produits_api]
    produits = [p for p in produits if p is not None]

    print(f"{len(produits)} produits valides après transformation.")

    print("\nSauvegarde en base de données...")
    sauvegarder_produits(produits)