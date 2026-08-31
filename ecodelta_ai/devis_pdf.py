"""
Génération du PDF d'un devis, à partir des données déjà stockées en base
(client, lignes produits, montant total, textes IA d'introduction/conclusion).

Installation : pip install reportlab
"""

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)


VERT_ECODELTA = colors.HexColor("#16a34a")
GRIS_TEXTE = colors.HexColor("#374151")


def generer_pdf_devis(devis_data):
    """
    devis_data : dict avec les clés
        id, client_nom, client_email, client_telephone,
        lignes (liste de dicts: nom, quantite, prix_unitaire, sous_total),
        montant_total, statut, introduction_ia, conclusion_ia, date_creation
    Retourne : bytes du PDF généré.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    style_titre = ParagraphStyle(
        "TitreEcodelta", parent=styles["Heading1"],
        textColor=VERT_ECODELTA, fontSize=22, spaceAfter=4,
    )
    style_soustitre = ParagraphStyle(
        "SousTitre", parent=styles["Normal"],
        textColor=GRIS_TEXTE, fontSize=11, spaceAfter=16,
    )
    style_normal = ParagraphStyle(
        "NormalEcodelta", parent=styles["Normal"],
        textColor=GRIS_TEXTE, fontSize=10.5, leading=15, spaceAfter=10,
    )
    style_alerte = ParagraphStyle(
        "Alerte", parent=styles["Normal"],
        textColor=colors.HexColor("#92400e"), fontSize=9, spaceAfter=6,
    )

    elements = []

    # ----- En-tête -----
    elements.append(Paragraph("ECODELTA", style_titre))
    elements.append(Paragraph(
        "Énergie solaire · Sécurité périmétrique · Gestion de parking · Affichage dynamique",
        style_soustitre,
    ))
    elements.append(HRFlowable(width="100%", color=VERT_ECODELTA, thickness=1.2, spaceAfter=16))

    elements.append(Paragraph(f"<b>DEVIS N° {devis_data['id']}</b>", styles["Heading2"]))
    date_str = devis_data["date_creation"][:10] if devis_data.get("date_creation") else "—"
    elements.append(Paragraph(f"Date : {date_str}", style_normal))

    # ----- Client -----
    elements.append(Paragraph("<b>Client</b>", styles["Heading3"]))
    elements.append(Paragraph(devis_data["client_nom"], style_normal))
    if devis_data.get("client_email"):
        elements.append(Paragraph(f"Email : {devis_data['client_email']}", style_normal))
    if devis_data.get("client_telephone"):
        elements.append(Paragraph(f"Téléphone : {devis_data['client_telephone']}", style_normal))

    elements.append(Spacer(1, 8))

    # ----- Introduction IA -----
    if devis_data.get("introduction_ia"):
        elements.append(Paragraph(devis_data["introduction_ia"], style_normal))

    # ----- Tableau des lignes -----
    donnees_tableau = [["Produit", "Quantité", "Prix unitaire (MAD)", "Sous-total (MAD)"]]
    for ligne in devis_data["lignes"]:
        donnees_tableau.append([
            ligne["nom"],
            str(ligne["quantite"]),
            f"{ligne['prix_unitaire']:.2f}",
            f"{ligne['sous_total']:.2f}",
        ])

    table = Table(donnees_tableau, colWidths=[75 * mm, 25 * mm, 40 * mm, 40 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERT_ECODELTA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 10))

    # ----- Montant total -----
    style_total = ParagraphStyle(
        "Total", parent=styles["Normal"],
        fontSize=13, textColor=colors.HexColor("#111827"), alignment=2,  # droite
    )
    elements.append(Paragraph(
        f"<b>MONTANT TOTAL (HT) : {devis_data['montant_total']:.2f} MAD</b>", style_total
    ))
    elements.append(Spacer(1, 14))

    # ----- Conclusion IA -----
    if devis_data.get("conclusion_ia"):
        elements.append(Paragraph(devis_data["conclusion_ia"], style_normal))

    elements.append(Spacer(1, 14))
    elements.append(HRFlowable(width="100%", color=colors.HexColor("#e5e7eb"), thickness=0.8, spaceAfter=8))

    statut = devis_data.get("statut", "brouillon")
    if statut == "valide":
        elements.append(Paragraph("✓ Devis validé — prêt à être transmis au client.", style_normal))
    elif statut == "refuse":
        elements.append(Paragraph("✕ Devis refusé — ne pas transmettre au client.", style_alerte))
    else:
        elements.append(Paragraph(
            "⚠️ Devis généré automatiquement — statut brouillon, à valider par un responsable avant tout envoi au client.",
            style_alerte,
        ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()