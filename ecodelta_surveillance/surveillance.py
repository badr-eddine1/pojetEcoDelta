"""
Phase 5 : Surveillance automatique.

Fait tourner le pipeline complet en continu, à intervalle régulier :
    scraping (avec filtre domaines) -> nouveaux AO détectés et enregistrés
        -> scoring IA (uniquement les AO pas encore scorés)
        -> notification email (uniquement les AO pertinents pas encore notifiés)

Lancer avec : python surveillance.py
Arrêter avec : Ctrl+C

Intervalle configurable via .env : SCRAP_INTERVAL_MINUTES=10
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler

from scraper_ao import scraper_ao, sauvegarder_en_bdd
from scoring import scorer_tous_les_ao
from notifications import notifier_ao_pertinents

load_dotenv()

INTERVALLE_MINUTES = int(os.getenv("SCRAP_INTERVAL_MINUTES", "10"))


def cycle_surveillance():
    horodatage = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*60}")
    print(f"[{horodatage}] Nouveau cycle de surveillance")
    print(f"{'='*60}")

    try:
        # 1. Scraping (filtré par domaines Ecodelta, anti-doublons déjà géré)
        print("\n[1/3] Scraping des appels d'offres...")
        ao_list = scraper_ao(max_pages=15, filtrer_par_domaines=True)
        sauvegarder_en_bdd(ao_list)

        # 2. Scoring (uniquement les AO nouvellement insérés, score_ia IS NULL)
        print("\n[2/3] Scoring IA des nouveaux AO...")
        scorer_tous_les_ao(limite=500)

        # 3. Notification (uniquement les AO pertinents pas encore notifiés)
        print("\n[3/3] Vérification des notifications à envoyer...")
        notifier_ao_pertinents()

        print(f"\n[{horodatage}] Cycle terminé avec succès.")

    except Exception as e:
        # On ne laisse jamais un cycle planter tout le scheduler :
        # on logue l'erreur et on attend simplement le prochain cycle.
        print(f"\n[ERREUR] Le cycle a échoué : {e}")
        print("Le scheduler continue, nouvelle tentative au prochain cycle.")


if __name__ == "__main__":
    print(f"Démarrage de la surveillance automatique Ecodelta.")
    print(f"Intervalle configuré : {INTERVALLE_MINUTES} minute(s)")
    print(f"Appuyez sur Ctrl+C pour arrêter.\n")

    # Premier cycle immédiat, sans attendre le premier intervalle
    cycle_surveillance()

    scheduler = BlockingScheduler()
    scheduler.add_job(cycle_surveillance, "interval", minutes=INTERVALLE_MINUTES)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\nSurveillance arrêtée par l'utilisateur.")
        sys.exit(0)