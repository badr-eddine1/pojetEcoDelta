import { useState } from "react";

const API_URL = "http://localhost:8000";

export default function Login({ onConnecte }) {
  const [email, setEmail] = useState("");
  const [motDePasse, setMotDePasse] = useState("");
  const [erreur, setErreur] = useState(null);
  const [chargement, setChargement] = useState(false);
  const [afficherMdp, setAfficherMdp] = useState(false);

  async function seConnecter(e) {
    e.preventDefault();
    setErreur(null);
    setChargement(true);

    try {
      const body = new URLSearchParams();
      body.append("username", email);
      body.append("password", motDePasse);

      const res = await fetch(`${API_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      });

      if (!res.ok) {
        throw new Error("Email ou mot de passe incorrect");
      }

      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      onConnecte();
    } catch (err) {
      setErreur(err.message);
    } finally {
      setChargement(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-fond-decoratif" />

      <form onSubmit={seConnecter} className="login-carte">
        <img
          src="https://ecodelta.ma/wp-content/uploads/2024/12/web-logo.png"
          alt="Ecodelta"
          className="login-logo"
        />

        <h1>Bienvenue</h1>
        <p className="login-soustitre">Plateforme de veille intelligente des appels d'offres</p>

        {erreur && (
          <p className="erreur login-erreur">
            ⚠️ {erreur}
          </p>
        )}

        <label htmlFor="login-email">Adresse email</label>
        <div className="login-champ">
          <span className="login-icone"></span>
          <input
            id="login-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="nom@ecodelta.ma"
            required
            autoFocus
          />
        </div>

        <label htmlFor="login-mdp">Mot de passe</label>
        <div className="login-champ">
          <span className="login-icone"></span>
          <input
            id="login-mdp"
            type={afficherMdp ? "text" : "password"}
            value={motDePasse}
            onChange={(e) => setMotDePasse(e.target.value)}
            placeholder="••••••••"
            required
          />
          <button
            type="button"
            className="login-toggle-mdp"
            onClick={() => setAfficherMdp(!afficherMdp)}
            tabIndex={-1}
          >
            {afficherMdp ? "🙈" : "👁️"}
          </button>
        </div>

        <button type="submit" className="btn-principal login-btn-submit" disabled={chargement}>
          {chargement ? "Connexion en cours..." : "Se connecter"}
        </button>

        <p className="login-footer">
          Accès réservé à l'équipe Ecodelta
        </p>
      </form>
    </div>
  );
}
