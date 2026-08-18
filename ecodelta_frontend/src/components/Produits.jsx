import { useEffect, useState } from "react";
import { getProduits } from "../api";

export default function Produits() {
  const [produits, setProduits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [erreur, setErreur] = useState(null);

  useEffect(() => {
    getProduits()
      .then(setProduits)
      .catch((e) => setErreur(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Chargement...</p>;
  if (erreur) return <p className="erreur">Erreur : {erreur}</p>;

  return (
    <div className="page">
      <h1>Catalogue produits</h1>
      <div className="liste-cartes">
        {produits.map((p) => {
          const fiche = p.fiche_technique;
          return (
            <div key={p.id} className="carte carte-produit">
              <h3>{fiche ? fiche.titre : p.nom}</h3>
              <p className="prix">{p.prix_unitaire.toLocaleString("fr-FR")} MAD</p>

              {fiche ? (
                <>
                  <p>{fiche.presentation}</p>
                  <strong>Caractéristiques :</strong>
                  <ul>
                    {fiche.caracteristiques.map((c, i) => <li key={i}>{c}</li>)}
                  </ul>
                  <strong>Applications :</strong>
                  <p>{fiche.applications}</p>
                </>
              ) : (
                <p>{p.description}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
