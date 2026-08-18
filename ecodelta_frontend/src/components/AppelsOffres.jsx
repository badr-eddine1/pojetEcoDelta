import { useEffect, useState } from "react";
import {
  getAppelsOffres,
  getNouveauxAppelsOffres,
  getAppelsOffresPertinents,
  getAppelsOffresNonPertinents,
  getAppelOffreDetail,
  getStatsSurveillance,
} from "../api";

const FILTRES = [
  { cle: "tous", label: "Tous" },
  { cle: "nouveaux", label: "Nouveaux (24h)" },
  { cle: "pertinents", label: "Pertinents" },
  { cle: "non_pertinents", label: "Non pertinents" },
];

export default function AppelsOffres() {
  const [ao, setAo] = useState([]);
  const [filtre, setFiltre] = useState("pertinents");
  const [loading, setLoading] = useState(true);
  const [erreur, setErreur] = useState(null);
  const [stats, setStats] = useState(null);

  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    charger();
    getStatsSurveillance().then(setStats).catch(() => {});
  }, [filtre]);

  function charger() {
    setLoading(true);
    setErreur(null);
    let promesse;
    if (filtre === "tous") promesse = getAppelsOffres();
    else if (filtre === "nouveaux") promesse = getNouveauxAppelsOffres(24);
    else if (filtre === "pertinents") promesse = getAppelsOffresPertinents(7);
    else promesse = getAppelsOffresNonPertinents(7);

    promesse.then(setAo).catch((e) => setErreur(e.message)).finally(() => setLoading(false));
  }

  function ouvrirDetail(id) {
    setDetailLoading(true);
    setDetail({});
    getAppelOffreDetail(id).then(setDetail).catch((e) => setErreur(e.message)).finally(() => setDetailLoading(false));
  }

  function fermerDetail() {
    setDetail(null);
  }

  function couleurScore(score) {
    if (score === null || score === undefined) return "#9CA3AF";
    if (score >= 8) return "#16a34a";
    if (score >= 5) return "#ca8a04";
    return "#6b7280";
  }

  return (
    <div className="page">
      <h1>Appels d'offres</h1>

      {stats && (
        <div className="stats-bar">
          <div><strong>{stats.nouveaux_dernieres_24h}</strong> nouveaux (24h)</div>
          <div><strong>{stats.pertinents}</strong> pertinents</div>
          <div><strong>{stats.notifies}</strong> notifiés</div>
          <div><strong>{stats.total}</strong> au total</div>
        </div>
      )}

      <div className="filtre-tabs">
        {FILTRES.map((f) => (
          <button
            key={f.cle}
            className={filtre === f.cle ? "active" : ""}
            onClick={() => setFiltre(f.cle)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {loading && <p>Chargement...</p>}
      {erreur && <p className="erreur">Erreur : {erreur}</p>}

      {!loading && !erreur && (
        <>
          <p className="compteur">{ao.length} appel(s) d'offres — clique sur une carte pour voir le détail</p>
          <div className="liste-cartes">
            {ao.map((item) => (
              <div key={item.id} className="carte carte-cliquable" onClick={() => ouvrirDetail(item.id)}>
                <div className="carte-header">
                  <span className="score" style={{ background: couleurScore(item.score_ia) }}>
                    {item.score_ia !== null ? `${item.score_ia}/10` : "non scoré"}
                  </span>
                  {item.notification_envoyee && <span className="badge-notifie">✉️ notifié</span>}
                </div>
                <h3>{item.titre}</h3>
                <p className="secteur">📍 {item.secteur || "Lieu non précisé"}</p>
                <p className="justification">{item.justification_ia}</p>
                {item.lien && <p className="reference">Réf : {item.lien}</p>}
              </div>
            ))}
          </div>
        </>
      )}

      {detail && (
        <div className="modal-overlay" onClick={fermerDetail}>
          <div className="modal-contenu" onClick={(e) => e.stopPropagation()}>
            <button className="modal-fermer" onClick={fermerDetail}>✕</button>
            {detailLoading || !detail.titre ? (
              <p>Chargement du détail...</p>
            ) : (
              <>
                <span className="score" style={{ background: couleurScore(detail.score_ia) }}>
                  {detail.score_ia !== null ? `${detail.score_ia}/10` : "non scoré"}
                </span>
                <h2>{detail.titre}</h2>
                <p className="secteur">📍 {detail.secteur || "Lieu non précisé"}</p>
                <p><strong>Date limite :</strong> {detail.date_limite ? new Date(detail.date_limite).toLocaleDateString("fr-FR") : "N/A"}</p>
                <p><strong>Détecté le :</strong> {detail.date_detection ? new Date(detail.date_detection).toLocaleString("fr-FR") : "N/A"}</p>
                <p><strong>Statut :</strong> {detail.statut}</p>
                <p><strong>Notification :</strong> {detail.notification_envoyee ? "✉️ envoyée" : "non envoyée"}</p>
                <hr />
                <p><strong>Description complète :</strong></p>
                <p>{detail.description || "Aucune description disponible."}</p>
                <hr />
                <p><strong>Analyse IA :</strong></p>
                <p>{detail.justification_ia}</p>
                {detail.lien && <p className="reference">Référence : {detail.lien}</p>}
                <a href="https://www.marchespublics.gov.ma" target="_blank" rel="noopener noreferrer" className="btn-lien-officiel">
                  🔗 Voir sur le site officiel (marchespublics.gov.ma)
                </a>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
