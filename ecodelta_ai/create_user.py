"""
Crée un compte utilisateur pour l'application (email + mot de passe).
Pas d'inscription publique : ce script est à lancer manuellement pour chaque
membre de l'équipe Ecodelta qui doit avoir accès à l'application.

Usage : python create_user.py
"""

import getpass
from db import get_connection
from auth import hasher_mot_de_passe

email = input("Email : ").strip().lower()
nom = input("Nom complet : ").strip()
mot_de_passe = getpass.getpass("Mot de passe (ne s'affiche pas à l'écran) : ")
confirmation = getpass.getpass("Confirme le mot de passe : ")

if mot_de_passe != confirmation:
    print("Les deux mots de passe ne correspondent pas. Abandon.")
    exit(1)

if len(mot_de_passe) < 8:
    print("Le mot de passe doit faire au moins 8 caractères. Abandon.")
    exit(1)

conn = get_connection()
cur = conn.cursor()
try:
    cur.execute(
        "INSERT INTO users (email, mot_de_passe_hash, nom) VALUES (%s, %s, %s);",
        (email, hasher_mot_de_passe(mot_de_passe), nom),
    )
    conn.commit()
    print(f"\nUtilisateur '{email}' créé avec succès.")
except Exception as e:
    conn.rollback()
    print(f"\nErreur : {e}")
    print("(cet email existe peut-être déjà)")
finally:
    cur.close()
    conn.close()