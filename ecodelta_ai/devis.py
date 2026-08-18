import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from db import get_connection

load_dotenv()

client_ia = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def recuperer_client(conn, client_id):
    cur = conn.cursor()
    cur.execute("SELECT id, nom, email, telephone FROM clients WHERE id = %s;", (client_id,))
    row = cur.fetchone()
    cur.close()
    if not row:
        raise ValueError(f"Client #{client_id} introuvable")
    return {"id": row[0], "nom": row[1], "email": row[2], "telephone": row[3]}


def recuperer_produits(conn, produits_quantites):
    """produits_quantites : liste de tuples (produit_id, quantite)"""
    cur = conn.cursor()
    lignes = []
    montant_total = 0

    for produit_id, quantite in produits_quantites:
        cur.execute(
            "SELECT id, nom, description, prix_unitaire FROM produits WHERE id = %s;", (produit_id,)
        )
        row = cur.fetchone()
        if not row:
            print(f"  (produit #{produit_id} introuvable, ignoré)")
            continue

        prix_unitaire = float(row[3])
        sous_total = prix_unitaire * quantite
        montant_total += sous_total

        lignes.append({
            "produit_id": row[0],
            "nom": row[1],
            "description": row[2],
            "prix_unitaire": prix_unitaire,
            "quantite": quantite,
            "sous_total": sous_total,
        })

    cur.close()
    return lignes, montant_total


def rediger_texte_devis(client_info, lignes, montant_total):
    """Demande à l'IA de rédiger le texte de présentation du devis (pas les calculs, faits en Python)."""
    lignes_texte = "\n".join(
        f"- {l['nom']} x{l['quantite']} = {l['sous_total']:.2f} MAD" for l in lignes
    )

    prompt = f"""Tu es un assistant qui rédige l'introduction et la conclusion d'un devis commercial pour
l'entreprise Ecodelta (spécialiste énergie solaire, sécurité/contrôle d'accès, gestion de parking,
affichage dynamique, effaroucheurs, terrains de padel).

Client : {client_info['nom']}

Produits/services devisés :
{lignes_texte}

Montant total : {montant_total:.2f} MAD (HT)

Rédige :
1. Une phrase d'introduction professionnelle et personnalisée pour ce client
2. Une phrase de conclusion (validité de l'offre, invitation à contacter Ecodelta pour toute question)

Réponds UNIQUEMENT au format JSON strict, sans texte avant ou après :
{{"introduction": "<texte>", "conclusion": "<texte>"}}
"""

    response = client_ia.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        response_format={"type": "json_object"},
    )

    tokens_input = response.usage.prompt_tokens
    tokens_output = response.usage.completion_tokens

    return json.loads(response.choices[0].message.content), tokens_input, tokens_output


def formater_devis_texte(client_info, lignes, montant_total, textes):
    sortie = [
        "=" * 50,
        "DEVIS - ECODELTA",
        "=" * 50,
        f"\nClient : {client_info['nom']}",
        f"Email : {client_info['email'] or 'N/A'}  |  Tél : {client_info['telephone'] or 'N/A'}\n",
        textes["introduction"],
        "\nDétail :",
    ]
    for l in lignes:
        sortie.append(f"  - {l['nom']} x{l['quantite']} .......... {l['sous_total']:.2f} MAD")
    sortie.append(f"\nMONTANT TOTAL (HT) : {montant_total:.2f} MAD")
    sortie.append(f"\n{textes['conclusion']}")
    sortie.append("\n⚠️  Devis généré automatiquement — à valider par un responsable avant envoi au client.")
    return "\n".join(sortie)


def generer_devis(client_id, produits_quantites):
    """produits_quantites : liste de tuples (produit_id, quantite), ex: [(1, 2), (5, 1)]"""
    conn = get_connection()

    client_info = recuperer_client(conn, client_id)
    lignes, montant_total = recuperer_produits(conn, produits_quantites)

    if not lignes:
        print("Aucun produit valide, devis annulé.")
        conn.close()
        return

    textes, tok_in, tok_out = rediger_texte_devis(client_info, lignes, montant_total)

    # Sauvegarde en base (statut brouillon, à valider par un humain avant envoi)
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO devis (client_id, produits, montant_total, statut, genere_par_ia, valide_par_humain)
           VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;""",
        (client_id, json.dumps(lignes, ensure_ascii=False), montant_total, "brouillon", True, False),
    )
    devis_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    texte_final = formater_devis_texte(client_info, lignes, montant_total, textes)
    print(texte_final)

    PRIX_INPUT_PAR_MILLION = 0.15
    PRIX_OUTPUT_PAR_MILLION = 0.60
    cout = (tok_in / 1_000_000 * PRIX_INPUT_PAR_MILLION) + (tok_out / 1_000_000 * PRIX_OUTPUT_PAR_MILLION)
    print(f"\n--- Devis #{devis_id} enregistré (statut: brouillon, à valider) ---")
    print(f"--- Coût estimé : ${cout:.4f} ---")

    return devis_id


if __name__ == "__main__":
    # Exemple de test : client #1, avec 2 bornes escamotables (produit #1) et 1 caméra LAPI (produit #4)
    generer_devis(client_id=1, produits_quantites=[(1, 2), (4, 1)])