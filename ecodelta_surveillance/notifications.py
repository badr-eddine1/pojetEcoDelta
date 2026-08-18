"""
Phase 4 (révisée) : Notification email des nouveaux appels d'offres pertinents.

Un seul email récapitulatif est envoyé par cycle, listant tous les AO
pertinents détectés depuis le dernier envoi — plutôt qu'un email par AO,
pour éviter de noyer la boîte mail d'Ecodelta.

Ne notifie jamais deux fois le même AO, grâce au champ notification_envoyee
vérifié avant envoi.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from db import get_connection

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_DESTINATAIRE = os.getenv("NOTIFICATION_EMAIL_TO")
SEUIL_NOTIFICATION = float(os.getenv("SEUIL_NOTIFICATION", "7"))


def construire_email_recapitulatif(ao_list):
    """ao_list : liste de tuples (id, titre, lien, secteur, date_limite, score_ia, justification_ia)"""
    nb = len(ao_list)
    intro = (
        f"🚨 {nb} nouvel(le)(s) appel(s) d'offres pertinent(s) pour Ecodelta\n"
        f"{'=' * 60}\n\n"
    )

    blocs = []
    for ao in ao_list:
        ao_id, titre, lien, secteur, date_limite, score, justification = ao
        blocs.append(
            f"Score : {score}/10\n"
            f"Objet : {titre}\n"
            f"Référence : {lien or 'N/A'}\n"
            f"Lieu : {secteur or 'N/A'}\n"
            f"Date limite : {date_limite or 'N/A'}\n"
            f"Justification : {justification}\n"
            f"{'-' * 60}"
        )

    pied = (
        "\n\nConsulter le portail des marchés publics :\n"
        "https://www.marchespublics.gov.ma\n\n"
        "---\n"
        "Notification automatique générée par le système de veille Ecodelta."
    )

    corps = intro + "\n\n".join(blocs) + pied

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_DESTINATAIRE
    if nb == 1:
        msg["Subject"] = f"🚨 1 nouvel AO pertinent : {ao_list[0][1][:60]}"
    else:
        msg["Subject"] = f"🚨 {nb} nouveaux appels d'offres pertinents pour Ecodelta"
    msg.attach(MIMEText(corps, "plain", "utf-8"))
    return msg


def envoyer_email(msg):
    if not SMTP_USER or not SMTP_PASSWORD or not EMAIL_DESTINATAIRE:
        print("  (SMTP_USER / SMTP_PASSWORD / NOTIFICATION_EMAIL_TO manquants dans .env — email non envoyé)")
        return False
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"  (échec envoi email: {e})")
        return False


def notifier_ao_pertinents():
    """
    Cherche tous les AO pertinents (score >= seuil) pas encore notifiés,
    envoie UN SEUL email récapitulatif les listant tous, puis marque
    notification_envoyee = TRUE pour chacun (pour ne jamais les renotifier).
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT id, titre, lien, secteur, date_limite, score_ia, justification_ia
           FROM appels_offres
           WHERE score_ia >= %s
             AND (notification_envoyee IS FALSE OR notification_envoyee IS NULL)
           ORDER BY score_ia DESC;""",
        (SEUIL_NOTIFICATION,),
    )
    a_notifier = cur.fetchall()

    if not a_notifier:
        print("  Aucun nouvel AO pertinent à notifier.")
        cur.close()
        conn.close()
        return

    print(f"  {len(a_notifier)} AO pertinent(s) à regrouper dans un seul email...")

    msg = construire_email_recapitulatif(a_notifier)
    succes = envoyer_email(msg)

    if succes:
        ids = [ao[0] for ao in a_notifier]
        cur.execute(
            "UPDATE appels_offres SET notification_envoyee = TRUE, date_notification = NOW() WHERE id = ANY(%s)",
            (ids,),
        )
        conn.commit()
        print(f"  -> Email récapitulatif envoyé ({len(a_notifier)} AO), tous marqués comme notifiés.")
    else:
        print("  -> Échec de l'envoi, les AO seront retentés au prochain cycle.")

    cur.close()
    conn.close()


if __name__ == "__main__":
    notifier_ao_pertinents()