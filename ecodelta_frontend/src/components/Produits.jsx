import { useEffect, useState } from "react";
import { getProduits } from "../api";

export default function Produits() {
  const [produits, setProduits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [erreur, setErreur] = useState(null);
  const [detail, setDetail] = useState(null);

  useEffect(() => {
    getProduits()
      .then(setProduits)
      .catch((e) => setErreur(e.message))
      .finally(() => setLoading(false));
  }, []);

  function ouvrirDetail(produit) {
    setDetail(produit);
  }

  function fermerDetail() {
    setDetail(null);
  }

  if (loading) return <p>Chargement...</p>;
  if (erreur) return <p className="erreur">Erreur : {erreur}</p>;

  return (
    <div className="page">
      <h1>Catalogue produits</h1>
      <p className="compteur">{produits.length} produit(s) — clique sur une carte pour voir le détail</p>

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
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
