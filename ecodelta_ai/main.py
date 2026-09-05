from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json

from db import get_connection
from devis import recuperer_client, recuperer_produits, rediger_texte_devis
from devis_pdf import generer_pdf_devis
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm
from auth import verifier_mot_de_passe, creer_token, get_current_user

app = FastAPI(title="Ecodelta API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    email = form_data.username.strip().lower()  # normalisation : évite les faux 401 dus à la casse

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT mot_de_passe_hash FROM users WHERE email = %s;", (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row or not verifier_mot_de_passe(form_data.password, row[0]):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    token = creer_token(email)
    return {"access_token": token, "token_type": "bearer"}


class ProduitDevis(BaseModel):
    produit_id: int
    quantite: int


class DevisCreate(BaseModel):
    client_id: int
    produits: list[ProduitDevis]


class ClientCreate(BaseModel):
    nom: str
    email: Optional[str] = None
    telephone: Optional[str] = None


class DevisValidation(BaseModel):
    valide: bool


COLONNES_AO = [
    "id", "titre", "secteur", "montant", "date_limite", "score_ia",
    "justification_ia", "lien", "statut", "date_detection", "notification_envoyee",
]
SELECT_AO = (
    "SELECT id, titre, secteur, montant, date_limite, score_ia, "
    "justification_ia, lien, statut, date_detection, notification_envoyee "
    "FROM appels_offres"
)


def _formatter_ao(row):
    d = dict(zip(COLONNES_AO, row))
    d["montant"] = float(d["montant"]) if d["montant"] is not None else None
    d["date_limite"] = d["date_limite"].isoformat() if d["date_limite"] else None
    d["date_detection"] = d["date_detection"].isoformat() if d["date_detection"] else None
    return d


# ---------- Appels d'offres : vue générale ----------

@app.get("/appels-offres", dependencies=[Depends(get_current_user)])
def liste_appels_offres(score_min: Optional[float] = None, limit: int = 100):
    """Vue 'Tous' : liste complète, filtrable par score minimum."""
    conn = get_connection()
    cur = conn.cursor()
    if score_min is not None:
        cur.execute(f"{SELECT_AO} WHERE score_ia >= %s ORDER BY score_ia DESC LIMIT %s;", (score_min, limit))
    else:
        cur.execute(f"{SELECT_AO} ORDER BY date_detection DESC NULLS LAST LIMIT %s;", (limit,))
    resultats = [_formatter_ao(row) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return resultats


# ---------- Appels d'offres : vue "Nouveaux" ----------

@app.get("/appels-offres/nouveaux", dependencies=[Depends(get_current_user)])
def liste_nouveaux_appels_offres(heures: int = 24, limit: int = 200):
    """
    Vue 'Nouveaux' : AO détectés récemment (par défaut les dernières 24h),
    peu importe leur score — utile pour voir ce que le dernier cycle a capté.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        f"{SELECT_AO} WHERE date_detection >= NOW() - (%s || ' hours')::interval "
        f"ORDER BY date_detection DESC LIMIT %s;",
        (heures, limit),
    )
    resultats = [_formatter_ao(row) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return resultats


# ---------- Appels d'offres : vue "Pertinents" ----------

@app.get("/appels-offres/pertinents", dependencies=[Depends(get_current_user)])
def liste_ao_pertinents(seuil: float = 7, limit: int = 200):
    """Vue 'Pertinents' : score_ia >= seuil (7 par défaut, aligné sur SEUIL_NOTIFICATION)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"{SELECT_AO} WHERE score_ia >= %s ORDER BY score_ia DESC LIMIT %s;", (seuil, limit))
    resultats = [_formatter_ao(row) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return resultats


# ---------- Appels d'offres : vue "Non pertinents" ----------

@app.get("/appels-offres/non-pertinents", dependencies=[Depends(get_current_user)])
def liste_ao_non_pertinents(seuil: float = 7, limit: int = 200):
    """Vue 'Non pertinents' : AO déjà scorés mais sous le seuil."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        f"{SELECT_AO} WHERE score_ia IS NOT NULL AND score_ia < %s "
        f"ORDER BY date_detection DESC LIMIT %s;",
        (seuil, limit),
    )
    resultats = [_formatter_ao(row) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return resultats


@app.get("/appels-offres/{ao_id}", dependencies=[Depends(get_current_user)])
def detail_appel_offre(ao_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, titre, description, secteur, montant, date_limite, score_ia, "
        "justification_ia, lien, statut, date_detection, notification_envoyee, date_notification "
        "FROM appels_offres WHERE id = %s;",
        (ao_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Appel d'offres introuvable")
    colonnes = COLONNES_AO[:2] + ["description"] + COLONNES_AO[2:] + ["date_notification"]
    # reconstruction propre (description insérée après titre)
    colonnes = ["id", "titre", "description", "secteur", "montant", "date_limite", "score_ia",
                "justification_ia", "lien", "statut", "date_detection", "notification_envoyee",
                "date_notification"]
    d = dict(zip(colonnes, row))
    d["montant"] = float(d["montant"]) if d["montant"] is not None else None
    for champ in ["date_limite", "date_detection", "date_notification"]:
        if d.get(champ):
            d[champ] = d[champ].isoformat()
    return d


# ---------- Produits ----------
@app.get("/produits", dependencies=[Depends(get_current_user)])
def liste_produits():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, nom, description, prix_unitaire, specs_techniques, fiche_technique, image_url FROM produits;"
    )
    colonnes = ["id", "nom", "description", "prix_unitaire", "specs_techniques", "fiche_technique", "image_url"]
    resultats = []
    for row in cur.fetchall():
        d = dict(zip(colonnes, row))
        d["prix_unitaire"] = float(d["prix_unitaire"]) if d["prix_unitaire"] is not None else None
        resultats.append(d)
    cur.close()
    conn.close()
    return resultats


# ---------- Clients ----------

@app.get("/clients", dependencies=[Depends(get_current_user)])
def liste_clients():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nom, email, telephone, statut FROM clients;")
    colonnes = ["id", "nom", "email", "telephone", "statut"]
    resultats = [dict(zip(colonnes, row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return resultats


@app.post("/clients", dependencies=[Depends(get_current_user)])
def creer_client(client: ClientCreate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO clients (nom, email, telephone, statut) VALUES (%s, %s, %s, 'nouveau') RETURNING id;",
        (client.nom, client.email, client.telephone),
    )
    client_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"id": client_id, "message": "Client créé"}


# ---------- Devis ----------

@app.get("/devis", dependencies=[Depends(get_current_user)])
def liste_devis():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT d.id, c.nom, d.montant_total, d.statut, d.valide_par_humain, d.date_creation
           FROM devis d JOIN clients c ON d.client_id = c.id
           ORDER BY d.date_creation DESC;"""
    )
    colonnes = ["id", "client_nom", "montant_total", "statut", "valide_par_humain", "date_creation"]
    resultats = []
    for row in cur.fetchall():
        d = dict(zip(colonnes, row))
        d["montant_total"] = float(d["montant_total"]) if d["montant_total"] is not None else None
        d["date_creation"] = d["date_creation"].isoformat() if d["date_creation"] else None
        resultats.append(d)
    cur.close()
    conn.close()
    return resultats


@app.post("/devis", dependencies=[Depends(get_current_user)])
def creer_devis(devis: DevisCreate):
    conn = get_connection()
    try:
        client_info = recuperer_client(conn, devis.client_id)
    except ValueError:
        conn.close()
        raise HTTPException(status_code=404, detail="Client introuvable")

    produits_quantites = [(p.produit_id, p.quantite) for p in devis.produits]
    lignes, montant_total = recuperer_produits(conn, produits_quantites)

    if not lignes:
        conn.close()
        raise HTTPException(status_code=400, detail="Aucun produit valide fourni")

    textes, tok_in, tok_out = rediger_texte_devis(client_info, lignes, montant_total)

    cur = conn.cursor()
    cur.execute(
        """INSERT INTO devis (client_id, produits, montant_total, statut, genere_par_ia,
                               valide_par_humain, introduction_ia, conclusion_ia)
           VALUES (%s, %s, %s, 'brouillon', TRUE, FALSE, %s, %s) RETURNING id;""",
        (devis.client_id, json.dumps(lignes, ensure_ascii=False), montant_total,
         textes["introduction"], textes["conclusion"]),
    )
    devis_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return {
        "id": devis_id,
        "client": client_info["nom"],
        "lignes": lignes,
        "montant_total": montant_total,
        "introduction": textes["introduction"],
        "conclusion": textes["conclusion"],
        "statut": "brouillon",
        "valide_par_humain": False,
    }


@app.patch("/devis/{devis_id}/valider", dependencies=[Depends(get_current_user)])
def valider_devis(devis_id: int, validation: DevisValidation):
    conn = get_connection()
    cur = conn.cursor()
    nouveau_statut = "valide" if validation.valide else "refuse"
    cur.execute(
        "UPDATE devis SET valide_par_humain = %s, statut = %s WHERE id = %s RETURNING id;",
        (validation.valide, nouveau_statut, devis_id),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Devis introuvable")
    return {"id": devis_id, "statut": nouveau_statut}


@app.get("/devis/{devis_id}/pdf", dependencies=[Depends(get_current_user)])
def telecharger_devis_pdf(devis_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT d.id, c.nom, c.email, c.telephone, d.produits, d.montant_total,
                  d.statut, d.introduction_ia, d.conclusion_ia, d.date_creation
           FROM devis d JOIN clients c ON d.client_id = c.id
           WHERE d.id = %s;""",
        (devis_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Devis introuvable")

    devis_data = {
        "id": row[0],
        "client_nom": row[1],
        "client_email": row[2],
        "client_telephone": row[3],
        "lignes": row[4],
        "montant_total": float(row[5]),
        "statut": row[6],
        "introduction_ia": row[7],
        "conclusion_ia": row[8],
        "date_creation": row[9].isoformat() if row[9] else None,
    }

    pdf_bytes = generer_pdf_devis(devis_data)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="devis_{devis_id}.pdf"'},
    )


# ---------- Statistiques de surveillance ----------

@app.get("/surveillance/stats", dependencies=[Depends(get_current_user)])
def stats_surveillance():
    """Petit tableau de bord : combien de nouveaux/pertinents/notifiés, utile pour le frontend."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT
             COUNT(*) FILTER (WHERE date_detection >= NOW() - INTERVAL '24 hours') AS nouveaux_24h,
             COUNT(*) FILTER (WHERE score_ia >= 7) AS pertinents,
             COUNT(*) FILTER (WHERE notification_envoyee IS TRUE) AS notifies,
             COUNT(*) AS total
           FROM appels_offres;"""
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return {
        "nouveaux_dernieres_24h": row[0],
        "pertinents": row[1],
        "notifies": row[2],
        "total": row[3],
    }


@app.get("/")
def racine():
    return {"message": "API Ecodelta en ligne", "docs": "/docs"}