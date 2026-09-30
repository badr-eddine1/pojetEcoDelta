# Checklist de test local — avant chaque déploiement

À parcourir avant tout `git push` suivi d'un déploiement sur le VPS. Prend 5-10 minutes une fois l'habitude prise.

---

## 1. Préparer l'environnement local

- [ ] Les 3 `venv` (ou `node_modules`) sont à jour : `pip install -r requirements.txt` / `npm install` si tu as ajouté une dépendance
- [ ] Ta base PostgreSQL locale a le **même schéma** que la prod — si tu as ajouté une migration récemment (`migration_*.sql`), vérifie qu'elle est bien appliquée en local aussi :
  ```bash
  psql -U postgres -d ecodelta_db -f nom_de_la_migration.sql
  ```
- [ ] Les 3 `.env` locaux sont renseignés (clé OpenAI, DB, JWT_SECRET_KEY, SMTP)

## 2. Lancer les 3 services en local

```bash
# Terminal 1
cd ecodelta_ai && venv\Scripts\activate && uvicorn main:app --reload

# Terminal 2
cd ecodelta_frontend && npm run dev

# Terminal 3
cd ecodelta_surveillance && venv\Scripts\activate && python surveillance.py
```

- [ ] Les 3 démarrent sans erreur dans leur terminal respectif
- [ ] `http://localhost:8000/docs` s'ouvre correctement (API accessible)
- [ ] Le frontend s'ouvre et la page de connexion s'affiche

## 3. Scénarios à tester à chaque fois (non-régression)

Même si ta modification ne touche qu'une seule fonctionnalité, teste toujours ces parcours de base — ce sont ceux dont dépend l'équipe commerciale au quotidien :

- [ ] Connexion avec un compte existant
- [ ] La liste des appels d'offres pertinents s'affiche
- [ ] La liste des produits s'affiche
- [ ] Créer un devis avec un produit **ayant** un prix en base
- [ ] Créer un devis avec un produit **sans** prix (`prix_unitaire = NULL`) → doit afficher un message clair, pas une erreur brute
- [ ] Valider un devis existant
- [ ] Le module de surveillance (Terminal 3) termine au moins un cycle complet sans erreur

## 4. Tester spécifiquement ce que tu viens de modifier

- [ ] Le nouveau comportement fonctionne dans le cas normal
- [ ] Il ne casse rien d'autre : relance rapidement `python test_smoke.py` (voir ci-dessous) pour vérifier que les endpoints principaux répondent toujours

## 5. Avant de pousser

- [ ] `git status` : pas de fichier `.env` ni de `venv/`/`node_modules/` inclus par erreur
- [ ] Message de commit clair sur ce qui a changé

## 6. Après déploiement sur le VPS

- [ ] `sudo systemctl status ecodelta-api` et `ecodelta-surveillance` → actifs (`active (running)`)
- [ ] Recharger le site en prod, refaire rapidement le test de connexion + une liste qui s'affiche
- [ ] Si une migration SQL était nécessaire : vérifie qu'elle a bien été appliquée sur la base de **production**, pas juste en local (facile à oublier)

---

## En cas de problème après déploiement

```bash
# Voir les logs en direct
sudo journalctl -u ecodelta-api -f
sudo journalctl -u ecodelta-surveillance -f
```

Si un déploiement casse quelque chose et que tu dois revenir en arrière rapidement :
```bash
git log --oneline -5      # repérer le dernier commit qui marchait
git checkout <hash>
sudo systemctl restart ecodelta-api ecodelta-surveillance
```