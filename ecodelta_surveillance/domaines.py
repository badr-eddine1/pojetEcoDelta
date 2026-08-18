"""
Phase 1 : Filtrage automatique par domaines d'activité Ecodelta.

Ce module ouvre la popup "Domaines d'activité" du portail des marchés publics,
coche automatiquement les domaines pertinents pour Ecodelta, valide la sélection,
puis revient sur le formulaire de recherche avancée pour lancer la recherche.

IMPORTANT : les codes ci-dessous ont été identifiés à partir du HTML réel de la
popup (fourni le 16/08/2026). Aucune catégorie "énergie solaire" ou "parking"
explicite n'existe dans l'arborescence du portail — ces activités semblent
couvertes par des catégories plus larges (électricité, hydraulique, automatisme).
À ajuster si de nouveaux codes pertinents sont identifiés.
"""

# Codes de domaines retenus pour Ecodelta (privilégie le recall : en cas de doute,
# on inclut, le scoring IA fera le tri fin ensuite)
DOMAINES_ECODELTA = [
    "1.16.5",   # Travaux d'installation d'équipements de contrôle d'accès
    "1.16.11",  # Travaux d'automatisme
    "1.17.3",   # Travaux d'installation pour usage industriel
    "1.17.4",   # Travaux d'éclairage publics
    "1.21.13",  # Installation d'équipements hydro-électromécaniques (ouvrages hydrauliques)
    "1.21.14",  # Installation d'équipements hydro-électromécaniques (stations de pompage)
    "2.20.5",   # Appareils d'éclairage
    "2.20.1",   # Équipements audio-visuel / communication / télécommunication
]


def selectionner_domaines_ecodelta(page):
    """
    Ouvre la popup 'Domaines d'activité' depuis la page de recherche avancée
    (page doit déjà être sur le formulaire de recherche avancée), coche les
    domaines pertinents pour Ecodelta, et valide.

    Retourne True si la sélection a réussi, False sinon (le script appelant
    peut alors décider de continuer sans filtre par domaine, en dernier recours).
    """
    try:
        # Le bouton "Définir" de la ligne "Domaines d'activité" est le 2e bouton
        # "Définir" de la page (après celui de "Lieu d'exécution" qui s'appelle
        # "Détails", donc index 0 = Domaines d'activité). À VÉRIFIER/AJUSTER si
        # le clic ouvre la mauvaise popup.
        with page.expect_popup(timeout=10000) as popup_info:
            page.click("text=Définir >> nth=0")
        popup = popup_info.value
        popup.wait_for_load_state()
        popup.wait_for_timeout(1000)

        coches = 0
        for code in DOMAINES_ECODELTA:
            try:
                trouve = popup.evaluate(
                    """(valeur) => {
                        const el = document.querySelector(`input[value="${valeur}"]`);
                        if (el) {
                            el.checked = true;
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                            el.dispatchEvent(new Event('click', { bubbles: true }));
                            return true;
                        }
                        return false;
                    }""",
                    code,
                )
                if trouve:
                    coches += 1
                else:
                    print(f"  (domaine {code} introuvable dans le DOM de la popup)")
            except Exception as e:
                print(f"  (erreur lors du cochage du domaine {code}: {e})")

        print(f"  -> {coches}/{len(DOMAINES_ECODELTA)} domaines cochés")

        if coches == 0:
            print("  (aucun domaine coché, abandon de la validation dans la popup)")
            return False

        # Valider la sélection dans la popup
        try:
            popup.click("#ctl0_CONTENU_PAGE_validateButton")
            popup.wait_for_timeout(1500)
        except Exception as e:
            print(f"  (la popup s'est peut-être déjà fermée après validation: {e})")

        return True

    except Exception as e:
        print(f"  (échec de la sélection des domaines: {e})")
        return False