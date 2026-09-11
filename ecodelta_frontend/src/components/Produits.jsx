import { useEffect, useState } from "react";
import { getProduits, creerProduit } from "../api";

export default function Produits() {
  const [produits, setProduits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [erreur, setErreur] = useState(null);
  const [detail, setDetail] = useState(null);

  const [afficherFormulaire, setAfficherFormulaire] = useState(false);
  const [nouveauNom, setNouveauNom] = useState("");
  const [nouvelleDescription, setNouvelleDescription] = useState("");
  const [nouveauPrix, setNouveauPrix] = useState("");
  const [nouvellesSpecs, setNouvellesSpecs] = useState("");
  const [envoiEnCours, setEnvoiEnCours] = useState(false);
  const [erreurFormulaire, setErreurFormulaire] = useState(null);

  function charger() {
    setLoading(true);
    getProduits()
      .then(setProduits)
      .catch((e) => setErreur(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    charger();
  }, []);

  function ouvrirDetail(produit) {
    setDetail(produit);
  }

  function fermerDetail() {
    setDetail(null);
  }

  function reinitialiserFormulaire() {
    setNouveauNom("");
    setNouvelleDescription("");
    setNouveauPrix("");
    setNouvellesSpecs("");
    setErreurFormulaire(null);
  }

  async function ajouterProduit(e) {
    e.preventDefault();
    if (!nouveauNom.trim()) {
      setErreurFormulaire("Le nom du produit est obligatoire.");
      return;
    }

    setEnvoiEnCours(true);
    setErreurFormulaire(null);
    try {
      await creerProduit({
        nom: nouveauNom.trim(),
        description: nouvelleDescription.trim() || null,
        prix_unitaire: nouveauPrix ? parseFloat(nouveauPrix) : null,
        specs_techniques: nouvellesSpecs.trim() || null,
      });
      reinitialiserFormulaire();
      setAfficherFormulaire(false);
      charger(); // recharge la liste pour inclure le nouveau produit
    } catch (e) {
      setErreurFormulaire(e.message);
    } finally {
      setEnvoiEnCours(false);
    }
  }

  if (loading) return <p>Chargement...</p>;
  if (erreur) return <p className="erreur">Erreur : {erreur}</p>;

  return (
    <div className="page">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Catalogue produits</h1>
        <button
          className="btn-principal"
          onClick={() => setAfficherFormulaire(!afficherFormulaire)}
        >
          {afficherFormulaire ? "✕ Annuler" : "+ Ajouter un produit"}
        </button>
      </div>

      <p className="compteur">
        {produits.length} produit(s) — catalogue issu du site ecodelta.ma, complété manuellement
      </p>

      {afficherFormulaire && (
        <form onSubmit={ajouterProduit} className="section">
          <h3 style={{ marginTop: 0 }}>Nouveau produit</h3>

          {erreurFormulaire && <p className="erreur">{erreurFormulaire}</p>}

          <label>Nom du produit *</label>
          <input
            type="text"
            value={nouveauNom}
            onChange={(e) => setNouveauNom(e.target.value)}
            placeholder="Ex : Borne escamotable BL-53"
            required
            style={{ width: "100%", marginBottom: 10 }}
          />

          <label>Description</label>
          <textarea
            value={nouvelleDescription}
            onChange={(e) => setNouvelleDescription(e.target.value)}
            placeholder="Description commerciale du produit..."
            rows={3}
            style={{ width: "100%", marginBottom: 10 }}
          />

          <label>Prix unitaire (MAD)</label>
          <input
            type="number"
            step="0.01"
            value={nouveauPrix}
            onChange={(e) => setNouveauPrix(e.target.value)}
            placeholder="Laisser vide si sur devis"
            style={{ width: "100%", marginBottom: 10 }}
          />

          <label>Caractéristiques techniques</label>
          <textarea
            value={nouvellesSpecs}
            onChange={(e) => setNouvellesSpecs(e.target.value)}
            placeholder="Alimentation, dimensions, matériaux..."
            rows={3}
            style={{ width: "100%", marginBottom: 14 }}
          />

          <button type="submit" className="btn-principal" disabled={envoiEnCours}>
            {envoiEnCours ? "Ajout en cours..." : "Ajouter le produit"}
          </button>
        </form>
      )}

      <div className="liste-cartes">
        {produits.map((p) => {
          const fiche = p.fiche_technique;
          return (
            <div
              key={p.id}
              className="carte carte-cliquable carte-produit"
              onClick={() => ouvrirDetail(p)}
            >
              {p.image_url && (
                <img src={p.image_url} alt={p.nom} className="image-produit" loading="lazy" />
              )}
              <h3>{fiche ? fiche.titre : p.nom}</h3>
              <p className="prix">
                {p.prix_unitaire != null
                  ? `${p.prix_unitaire.toLocaleString("fr-FR")} MAD`
                  : "Sur devis"}
              </p>
            </div>
          );
        })}
      </div>

      {detail && (
        <div className="modal-overlay" onClick={fermerDetail}>
          <div className="modal-contenu" onClick={(e) => e.stopPropagation()}>
            <button className="modal-fermer" onClick={fermerDetail}>✕</button>

            {detail.image_url && (
              <img src={detail.image_url} alt={detail.nom} className="image-produit-modal" />
            )}

            <h2>{detail.fiche_technique ? detail.fiche_technique.titre : detail.nom}</h2>
            <p className="prix">
              {detail.prix_unitaire != null
                ? `${detail.prix_unitaire.toLocaleString("fr-FR")} MAD`
                : "Sur devis"}
            </p>
            <hr />

            {detail.fiche_technique ? (
              <>
                <p>{detail.fiche_technique.presentation}</p>
                <p><strong>Caractéristiques :</strong></p>
                <ul>
                  {detail.fiche_technique.caracteristiques.map((c, i) => <li key={i}>{c}</li>)}
                </ul>
                <p><strong>Applications recommandées :</strong></p>
                <p>{detail.fiche_technique.applications}</p>
              </>
            ) : (
              <>
                <p><strong>Description :</strong></p>
                <p>{detail.description || "Aucune description disponible."}</p>
                {detail.specs_techniques && (
                  <>
                    <p><strong>Caractéristiques techniques :</strong></p>
                    <p>{detail.specs_techniques}</p>
                  </>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}