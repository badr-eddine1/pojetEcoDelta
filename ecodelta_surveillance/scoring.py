import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from db import get_connection

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def scorer_ao(titre, description, montant, secteur):
    prompt = f"""Tu es un assistant qui évalue la pertinence d'un appel d'offres pour l'entreprise Ecodelta.

PROFIL D'ECODELTA (entreprise marocaine basée à Rabat) :
Ecodelta est spécialisée UNIQUEMENT dans ces domaines :
- Énergie solaire (injection solaire, pompage solaire)
- Sécurité périmétrique et contrôle d'accès (bornes escamotables, tourniquets, couloirs rapides, portillons PMR, barrières)
- Gestion de parking (bornes d'entrée/sortie, caméras de lecture de plaques, caisses automatiques, afficheurs de places libres)
- Mur d'image / affichage dynamique (écrans TV, supports)
- Effaroucheurs laser/acoustique (protection de sites contre oiseaux/animaux)
- Construction de terrains de padel

Secteurs clients ciblés : industrie et zones industrielles, hôtellerie et tourisme, ports et infrastructures maritimes, aéroports et aviation, secteur public et infrastructures nationales.

Ecodelta NE FAIT PAS : de gros travaux de BTP/construction générale, de plomberie, de climatisation/HVAC classique, d'informatique pure, de fournitures de bureau, ni de projets sans lien avec l'énergie solaire, la sécurité/contrôle d'accès, le parking, l'affichage ou les effaroucheurs.

Appel d'offres à évaluer :
- Titre : {titre}
- Description : {description}
- Montant : {montant} MAD
- Lieu/secteur : {secteur}

CONSIGNE DE NOTATION (sois strict et discriminant) :
- Score 8-10 : correspond directement à un des domaines d'expertise d'Ecodelta (solaire, contrôle d'accès, parking, affichage, effaroucheurs, padel)
- Score 4-7 : lien indirect possible (ex. un projet dans un secteur cible comme aéroport/port/hôtel, mais sans certitude que le lot corresponde à l'expertise d'Ecodelta)
- Score 0-3 : aucun rapport avec les domaines d'Ecodelta (BTP générique, plomberie, fournitures, informatique, agriculture, etc.)

Donne un score de pertinence de 0 à 10, et une justification en 1-2 phrases qui doit citer explicitement quel domaine d'expertise d'Ecodelta est concerné (ou expliquer pourquoi aucun ne l'est).
Réponds UNIQUEMENT au format JSON strict, sans texte avant ou après :
{{"score": <nombre>, "justification": "<texte>"}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        response_format={"type": "json_object"},
    )

    tokens_input = response.usage.prompt_tokens
    tokens_output = response.usage.completion_tokens

    return response.choices[0].message.content, tokens_input, tokens_output


def scorer_tous_les_ao(limite=None, ids_specifiques=None):
    conn = get_connection()
    cur = conn.cursor()
    if ids_specifiques:
        cur.execute(
            "SELECT id, titre, description, montant, secteur FROM appels_offres WHERE id = ANY(%s) AND score_ia IS NULL;",
            (ids_specifiques,),
        )
    elif limite:
        cur.execute(
            "SELECT id, titre, description, montant, secteur FROM appels_offres WHERE score_ia IS NULL LIMIT %s;",
            (limite,),
        )
    else:
        cur.execute(
            "SELECT id, titre, description, montant, secteur FROM appels_offres WHERE score_ia IS NULL;"
        )
    rows = cur.fetchall()
    print(f"{len(rows)} AO à scorer...")

    total_input = 0
    total_output = 0

    for ao_id, titre, description, montant, secteur in rows:
        try:
            resultat_brut, tok_in, tok_out = scorer_ao(titre, description, montant, secteur)
            total_input += tok_in
            total_output += tok_out

            resultat = json.loads(resultat_brut)
            score = resultat.get("score")
            justification = resultat.get("justification")

            cur.execute(
                "UPDATE appels_offres SET score_ia = %s, justification_ia = %s WHERE id = %s",
                (score, justification, ao_id),
            )
            conn.commit()
            print(f"AO #{ao_id} -> score {score} : {justification}")

        except Exception as e:
            print(f"AO #{ao_id} -> erreur : {e}")

    # Tarifs gpt-4o-mini au 30/07/2026 (à revérifier sur https://openai.com/api/pricing/)
    PRIX_INPUT_PAR_MILLION = 0.15
    PRIX_OUTPUT_PAR_MILLION = 0.60
    cout = (total_input / 1_000_000 * PRIX_INPUT_PAR_MILLION) + (total_output / 1_000_000 * PRIX_OUTPUT_PAR_MILLION)

    print(f"\n--- Tokens de ce lot : {total_input} input / {total_output} output ---")
    print(f"--- Coût estimé de ce lot : ${cout:.4f} ---")

    cur.close()
    conn.close()


if __name__ == "__main__":
    TAILLE_LOT = 500

    while True:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM appels_offres WHERE score_ia IS NULL;")
        restants = cur.fetchone()[0]
        cur.close()
        conn.close()

        if restants == 0:
            print("\nTous les AO ont été scorés. Terminé !")
            break

        print(f"\n{restants} AO restants à scorer. Traitement d'un lot de {min(TAILLE_LOT, restants)}...")
        scorer_tous_les_ao(limite=TAILLE_LOT)

        reponse = input("\nContinuer avec le lot suivant ? (o/n) : ").strip().lower()
        if reponse != "o":
            print("Arrêt demandé. Relance le script plus tard pour continuer là où tu t'es arrêté.")
            break