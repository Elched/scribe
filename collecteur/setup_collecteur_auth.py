#!/usr/bin/env python3
"""
setup_collecteur_auth.py — Configure le login/mot de passe de l'interface web du collecteur.

Usage :
  python setup_collecteur_auth.py           → configure un login/mdp
  python setup_collecteur_auth.py --remove  → supprime la protection

Le fichier collecteur_ui_auth.json est créé dans le dossier courant.
Sans ce fichier, l'interface est accessible sans authentification.
"""
import sys, json, hashlib, getpass
from pathlib import Path

AUTH_FILE = Path("collecteur_ui_auth.json")

if "--remove" in sys.argv:
    if AUTH_FILE.exists():
        AUTH_FILE.unlink()
        print("✓ Protection supprimée — l'interface est maintenant accessible sans authentification.")
    else:
        print("~ Aucune protection configurée.")
    sys.exit(0)

print("\n  Configuration du login collecteur")
print("  ─────────────────────────────────\n")
login = input("  Identifiant : ").strip()
if not login:
    print("✗ Identifiant vide.")
    sys.exit(1)

password = getpass.getpass("  Mot de passe : ")
if len(password) < 6:
    print("✗ Mot de passe trop court (6 caractères minimum).")
    sys.exit(1)

confirm = getpass.getpass("  Confirmer le mot de passe : ")
if password != confirm:
    print("✗ Les mots de passe ne correspondent pas.")
    sys.exit(1)

h = hashlib.sha256(password.encode()).hexdigest()
AUTH_FILE.write_text(json.dumps({"login": login, "password_hash": h}, indent=2))

print(f"\n  ✓ Protection configurée.")
print(f"  Login    : {login}")
print(f"  Fichier  : {AUTH_FILE.resolve()}")
print(f"\n  Relancez le collecteur pour appliquer : python collecteur.py")
