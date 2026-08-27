"""
Scraper du catalogue produits réel d'Ecodelta (ecodelta.ma).

Contrairement au scraper des appels d'offres, ce site est rendu côté serveur
(WordPress/WooCommerce classique) : pas besoin de Playwright, requests + BeautifulSoup
suffisent.

IMPORTANT : aucun prix n'est affiché publiquement sur le site (modèle "sur devis").
Le champ prix_unitaire est donc laissé à NULL pour chaque produit inséré.

Avant de lancer ce script :
1. Vérifie toi-même https://ecodelta.ma/robots.txt pour confirmer que /nos-produits/
   et /produit/ ne sont pas interdits au crawl.
2. Installe les dépendances : pip install requests beautifulsoup4 psycopg2-binary python-dotenv
"""

import time
import re
import requests
from bs4 import BeautifulSoup
from db import get_connection

BASE_URL = "https://ecodelta.ma"
LISTE_URL = "https://ecodelta.ma/nos-produits/"
NB_PAGES = 4  # constaté manuellement (pagination "1 2 3 4" sur le site)

# User-Agent honnête, identifiant clairement le script (bonne pratique de scraping éthique)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; EcodeltaCatalogBot/1.0; usage interne stage EMSI)"
}

DELAI_ENTRE_REQUETES = 1.5  # secondes, pour ne pas surcharger le serveur


def recuperer_liens_produits():
    """Parcourt les pages de la boutique et collecte tous les liens vers les fiches produits."""
    liens = set()

    for page_num in range(1, NB_PAGES + 1):
        url = LISTE_URL if page_num == 1 else f"{LISTE_URL}?product-page={page_num}"
        print(f"Lecture de la page {page_num} : {url}")

        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  (erreur sur la page {page_num}: {e})")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        # Les fiches produits sont liées via des <a href="https://ecodelta.ma/produit/...">
        for a in soup.select('a[href*="/produit/"]'):
            href = a.get("href")
            if href and "/produit/" in href:
                liens.add(href.split("?")[0].rstrip("/") + "/")

        time.sleep(DELAI_ENTRE_REQUETES)

    print(f"\n{len(liens)} fiches produits uniques trouvées.")
    return sorted(liens)


def extraire_produit(url):
    """Récupère et parse une fiche produit individuelle."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  (erreur sur {url}: {e})")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # --- Nom du produit ---
    h1 = soup.select_one("h1.product_title, h1.entry-title, h1")
    nom = h1.get_text(strip=True) if h1 else None
    if not nom:
        return None

    # --- Description complète (onglet Description WooCommerce) ---
    desc_div = soup.select_one("#tab-description, .woocommerce-Tabs-panel--description, .woocommerce-product-details__short-description")
    description = ""
    if desc_div:
        # Récupère le texte en gardant des retours à la ligne lisibles
        description = desc_div.get_text(separator="\n", strip=True)
    else:
        # Repli : première zone de contenu principal
        contenu = soup.select_one(".entry-content, .product-content")
        description = contenu.get_text(separator="\n", strip=True) if contenu else ""

    # --- Extraction heuristique des caractéristiques techniques ---
    # (le bloc commence généralement après un titre du type "CARACTÉRISTIQUES TECHNIQUES")
    specs_techniques = ""
    match = re.search(r"(CARACT[ÉE]RISTIQUES?.*?)(?:$)", description, re.IGNORECASE | re.DOTALL)
    if match:
        specs_techniques = match.group(1).strip()

    # --- Catégories ---
    categories = [a.get_text(strip=True) for a in soup.select('a[href*="/categorie-produit/"]')]
    categories = list(dict.fromkeys(categories))  # dédoublonnage en gardant l'ordre

    # --- Image principale ---
    img = soup.select_one(".woocommerce-product-gallery__image img, .product-images img")
    image_url = None
    if img:
        image_url = img.get("data-large_image") or img.get("src")

    return {
        "nom": nom,
        "description": description[:4000],  # évite des textes démesurés
        "specs_techniques": specs_techniques[:2000],
        "categories": ", ".join(categories),
        "image_url": image_url,
        "url": url,
    }


def sauvegarder_produits(produits):
    conn = get_connection()
    cur = conn.cursor()
    inseres = 0
    ignores = 0

    for p in produits:
        if p is None:
            continue

        # Anti-doublon simple sur le nom (à adapter si tu préfères sur l'URL)
        cur.execute("SELECT id FROM produits WHERE nom = %s", (p["nom"],))
        if cur.fetchone():
            ignores += 1
            continue

        cur.execute(
            """INSERT INTO produits (nom, description, prix_unitaire, specs_techniques)
               VALUES (%s, %s, NULL, %s)""",
            (p["nom"], p["description"], p["specs_techniques"]),
        )
        inseres += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"\n{inseres} produits insérés, {ignores} déjà existants (ignorés).")


if __name__ == "__main__":
    print("Étape 1/2 : collecte des liens produits...")
    liens = recuperer_liens_produits()

    print("\nÉtape 2/2 : extraction du détail de chaque produit...")
    produits = []
    for i, url in enumerate(liens, 1):
        print(f"  [{i}/{len(liens)}] {url}")
        p = extraire_produit(url)
        if p:
            produits.append(p)
        time.sleep(DELAI_ENTRE_REQUETES)

    print(f"\n{len(produits)} produits extraits avec succès sur {len(liens)} tentés.")

    print("\nSauvegarde en base de données...")
    sauvegarder_produits(produits)