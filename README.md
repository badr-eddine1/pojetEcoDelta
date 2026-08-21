# Ecodelta — Plateforme de veille intelligente des appels d'offres

Plateforme automatisant la veille des appels d'offres publics marocains, la gestion de la relation client, la génération de devis et de fiches techniques, avec surveillance continue et notification automatique par email.

Développée dans le cadre d'un stage chez **Ecodelta** (Rabat, Maroc), entreprise spécialisée en énergie solaire, sécurité périmétrique et contrôle d'accès, gestion de parking, affichage dynamique et effaroucheurs anti-volatiles.

---

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Stack technique](#stack-technique)
- [Structure du projet](#structure-du-projet)
- [Installation](#installation)
- [Configuration (.env)](#configuration-env)
- [Lancement](#lancement)
- [Endpoints de l'API](#endpoints-de-lapi)
- [Limites connues](#limites-connues)

---

## Fonctionnalités

- 🔍 **Collecte automatique** des appels d'offres depuis [marchespublics.gov.ma](https://www.marchespublics.gov.ma), filtrée par domaines d'activité pertinents pour Ecodelta
- 🤖 **Scoring par intelligence artificielle** (OpenAI gpt-4o-mini) évaluant la pertinence de chaque appel d'offres, avec justification
- 👥 **Gestion des clients** et d'un catalogue produits avec fiches techniques générées automatiquement
- 💰 **Génération de devis** — calcul déterministe des montants (jamais par l'IA), validation humaine obligatoire avant tout envoi
- ⏱️ **Surveillance automatique continue** (toutes les 10 minutes) : détection des nouveaux appels d'offres, scoring, notification — sans intervention manuelle
- ✉️ **Notification email récapitulative** dès qu'un nouvel appel d'offres pertinent est détecté
- 🖥️ **Interface web** (React) avec filtres Tous / Nouveaux / Pertinents / Non pertinents et tableau de bord de statistiques

---

## Architecture

```
Portail des marchés publics
          │
          ▼
  Scraper (Playwright)  ──filtrage domaines──►  Base de données (PostgreSQL)
          │                                              │
          │                                              ▼
   Scheduler (APScheduler,                      Scoring IA (OpenAI)
   toutes les 10 min)                                     │
          │                                              ▼
          └──────────────────────────►     Notification email (SMTP)
                                                           │
                                                           ▼
                                              API REST (FastAPI)
                                                           │
                                                           ▼
                                              Interface web (React)
```

Trois sous-projets indépendants, communiquant via une base de données PostgreSQL commune :

| Dossier | Rôle |
|---|---|
| `ecodelta_ai/` | API REST (FastAPI) : appels d'offres, clients, produits, devis |
| `ecodelta_frontend/` | Interface web (React + Vite) |
| `ecodelta_surveillance/` | Pipeline automatique : scraping filtré, scoring, notification, scheduler |

---

## Stack technique

| Catégorie | Technologies |
|---|---|
| Langages | Python, JavaScript (JSX), SQL |
| Backend / IA | FastAPI, Playwright, psycopg2, APScheduler, smtplib |
| Frontend | React, Vite |
| Base de données | PostgreSQL |
| IA | API OpenAI (gpt-4o-mini) |
| Outils | Git, GitHub, VS Code, pgAdmin 4 |

---

## Structure du projet

```
ProjetEcodelta/
│
├── ecodelta_ai/                    # API REST + logique métier
│   ├── db.py                       # Connexion PostgreSQL
│   ├── scoring.py                  # Scoring des AO par IA
│   ├── fiches_techniques.py        # Génération de fiches produits
│   ├── devis.py                    # Génération de devis
│   ├── main.py                     # API FastAPI
│   └── .env
│
├── ecodelta_frontend/               # Interface web
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       └── components/
│           ├── AppelsOffres.jsx
│           ├── Clients.jsx
│           └── Produits.jsx
│
└── ecodelta_surveillance/           # Pipeline automatique
    ├── db.py
    ├── domaines.py                 # Sélection auto des domaines d'activité
    ├── scraper_ao.py                # Scraper avec filtrage intégré
    ├── scoring.py
    ├── notifications.py             # Envoi d'emails récapitulatifs
    ├── surveillance.py              # Scheduler (boucle automatique)
    ├── migration_surveillance.sql
    └── .env
```

---

## Installation

Chaque dossier possède son propre environnement virtuel.

### `ecodelta_ai/`
```bash
cd ecodelta_ai
python -m venv venv
venv\Scripts\activate        # Windows
pip install fastapi uvicorn psycopg2-binary python-dotenv openai
```

### `ecodelta_frontend/`
```bash
cd ecodelta_frontend
npm install
```

### `ecodelta_surveillance/`
```bash
cd ecodelta_surveillance
python -m venv venv
venv\Scripts\activate
pip install playwright psycopg2-binary python-dotenv openai apscheduler
playwright install
```

### Base de données
Exécuter dans pgAdmin (ou `psql`) :
```sql
-- Schéma initial (tables appels_offres, clients, produits, devis)
-- puis :
\i ecodelta_surveillance/migration_surveillance.sql
```

---

## Configuration (.env)

### `ecodelta_ai/.env`
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ecodelta_db
DB_USER=postgres
DB_PASSWORD=ton_mot_de_passe

OPENAI_API_KEY=ta_cle_openai
```

### `ecodelta_surveillance/.env`
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ecodelta_db
DB_USER=postgres
DB_PASSWORD=ton_mot_de_passe

OPENAI_API_KEY=ta_cle_openai

SCRAP_INTERVAL_MINUTES=10
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=ton_email@gmail.com
SMTP_PASSWORD=mot_de_passe_application
NOTIFICATION_EMAIL_TO=contact@ecodelta.ma
SEUIL_NOTIFICATION=7
```

> ⚠️ Pour Gmail, `SMTP_PASSWORD` doit être un **mot de passe d'application** (généré via [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)), pas le mot de passe du compte.

---

## Lancement

Trois processus séparés, dans trois terminaux :

```bash
# Terminal 1 — API REST
cd ecodelta_ai
venv\Scripts\activate
uvicorn main:app --reload

# Terminal 2 — Interface web
cd ecodelta_frontend
npm run dev

# Terminal 3 — Surveillance automatique (le cœur du système)
cd ecodelta_surveillance
venv\Scripts\activate
python surveillance.py
```

Le Terminal 3 tourne en continu : il lance un premier cycle immédiatement puis se relance automatiquement toutes les `SCRAP_INTERVAL_MINUTES` (Ctrl+C pour arrêter).

---

## Endpoints de l'API

| Endpoint | Méthode | Description |
|---|---|---|
| `/appels-offres` | GET | Liste complète, filtrable par `score_min` |
| `/appels-offres/nouveaux` | GET | AO détectés dans les dernières 24h |
| `/appels-offres/pertinents` | GET | AO au score ≥ seuil |
| `/appels-offres/non-pertinents` | GET | AO scorés mais sous le seuil |
| `/appels-offres/{id}` | GET | Détail complet d'un AO |
| `/produits` | GET | Catalogue produits + fiches techniques |
| `/clients` | GET / POST | Liste / création de clients |
| `/devis` | GET / POST | Historique / génération de devis |
| `/devis/{id}/valider` | PATCH | Validation humaine d'un devis |
| `/surveillance/stats` | GET | Statistiques agrégées (nouveaux, pertinents, notifiés) |

Documentation interactive disponible sur `http://localhost:8000/docs` une fois l'API lancée.

---

## Limites connues

- **Pas de temps réel strict** : le portail des marchés publics ne propose aucune API/webhook ; la détection repose sur un polling périodique (délai maximal = intervalle configuré, 10 min par défaut)
- **Données de test** : catalogue produits et répertoire clients à remplacer par les données réelles d'Ecodelta
- **Pas de TVA** ni de conditions de paiement dans le calcul actuel des devis
- **Pas d'export PDF** des devis/fiches techniques pour le moment

---

## Auteur

**AITBEN IJJA Badr-Eddine** — Stagiaire, EMSI Marrakech, Ingénierie Informatique et Data Science
