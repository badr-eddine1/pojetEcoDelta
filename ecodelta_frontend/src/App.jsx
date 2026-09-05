import { useState } from "react";
import AppelsOffres from "./components/AppelsOffres";
import Clients from "./components/Clients";
import Produits from "./components/Produits";
import MotsCles from "./components/MotsCles";
import Login from "./components/Login";
import "./App.css";

export default function App() {
  const [page, setPage] = useState("ao");
  const [connecte, setConnecte] = useState(!!localStorage.getItem("token"));

  function seDeconnecter() {
    localStorage.removeItem("token");
    setConnecte(false);
  }

  if (!connecte) {
    return <Login onConnecte={() => setConnecte(true)} />;
  }

  return (
    <div className="app">
      <nav className="navbar">
        <img src="https://ecodelta.ma/wp-content/uploads/2024/12/web-logo.png" alt="Ecodelta" className="logo-img" />
        <div className="nav-links">
          <button className={page === "ao" ? "active" : ""} onClick={() => setPage("ao")}>
            Appels d'offres
          </button>
          <button className={page === "clients" ? "active" : ""} onClick={() => setPage("clients")}>
            Clients & Devis
          </button>
          <button className={page === "produits" ? "active" : ""} onClick={() => setPage("produits")}>
            Produits
          </button>
          <button className={page === "mots-cles" ? "active" : ""} onClick={() => setPage("mots-cles")}>
            Mots-clés
          </button>
        </div>
        <button onClick={seDeconnecter} className="btn-deconnexion">
          Déconnexion
        </button>
      </nav>

      <main>
        {page === "ao" && <AppelsOffres />}
        {page === "clients" && <Clients />}
        {page === "produits" && <Produits />}
        {page === "mots-cles" && <MotsCles />}
      </main>
    </div>
  );
}
