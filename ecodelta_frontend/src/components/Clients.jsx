import { useEffect, useState } from "react";
import { getClients, getProduits, creerDevis, getDevis, validerDevis } from "../api";

export default function Clients() {
  const [clients, setClients] = useState([]);
  const [produits, setProduits] = useState([]);
  const [devisListe, setDevisListe] = useState([]);
  const [loading, setLoading] = useState(true);

  const [clientSelectionne, setClientSelectionne] = useState("");
  const [lignesDevis, setLignesDevis] = useState([{ produit_id: "", quantite: 1 }]);
  const [devisGenere, setDevisGenere] = useState(null);
  const [genereEnCours, setGenereEnCours] = useState(false);
  const [erreur, setErreur] = useState(null);

  useEffect(() => {
    charger();
  }, []);

  function charger() {
    setLoading(true);
    Promise.all([getClients(), getProduits(), getDevis()])
      .then(([c, p, d]) => {
        setClients(c);
        setProduits(p);
        setDevisListe(d);
      })
      .catch((e) => setErreur(e.message))
      .finally(() => setLoading(false));
  }

  function ajouterLigne() {
    setLignesDevis([...lignesDevis, { produit_id: "", quantite: 1 }]);
  }

  function modifierLigne(index, champ, valeur) {
    const copie = [...lignesDevis];
    copie[index][champ] = valeur;
    setLignesDevis(copie);
  }

  function supprimerLigne(index) {
    setLignesDevis(lignesDevis.filter((_, i) => i !== index));
  }

  async function genererDevis() {
    setErreur(null);
    if (!clientSelectionne) {
      setErreur("Choisis un client");
      return;
    }
    const produitsValides = lignesDevis
      .filter((l) => l.produit_id && l.quantite > 0)
      .map((l) => ({ produit_id: Number(l.produit_id), quantite: Number(l.quantite) }));

    if (produitsValides.length === 0) {
      setErreur("Ajoute au moins un produit");
      return;
    }

    setGenereEnCours(true);
    try {
      const resultat = await creerDevis(Number(clientSelectionne), produitsValides);
      setDevisGenere(resultat);
      charger();
    } catch (e) {
      setErreur(e.message);
    } finally {
      setGenereEnCours(false);
    }
  }

  async function marquerValide(devisId, valide) {
    await validerDevis(devisId, valide);
    charger();
  }

  if (loading) return <p>Chargement...</p>;

  return (
    <div className="page">
      <h1>Clients & Devis</h1>
      {erreur && <p className="erreur">{erreur}</p>}

      <div className="section">
        <h2>Générer un devis</h2>

        <label>
          Client :{" "}
          <select value={clientSelectionne} onChange={(e) => setClientSelectionne(e.target.value)}>
            <option value="">-- Choisir un client --</option>
            {clients.map((c) => (
              <option key={c.id} value={c.id}>{c.nom}</option>
            ))}
          </select>
        </label>

        <h3>Produits</h3>
        {lignesDevis.map((ligne, index) => (
          <div key={index} className="ligne-produit">
            <select
              value={ligne.produit_id}
              onChange={(e) => modifierLigne(index, "produit_id", e.target.value)}
            >
              <option value="">-- Produit --</option>
              {produits.map((p) => (
                <option key={p.id} value={p.id}>{p.nom} ({p.prix_unitaire} MAD)</option>
              ))}
            </select>
            <input
              type="number"
              min="1"
              value={ligne.quantite}
              onChange={(e) => modifierLigne(index, "quantite", e.target.value)}
            />
            <button onClick={() => supprimerLigne(index)} className="btn-supprimer">✕</button>
          </div>
        ))}
        <button onClick={ajouterLigne} className="btn-secondaire">+ Ajouter un produit</button>

        <div className="actions">
          <button onClick={genererDevis} disabled={genereEnCours} className="btn-principal">
            {genereEnCours ? "Génération..." : "Générer le devis"}
          </button>
        </div>

        {devisGenere && (
          <div className="devis-resultat">
            <h3>Devis #{devisGenere.id} — {devisGenere.client}</h3>
            <p>{devisGenere.introduction}</p>
            <ul>
              {devisGenere.lignes.map((l, i) => (
                <li key={i}>{l.nom} x{l.quantite} = {l.sous_total.toLocaleString("fr-FR")} MAD</li>
              ))}
            </ul>
            <p className="montant-total">Total : {devisGenere.montant_total.toLocaleString("fr-FR")} MAD</p>
            <p>{devisGenere.conclusion}</p>
            <p className="alerte">⚠️ Devis généré par IA — statut : brouillon, à valider avant envoi</p>
          </div>
        )}
      </div>

      <div className="section">
        <h2>Répertoire clients</h2>
        <table>
          <thead>
            <tr><th>Nom</th><th>Email</th><th>Téléphone</th><th>Statut</th></tr>
          </thead>
          <tbody>
            {clients.map((c) => (
              <tr key={c.id}>
                <td>{c.nom}</td>
                <td>{c.email ? <a href={`mailto:${c.email}`}>{c.email}</a> : "—"}</td>
                <td>{c.telephone ? <a href={`tel:${c.telephone}`}>{c.telephone}</a> : "—"}</td>
                <td><span className="badge badge-brouillon">{c.statut}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="section">
        <h2>Historique des devis</h2>
        <table>
          <thead>
            <tr><th>ID</th><th>Client</th><th>Contact</th><th>Montant</th><th>Statut</th><th>Action</th></tr>
          </thead>
          <tbody>
            {devisListe.map((d) => {
              const clientInfo = clients.find((c) => c.nom === d.client_nom);
              return (
                <tr key={d.id}>
                  <td>{d.id}</td>
                  <td>{d.client_nom}</td>
                  <td>
                    {clientInfo?.email && (
                      <a href={`mailto:${clientInfo.email}`} className="lien-contact" title="Envoyer un email">
                        ✉️
                      </a>
                    )}
                    {clientInfo?.telephone && (
                      <a href={`tel:${clientInfo.telephone}`} className="lien-contact" title="Appeler">
                        📞
                      </a>
                    )}
                  </td>
                  <td>{Number(d.montant_total).toLocaleString("fr-FR")} MAD</td>
                  <td>
                    <span className={`badge badge-${d.statut}`}>{d.statut}</span>
                  </td>
                  <td>
                    {d.statut === "brouillon" && (
                      <>
                        <button onClick={() => marquerValide(d.id, true)} className="btn-valider">✓ Valider</button>
                        <button onClick={() => marquerValide(d.id, false)} className="btn-refuser">✕ Refuser</button>
                      </>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
