import { useEffect, useState } from "react";
import { getStatsSurveillance } from "../api";

export default function Statistiques() {
  const [stats, setStats] = useState(null);
  const [erreur, setErreur] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    charger();
  }, []);

  function charger() {
    setLoading(true);
    getStatsSurveillance()
      .then((data) => {
        setStats(data);
        setErreur(null);
      })
      .catch((e) => setErreur(e.message))
      .finally(() => setLoading(false));
  }

  if (loading) return <p>Chargement...</p>;

  return (
    <div className="page">
      <h1>Statistiques de surveillance</h1>
      {erreur && <p className="erreur">{erreur}</p>}

      {stats && (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-valeur">{stats.nouveaux_dernieres_24h}</span>
              <span className="stat-label">Nouveaux AO (24h)</span>
            </div>
            <div className="stat-card">
              <span className="stat-valeur">{stats.pertinents}</span>
              <span className="stat-label">AO pertinents (score ≥ 7)</span>
            </div>
            <div className="stat-card">
              <span className="stat-valeur">{stats.notifies}</span>
              <span className="stat-label">AO notifiés</span>
            </div>
            <div className="stat-card">
              <span className="stat-valeur">{stats.total}</span>
              <span className="stat-label">Total AO collectés</span>
            </div>
          </div>

          <div className="section" style={{ marginTop: "2rem" }}>
            <h2>Détails</h2>
            <table>
              <thead>
                <tr>
                  <th>Indicateur</th>
                  <th>Valeur</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Nouveaux appels d'offres (dernières 24h)</td>
                  <td>{stats.nouveaux_dernieres_24h}</td>
                </tr>
                <tr>
                  <td>Appels d'offres pertinents (score ≥ 7)</td>
                  <td>{stats.pertinents}</td>
                </tr>
                <tr>
                  <td>Appels d'offres notifiés</td>
                  <td>{stats.notifies}</td>
                </tr>
                <tr>
                  <td>Total appels d'offres collectés</td>
                  <td>{stats.total}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}