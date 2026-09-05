import { useEffect, useState } from "react";
import { getMotsCles, creerMotCle, basculerMotCle, supprimerMotCle } from "../api";

export default function MotsCles() {
  const [motsCles, setMotsCles] = useState([]);
  const [nouveauMot, setNouveauMot] = useState("");
  const [loading, setLoading] = useState(true);
  const [erreur, setErreur] = useState(null);

  function charger() {
    setLoading(true);
    getMotsCles()
      .then(setMotsCles)
      .catch((e) => setErreur(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    charger();
  }, []);

  function ajouter(e) {
    e.preventDefault();
    if (!nouveauMot.trim()) return;
    creerMotCle(nouveauMot.trim())
      .then(() => {
        setNouveauMot("");
        charger();
      })
      .catch((e) => setErreur(e.message));
  }

  function toggle(id) {
    basculerMotCle(id).then(charger).catch((e) => setErreur(e.message));
  }

  function supprimer(id) {
    supprimerMotCle(id).then(charger).catch((e) => setErreur(e.message));
  }

  return (
    <div className="page">
      <h1>Mots-clés de recherche</h1>
      <p className="compteur">
        Ces mots-clés sont utilisés lors de la collecte des appels d'offres, en complément
        du filtre par domaines d'activité : un appel d'offres n'est retenu que s'il correspond
        à un domaine <strong>ET</strong> contient au moins un mot-clé actif dans son objet.
      </p>

      {erreur && <p className="erreur">{erreur}</p>}

      <form onSubmit={ajouter} className="section" style={{ display: "flex", gap: 8 }}>
        <input
          type="text"
          value={nouveauMot}
          onChange={(e) => setNouveauMot(e.target.value)}
          placeholder="Ex : panneaux solaires, contrôle d'accès..."
          style={{ flex: 1 }}
        />
        <button type="submit" className="btn-principal">+ Ajouter</button>
      </form>

      {loading ? (
        <p>Chargement...</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Mot-clé</th>
              <th>Statut</th>
              <th>Ajouté le</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {motsCles.map((m) => (
              <tr key={m.id}>
                <td>{m.mot_cle}</td>
                <td>
                  <span className={`badge ${m.actif ? "badge-valide" : "badge-refuse"}`}>
                    {m.actif ? "Actif" : "Inactif"}
                  </span>
                </td>
                <td>{m.date_creation ? new Date(m.date_creation).toLocaleDateString("fr-FR") : "—"}</td>
                <td>
                  <button onClick={() => toggle(m.id)} className="btn-secondaire">
                    {m.actif ? "Désactiver" : "Activer"}
                  </button>
                  <button onClick={() => supprimer(m.id)} className="btn-supprimer" style={{ marginLeft: 6 }}>
                    ✕
                  </button>
                </td>
              </tr>
            ))}
            {motsCles.length === 0 && (
              <tr>
                <td colSpan={4} style={{ textAlign: "center", color: "#9ca3af" }}>
                  Aucun mot-clé — la recherche se fera uniquement par domaines d'activité.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
