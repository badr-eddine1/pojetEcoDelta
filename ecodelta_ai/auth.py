"""
Authentification par JWT (JSON Web Token).

Fonctionnement :
1. L'utilisateur se connecte via POST /login (email + mot de passe)
2. Si les identifiants sont corrects, un jeton (token) signé est renvoyé
3. Le frontend stocke ce jeton et le renvoie dans l'en-tête "Authorization: Bearer <token>"
   pour chaque requête suivante
4. Chaque route protégée vérifie ce jeton via get_current_user avant de répondre

Installation : pip install "python-jose[cryptography]" bcrypt

Note : on utilise directement la librairie bcrypt (pas passlib), qui pose des
problèmes de compatibilité avec les versions récentes de bcrypt (erreur
"module 'bcrypt' has no attribute '__about__'").

Variable d'environnement requise dans .env :
    JWT_SECRET_KEY=une_chaine_aleatoire_longue_et_secrete
    (génère-la par exemple avec : python -c "import secrets; print(secrets.token_hex(32))")
"""

import os
from datetime import datetime, timedelta, timezone

import bcrypt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY manquant dans le fichier .env")

ALGORITHM = "HS256"
DUREE_VALIDITE_MINUTES = 60 * 12  # le jeton reste valide 12 heures

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def hasher_mot_de_passe(mot_de_passe_clair: str) -> str:
    hash_bytes = bcrypt.hashpw(mot_de_passe_clair.encode("utf-8"), bcrypt.gensalt())
    return hash_bytes.decode("utf-8")


def verifier_mot_de_passe(mot_de_passe_clair: str, mot_de_passe_hash: str) -> bool:
    return bcrypt.checkpw(
        mot_de_passe_clair.encode("utf-8"),
        mot_de_passe_hash.encode("utf-8"),
    )


def creer_token(email: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(minutes=DUREE_VALIDITE_MINUTES)
    payload = {"sub": email, "exp": expiration}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Dépendance FastAPI à ajouter sur chaque route protégée."""
    erreur_auth = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides ou session expirée",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise erreur_auth
        return email
    except JWTError:
        raise erreur_auth