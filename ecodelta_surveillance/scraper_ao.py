from playwright.sync_api import sync_playwright
from datetime import datetime
from db import get_connection
from domaines import selectionner_domaines_ecodelta

URL_ACCUEIL = "https://www.marchespublics.gov.ma"


def parser_ao(ligne):
    ref_el = ligne.query_selector('td[headers="cons_ref"]')
    titre_el = ligne.query_selector('td[headers="cons_intitule"]')
    lieu_el = ligne.query_selector('td[headers="cons_lieuExe"]')
    date_el = ligne.query_selector('td[headers="cons_dateEnd"]')

    if not (ref_el and titre_el):
        return None

    lignes_titre = [l.strip() for l in titre_el.inner_text().strip().split("\n") if l.strip()]
    reference_reelle = lignes_titre[0] if lignes_titre else None
    objet = None
    acheteur = None
    for l in lignes_titre:
        if l.startswith("Objet :"):
            objet = l.replace("Objet :", "").strip()
        if l.startswith("Acheteur public :"):
            acheteur = l.replace("Acheteur public :", "").strip()

    lieu_texte = lieu_el.inner_text().strip() if lieu_el else ""
    lignes_lieu = [l.strip() for l in lieu_texte.split("\n") if l.strip() and l.strip() != "-"]
    lieu_reel = lignes_lieu[-1] if lignes_lieu else None

    date_texte = date_el.inner_text().strip() if date_el else ""
    lignes_date = [l.strip() for l in date_texte.split("\n") if l.strip()]
    date_reelle = lignes_date[0] if lignes_date else None

    return {
        "reference": reference_reelle,
        "titre": objet,
        "acheteur": acheteur,
        "lieu": lieu_reel,
        "date_limite": date_reelle,
    }


def convertir_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    except ValueError:
        return None


def extraire_page_courante(page):
    for tentative in range(3):
        try:
            page.wait_for_selector('td[headers="cons_ref"]', timeout=20000)
            lignes = page.query_selector_all("tr")
            resultats = []
            for ligne in lignes:
                ao = parser_ao(ligne)
                if ao and ao["titre"]:
                    resultats.append(ao)
            return resultats
        except Exception as e:
            print(f"  (tentative {tentative + 1}/3 échouée: {e}, nouvelle tentative dans 2s...)")
            page.wait_for_timeout(2000)
    print("  (échec définitif de lecture de la page)")
    return []


def aller_page_suivante(page):
    selecteur = 'img[alt="Aller à la page suivante"]'
    el = page.query_selector(selecteur)
    if not el:
        return False
    try:
        el.click()
        page.wait_for_timeout(3000)
        return True
    except Exception as e:
        print(f"  (impossible d'aller à la page suivante: {e})")
        return False


def scraper_ao(max_pages=15, filtrer_par_domaines=True):
    resultats = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL_ACCUEIL)
        page.wait_for_timeout(2000)

        page.click("text=Recherche avancée >> nth=0")
        page.wait_for_timeout(2000)

        # ----- PHASE 1 : filtrage par domaines d'activité Ecodelta -----
        if filtrer_par_domaines:
            print("Sélection des domaines d'activité Ecodelta...")
            ok = selectionner_domaines_ecodelta(page)
            if not ok:
                print("  (filtrage par domaines échoué — poursuite SANS filtre, "
                      "à corriger : voir domaines.py)")
        # -----------------------------------------------------------------

        page.click("#ctl0_CONTENU_PAGE_AdvancedSearch_lancerRecherche")
        page.wait_for_timeout(3000)

        try:
            page.select_option("#ctl0_CONTENU_PAGE_resultSearch_listePageSizeTop", "500")
        except Exception as e:
            print(f"  (select 500/page: {e}, on continue quand même)")
        page.wait_for_timeout(2000)

        page_num = 1
        while page_num <= max_pages:
            print(f"  -> Lecture page {page_num}...")
            nouveaux = extraire_page_courante(page)
            resultats.extend(nouveaux)

            a_continue = aller_page_suivante(page)
            if not a_continue:
                print(f"  -> Fin de la pagination (page {page_num} était la dernière)")
                break
            page_num += 1

        browser.close()

    return resultats


def sauvegarder_en_bdd(ao_list):
    conn = get_connection()
    cur = conn.cursor()
    inseres = 0
    ignores = 0

    for ao in ao_list:
        cur.execute("SELECT id FROM appels_offres WHERE lien = %s", (ao["reference"],))
        if cur.fetchone():
            ignores += 1
            continue

        cur.execute(
            """INSERT INTO appels_offres
               (titre, description, secteur, date_limite, lien, source, statut)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                ao["titre"],
                f"Acheteur public : {ao['acheteur']}" if ao["acheteur"] else None,
                ao["lieu"],
                convertir_date(ao["date_limite"]),
                ao["reference"],
                "marchespublics.gov.ma",
                "nouveau",
            ),
        )
        inseres += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"{inseres} AO insérés, {ignores} déjà existants (ignorés)")


if __name__ == "__main__":
    ao_list = scraper_ao(max_pages=15, filtrer_par_domaines=True)
    print(f"\n{len(ao_list)} AO trouvés (après filtrage par domaines)\n")

    for ao in ao_list[:5]:
        print(ao)

    print("\nSauvegarde en base de données...")
    sauvegarder_en_bdd(ao_list)