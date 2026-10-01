-- Emplacement : ProjetEcodelta/init-db/01_schema.sql
-- Exécuté automatiquement par le conteneur PostgreSQL au tout premier démarrage
-- (uniquement si le volume pgdata est vide — ne se relance pas tout seul ensuite).
--
-- Vérifié colonne par colonne contre information_schema.columns de la base réelle le 2026-10-01.

-- ========== appels_offres ==========
CREATE TABLE appels_offres (
    id SERIAL PRIMARY KEY,
    titre VARCHAR(255) NOT NULL,
    description TEXT,
    montant NUMERIC,
    secteur VARCHAR(100),
    date_limite DATE,
    lien VARCHAR(500),
    source VARCHAR(100),
    score_ia NUMERIC,
    justification_ia TEXT,
    statut VARCHAR(50) DEFAULT 'nouveau',
    date_ajout TIMESTAMP DEFAULT NOW(),
    url_detail VARCHAR(500),
    date_detection TIMESTAMP DEFAULT NOW(),
    notification_envoyee BOOLEAN DEFAULT FALSE,
    date_notification TIMESTAMP
);

-- ========== clients ==========
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    telephone VARCHAR(50),
    statut VARCHAR(50) DEFAULT 'nouveau',
    date_creation TIMESTAMP DEFAULT NOW()
);

-- ========== produits ==========
CREATE TABLE produits (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    description TEXT,
    prix_unitaire NUMERIC,
    specs_techniques TEXT,
    source_id INTEGER,
    image_url TEXT,
    fiche_technique JSONB
);

-- ========== devis ==========
CREATE TABLE devis (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    produits JSONB,
    montant_total NUMERIC,
    statut VARCHAR(50) DEFAULT 'brouillon',
    date_creation TIMESTAMP DEFAULT NOW(),
    genere_par_ia BOOLEAN DEFAULT TRUE,
    valide_par_humain BOOLEAN DEFAULT FALSE,
    introduction_ia TEXT,
    conclusion_ia TEXT
);

-- ========== users ==========
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    mot_de_passe_hash VARCHAR(255) NOT NULL,
    nom VARCHAR(255),
    date_creation TIMESTAMP DEFAULT NOW()
);

-- ========== mots_cles_recherche ==========
CREATE TABLE mots_cles_recherche (
    id SERIAL PRIMARY KEY,
    mot_cle VARCHAR(255) NOT NULL UNIQUE,
    actif BOOLEAN DEFAULT TRUE,
    date_creation TIMESTAMP DEFAULT NOW()
);