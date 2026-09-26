# Ecodelta — Plateforme de veille intelligente des appels d'offres

Plateforme automatisant la veille des appels d'offres publics marocains, la gestion de la relation client et la génération de devis et de fiches techniques, avec surveillance continue, notification automatique par email et export PDF.

Développée dans le cadre d'un stage chez **Ecodelta** (Rabat, Maroc), entreprise spécialisée en énergie solaire, sécurité périmétrique et contrôle d'accès, gestion de parking, affichage dynamique et effaroucheurs anti-volatiles.

---

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Stack technique](#stack-technique)
- [Structure du projet](#structure-du-projet)
- [Installation](#installation)
- [Configuration (.env)](#configuration-env)
- [Créer un compte utilisateur](#créer-un-compte-utilisateur)
- [Lancement](#lancement)
- [Authentification](#authentification)
- [Endpoints de l'API](#endpoints-de-lapi)
- [Collecte du catalogue produits](#collecte-du-catalogue-produits)
- [Export PDF des devis](#export-pdf-des-devis)
- [Limites connues](#limites-connues)

---

## Fonctionnalités

- 🔐 **Authentification par JWT** : accès à l'application réservé aux comptes créés manuellement pour l'équipe Ecodelta, jeton valide 12h
- 🔍 **Collecte automatique** des appels d'offres depuis [marchespublics.gov.ma](https://www.marchespublics.gov.ma), filtrée par domaines d'activité pertinents pour Ecodelta
- 🤖 **Scoring par intelligence artificielle** (OpenAI gpt-4o-mini) évaluant la pertinence de chaque appel d'offres, avec justification
- 📦 **Catalogue produits réel**, récupéré directement depuis l'API publique WooCommerce du site [ecodelta.ma](https://ecodelta.ma) (nom, description, image, catégories), avec fiches techniques commerciales générées automatiquement par IA
- 👥 **Gestion des clients**
- 💰 **Génération de devis** — calcul déterministe des montants (jamais par l'IA), rédaction de l'introduction/conclusion par IA, validation humaine obligatoire avant tout envoi
- 📄 **Export PDF des devis**, mise en forme aux couleurs Ecodelta, mention claire du statut (brouillon / validé / refusé)
- ⏱️ **Surveillance automatique continue** (toutes les 10 minutes) : détection des nouveaux appels d'offres, scoring, notification — sans intervention manuelle
- ✉️ **Notification email récapitulative** dès qu'un nouvel appel d'offres pertinent est détecté
- 🖥️ **Interface web** (React) avec filtres Tous / Nouveaux / Pertinents / Non pertinents, tableau de bord de statistiques, et fenêtres de détail au clic (appels d'offres et produits)

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
                                    API REST (FastAPI) ──auth JWT──► Interface web (React)
                                              │
                                              ▼
                                   Export PDF des devis (ReportLab)
```

Trois sous-projets indépendants, communiquant via une base de données PostgreSQL commune :

| Dossier | Rôle |
|---|---|
| `ecodelta_ai/` | API REST (FastAPI) : authentification, appels d'offres, clients, produits, devis, export PDF |
| `ecodelta_frontend/` | Interface web (React + Vite) |
| `ecodelta_surveillance/` | Pipeline automatique : scraping filtré, scoring, notification, scheduler |

---

## Stack technique

| Catégorie | Technologies |
|---|---|
| Langages | Python, JavaScript (JSX), SQL |
| Backend / IA | FastAPI, Playwright, psycopg2, APScheduler, smtplib |
| Authentification | python-jose (JWT), bcrypt |
| Documents | ReportLab (export PDF des devis) |
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
│   ├── auth.py                     # Authentification JWT (hash, token, dépendance FastAPI)
│   ├── create_user.py              # Script CLI de création manuelle de compte
│   ├── scoring.py                  # Scoring des AO par IA
│   ├── fiches_techniques.py        # Génération de fiches produits
│   ├── scraper_produits.py         # Récupération du catalogue réel (API WooCommerce ecodelta.ma)
│   ├── devis.py                    # Génération de devis (calcul Python + rédaction IA)
│   ├── devis_pdf.py                # Export PDF d'un devis (ReportLab)
│   ├── main.py                     # API FastAPI
│   └── .env
│
├── ecodelta_frontend/               # Interface web
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       └── components/
│           ├── Login.jsx
│           ├── AppelsOffres.jsx
│           ├── Clients.jsx
│           └── Produits.jsx
│
└── ecodelta_surveillance/           # Pipeline automatique
    ├── db.py
    ├── domaines.py                 # Sélection auto des domaines d'activité (popup du portail)
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
pip install "python-jose[cryptography]" bcrypt
pip install reportlab
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
-- Schéma initial (tables appels_offres, clients, produits, devis, users)
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

JWT_SECRET_KEY=une_chaine_aleatoire_longue_et_secrete
```

> 🔑 Génère `JWT_SECRET_KEY` avec : `python -c "import secrets; print(secrets.token_hex(32))"`

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

## Créer un compte utilisateur

Il n'existe pas d'inscription publique : chaque membre de l'équipe Ecodelta doit se voir créer un compte manuellement.

```bash
cd ecodelta_ai
venv\Scripts\activate
python create_user.py
```

Le script demande un email, un nom complet et un mot de passe (au moins 8 caractères, saisie masquée), puis crée la ligne correspondante dans la table `users` (mot de passe stocké sous forme de hash bcrypt, jamais en clair).

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

## Authentification

Toutes les routes de l'API (hors `/login`) sont protégées par jeton JWT.

**Connexion :**
```
POST /login
Content-Type: application/x-www-form-urlencoded

username=email@ecodelta.ma&password=motdepasse
```
Renvoie `{ "access_token": "...", "token_type": "bearer" }` si les identifiants sont valides.

**Requêtes suivantes**, le frontend ajoute l'en-tête à chaque appel :
```
Authorization: Bearer <access_token>
```

Le jeton reste valide **12 heures**. Passé ce délai (ou en cas de jeton invalide), l'API répond `401 Unauthorized` et le frontend redirige vers l'écran de connexion.

---

## Endpoints de l'API

| Endpoint | Méthode | Auth | Description |
|---|---|---|---|
| `/login` | POST | — | Connexion, retourne un jeton JWT |
| `/appels-offres` | GET | ✓ | Liste complète, filtrable par `score_min` |
| `/appels-offres/nouveaux` | GET | ✓ | AO détectés dans les dernières 24h |
| `/appels-offres/pertinents` | GET | ✓ | AO au score ≥ seuil |
| `/appels-offres/non-pertinents` | GET | ✓ | AO scorés mais sous le seuil |
| `/appels-offres/{id}` | GET | ✓ | Détail complet d'un AO |
| `/produits` | GET | ✓ | Catalogue produits + fiches techniques |
| `/clients` | GET / POST | ✓ | Liste / création de clients |
| `/devis` | GET / POST | ✓ | Historique / génération de devis |
| `/devis/{id}/valider` | PATCH | ✓ | Validation humaine d'un devis |
| `/devis/{id}/pdf` | GET | ✓ | Export PDF du devis |
| `/surveillance/stats` | GET | ✓ | Statistiques agrégées (nouveaux, pertinents, notifiés) |

Documentation interactive disponible sur `http://localhost:8000/docs` une fois l'API lancée (le bouton *Authorize* permet d'y coller un jeton pour tester les routes protégées).

---

## Collecte du catalogue produits

Contrairement au module de veille des appels d'offres (qui doit scraper le HTML rendu du portail des marchés publics via Playwright, faute d'API), le catalogue produits d'Ecodelta est récupéré via une méthode plus simple et plus fiable :

**Le site ecodelta.ma utilise WooCommerce, qui expose une API JSON publique** (`/wp-json/wc/store/v1/products`), normalement prévue pour les fonctionnalités de panier/paiement du site. Cette API permet de récupérer tout le catalogue (nom, description, image, catégories) de façon structurée, sans avoir à parser du HTML — pas besoin de navigateur automatisé ici, une simple requête `requests` suffit.

```bash
cd ecodelta_ai
python scraper_produits.py
```

Points importants :
- **Aucun prix n'est affiché publiquement** sur le site (modèle « sur devis ») : le champ `prix_unitaire` reste donc `NULL` pour les produits scrapés, et l'interface affiche « Sur devis » à la place
- **Dédoublonnage par `source_id`** (l'identifiant unique WooCommerce), pas par nom : plusieurs produits du catalogue réel partagent des noms identiques ou très proches, un dédoublonnage par nom en perdrait donc à tort
- Une fois le catalogue importé, `fiches_techniques.py` peut être exécuté sur ces produits réels pour générer leurs fiches commerciales par IA, exactement comme pour les données de test utilisées initialement

---

## Export PDF des devis

`devis_pdf.py` génère le PDF d'un devis à partir des données déjà stockées en base (client, lignes produits, montant total, textes IA d'introduction/conclusion) — aucun nouvel appel à l'IA n'est effectué à l'export, uniquement de la mise en forme.

Le PDF reprend l'identité visuelle d'Ecodelta et affiche clairement le statut du devis :
- **Brouillon** → bandeau d'avertissement : à valider avant tout envoi au client
- **Validé** → mention verte : prêt à être transmis
- **Refusé** → mention explicite : ne pas transmettre

```bash
pip install reportlab
```

Appelé via l'API (`GET /devis/{id}/pdf`), qui renvoie directement le fichier généré.

---

## Limites connues

- **Pas de temps réel strict** : le portail des marchés publics ne propose aucune API/webhook ; la détection repose sur un polling périodique (délai maximal = intervalle configuré, 10 min par défaut)
- **Répertoire clients** encore en données de test, à remplacer par les vrais clients d'Ecodelta
- **Fiches techniques IA** pas encore régénérées sur l'ensemble du catalogue réel (99 produits) — à relancer via `fiches_techniques.py`
- **Pas de TVA** ni de conditions de paiement dans le calcul actuel des devis
- **Pas d'envoi automatique** du devis validé au client : le PDF est généré et téléchargeable, mais sa transmission reste une action manuelle de l'équipe commerciale en dehors de la plateforme
- **Filtrage par domaines** basé sur des codes identifiés manuellement dans le HTML du portail (`domaines.py`) — aucune catégorie « énergie solaire » ou « parking » explicite n'existe dans l'arborescence, ces activités sont couvertes par des catégories plus larges (électricité, hydraulique, automatisme), à ajuster si de nouveaux codes pertinents sont identifiés

---

## Auteur

**AITBEN IJJA Badr-Eddine** 