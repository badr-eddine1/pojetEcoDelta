import { useState } from "react";
import AppelsOffres from "./components/AppelsOffres";
import Clients from "./components/Clients";
import Produits from "./components/Produits";
import "./App.css";

export default function App() {
  const [page, setPage] = useState("ao");

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
        </div>
      </nav>

      <main>
        {page === "ao" && <AppelsOffres />}
        {page === "clients" && <Clients />}
        {page === "produits" && <Produits />}
      </main>
    </div>
  );
}
