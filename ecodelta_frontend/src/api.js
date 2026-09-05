const API_URL = "http://localhost:8000";

// ---------- Wrapper central : ajoute le jeton et gère les sessions expirées ----------

async function requeteAuth(url, options = {}) {
  const token = localStorage.getItem("token");

  const headers = {
    ...(options.headers || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const res = await fetch(url, { ...options, headers });

  if (res.status === 401) {
    // Session expirée ou jeton invalide : on déconnecte proprement
    localStorage.removeItem("token");
    window.location.reload();
    throw new Error("Session expirée, merci de vous reconnecter");
  }

  return res;
}

// ---------- Appels d'offres ----------

export async function getAppelsOffres(scoreMin = null) {
  const url = scoreMin !== null
    ? `${API_URL}/appels-offres?score_min=${scoreMin}&limit=200`
    : `${API_URL}/appels-offres?limit=200`;
  const res = await requeteAuth(url);
  if (!res.ok) throw new Error("Erreur lors du chargement des appels d'offres");
  return res.json();
}

export async function getNouveauxAppelsOffres(heures = 24) {
  const res = await requeteAuth(`${API_URL}/appels-offres/nouveaux?heures=${heures}`);
  if (!res.ok) throw new Error("Erreur lors du chargement des nouveaux AO");
  return res.json();
}

export async function getAppelsOffresPertinents(seuil = 7) {
  const res = await requeteAuth(`${API_URL}/appels-offres/pertinents?seuil=${seuil}`);
  if (!res.ok) throw new Error("Erreur lors du chargement des AO pertinents");
  return res.json();
}

export async function getAppelsOffresNonPertinents(seuil = 7) {
  const res = await requeteAuth(`${API_URL}/appels-offres/non-pertinents?seuil=${seuil}`);
  if (!res.ok) throw new Error("Erreur lors du chargement des AO non pertinents");
  return res.json();
}

export async function getAppelOffreDetail(id) {
  const res = await requeteAuth(`${API_URL}/appels-offres/${id}`);
  if (!res.ok) throw new Error("Erreur lors du chargement du détail de l'AO");
  return res.json();
}

export async function getStatsSurveillance() {
  const res = await requeteAuth(`${API_URL}/surveillance/stats`);
  if (!res.ok) throw new Error("Erreur lors du chargement des statistiques");
  return res.json();
}

// ---------- Produits ----------

export async function getProduits() {
  const res = await requeteAuth(`${API_URL}/produits`);
  if (!res.ok) throw new Error("Erreur lors du chargement des produits");
  return res.json();
}

// ---------- Clients ----------

export async function getClients() {
  const res = await requeteAuth(`${API_URL}/clients`);
  if (!res.ok) throw new Error("Erreur lors du chargement des clients");
  return res.json();
}

export async function creerClient(nom, email, telephone) {
  const res = await requeteAuth(`${API_URL}/clients`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nom, email, telephone }),
  });
  if (!res.ok) throw new Error("Erreur lors de la création du client");
  return res.json();
}

// ---------- Devis ----------

export async function getDevis() {
  const res = await requeteAuth(`${API_URL}/devis`);
  if (!res.ok) throw new Error("Erreur lors du chargement des devis");
  return res.json();
}

export async function creerDevis(clientId, produits) {
  const res = await requeteAuth(`${API_URL}/devis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ client_id: clientId, produits }),
  });
  if (!res.ok) throw new Error("Erreur lors de la création du devis");
  return res.json();
}

export async function validerDevis(devisId, valide) {
  const res = await requeteAuth(`${API_URL}/devis/${devisId}/valider`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ valide }),
  });
  if (!res.ok) throw new Error("Erreur lors de la validation du devis");
  return res.json();
}

// ---------- Mots-clés ----------

export async function getMotsCles() {
  const res = await requeteAuth(`${API_URL}/mots-cles`);
  if (!res.ok) throw new Error("Erreur lors du chargement des mots-clés");
  return res.json();
}

export async function creerMotCle(motCle) {
  const res = await requeteAuth(`${API_URL}/mots-cles`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mot_cle: motCle }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Erreur lors de la création du mot-clé");
  }
  return res.json();
}

export async function basculerMotCle(id) {
  const res = await requeteAuth(`${API_URL}/mots-cles/${id}`, { method: "PATCH" });
  if (!res.ok) throw new Error("Erreur lors de la mise à jour du mot-clé");
  return res.json();
}

export async function supprimerMotCle(id) {
  const res = await requeteAuth(`${API_URL}/mots-cles/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Erreur lors de la suppression du mot-clé");
  return res.json();
}