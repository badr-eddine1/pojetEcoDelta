import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from db import get_connection

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generer_fiche_technique(nom, description, prix_unitaire, specs_techniques):
    prompt = f"""Tu es un assistant qui rédige des fiches techniques commerciales pour l'entreprise Ecodelta
(spécialiste marocaine en énergie solaire, sécurité périmétrique/contrôle d'accès, gestion de parking,
affichage dynamique, effaroucheurs et terrains de padel).

Rédige une fiche technique professionnelle et vendeuse pour ce produit, à partir des informations suivantes :
- Nom : {nom}
- Description : {description}
- Prix unitaire : {prix_unitaire} MAD
- Caractéristiques techniques : {specs_techniques}

La fiche doit contenir :
1. Un titre accrocheur (reprenant le nom du produit)
2. Un court paragraphe de présentation (2-3 phrases, orienté bénéfices client)
3. Une liste des caractéristiques techniques, bien formatée
4. Un paragraphe "Applications recommandées"
5. Le prix indicatif

CONSIGNE IMPORTANTE pour les applications recommandées :
Les secteurs clients possibles sont : industrie/zones industrielles, hôtellerie/tourisme, ports/infrastructures
maritimes, aéroports/aviation, secteur public/infrastructures nationales, terrains de sport (pour le padel).
Ne cite JAMAIS tous ces secteurs par défaut. Choisis UNIQUEMENT les 2 à 3 secteurs les plus pertinents pour
CE produit précis, et explique brièvement pourquoi ce produit y est particulièrement utile (pas juste "adapté à").
Par exemple : un effaroucheur anti-volatiles est surtout utile en agriculture/aéroports (risque aviaire), pas
vraiment en hôtellerie de centre-ville. Un mur d'image est surtout utile en hôtellerie/événementiel/secteur
public pour la communication visuelle, pas forcément dans un port industriel. Sois spécifique et sélectif.

Réponds UNIQUEMENT au format JSON strict, sans texte avant ou après, avec cette structure exacte :
{{
  "titre": "<titre accrocheur>",
  "presentation": "<paragraphe de présentation>",
  "caracteristiques": ["<caractéristique 1>", "<caractéristique 2>", "..."],
  "applications": "<paragraphe applications recommandées, 2-3 secteurs max, justifiés>",
  "prix_indicatif": "<prix formaté avec devise>"
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
        response_format={"type": "json_object"},
    )

    tokens_input = response.usage.prompt_tokens
    tokens_output = response.usage.completion_tokens

    return response.choices[0].message.content, tokens_input, tokens_output


def formater_fiche_texte(fiche):
    """Transforme le JSON de la fiche en texte lisible (utile pour aperçu ou export)."""
    lignes = [
        f"=== {fiche['titre']} ===\n",
        f"{fiche['presentation']}\n",
        "Caractéristiques techniques :",
    ]
    for c in fiche["caracteristiques"]:
        lignes.append(f"  - {c}")
    lignes.append(f"\nApplications recommandées :\n{fiche['applications']}")
    lignes.append(f"\nPrix indicatif : {fiche['prix_indicatif']}")
    return "\n".join(lignes)


def generer_toutes_les_fiches():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, nom, description, prix_unitaire, specs_techniques FROM produits WHERE fiche_technique IS NULL;"
    )
    rows = cur.fetchall()
    print(f"{len(rows)} produits à traiter...")

    total_input = 0
    total_output = 0

    for produit_id, nom, description, prix_unitaire, specs_techniques in rows:
        try:
            resultat_brut, tok_in, tok_out = generer_fiche_technique(
                nom, description, prix_unitaire, specs_techniques
            )
            total_input += tok_in
            total_output += tok_out

            fiche = json.loads(resultat_brut)
            fiche_texte = formater_fiche_texte(fiche)

            cur.execute(
                "UPDATE produits SET fiche_technique = %s WHERE id = %s",
                (json.dumps(fiche, ensure_ascii=False), produit_id),
            )
            conn.commit()
            print(f"\nProduit #{produit_id} ({nom}) -> fiche générée :\n{fiche_texte}\n{'-'*50}")

        except Exception as e:
            print(f"Produit #{produit_id} -> erreur : {e}")

    PRIX_INPUT_PAR_MILLION = 0.15
    PRIX_OUTPUT_PAR_MILLION = 0.60
    cout = (total_input / 1_000_000 * PRIX_INPUT_PAR_MILLION) + (total_output / 1_000_000 * PRIX_OUTPUT_PAR_MILLION)

    print(f"\n--- Tokens utilisés : {total_input} input / {total_output} output ---")
    print(f"--- Coût estimé : ${cout:.4f} ---")

    cur.close()
    conn.close()


if __name__ == "__main__":
    generer_toutes_les_fiches()