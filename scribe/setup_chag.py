"""
setup_chag.py — Initialisation CHAG pour SCRIBE
Usage : python setup_chag.py

Prérequis :
  - config.xml = config_chag.xml (copié depuis votre dossier privé)
  - uf.xlsx = export FICOM CHAG (placé dans ce même dossier)

Ce script :
  1. Init les tables et sites depuis config.xml (via setup.py)
  2. Crée les 7 sites GPS CHAG avec leurs vraies coordonnées
  3. Importe les UF depuis uf.xlsx (export FICOM)
  4. Génère config.js avec directeurs, annuaire, IA, federation
"""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(__file__))

print("""
╔══════════════════════════════════════════════════════════════╗
║  SCRIBE — Initialisation CHAG                                ║
╚══════════════════════════════════════════════════════════════╝
""")

# Vérifier que config.xml est bien celui du CHAG
import xml.etree.ElementTree as ET
xml_path = os.path.join(os.path.dirname(__file__), "config.xml")
if not os.path.exists(xml_path):
    print("✗ config.xml introuvable.")
    print("  Copiez config_chag.xml vers config.xml avant de lancer ce script.")
    sys.exit(1)

root = ET.parse(xml_path).getroot()
sigle = (root.findtext("etablissement/sigle") or "").strip()
if sigle != "CHAG":
    print(f"✗ config.xml contient le sigle '{sigle}' au lieu de 'CHAG'.")
    print("  Copiez config_chag.xml vers config.xml avant de lancer ce script.")
    sys.exit(1)

print(f"[✓] config.xml = CHAG — OK\n")

# Étape 1 — setup.py (sites depuis config.xml + admin + config.js)
print("[1/2] Initialisation via setup.py...")
r = subprocess.run([sys.executable, "setup.py"], capture_output=False)
if r.returncode != 0:
    print("✗ setup.py a échoué.")
    sys.exit(1)

# Étape 2 — import_uf2.py (UF depuis uf.xlsx)
uf_path = os.path.join(os.path.dirname(__file__), "uf.xlsx")
if os.path.exists(uf_path):
    print("\n[2/2] Import des UF depuis uf.xlsx...")
    r = subprocess.run([sys.executable, "import_uf2.py", uf_path], capture_output=False)
    if r.returncode != 0:
        print("⚠ import_uf2.py a rencontré une erreur — vérifiez le format du fichier.")
    else:
        print("  ✓ UF importées depuis uf.xlsx")
else:
    print("\n[2/2] uf.xlsx absent — UF non importées.")
    print("  Placez votre export FICOM (uf.xlsx) dans ce dossier puis relancez.")
    print("  Vous pouvez aussi importer plus tard : python import_uf2.py uf.xlsx")

print("""
╔══════════════════════════════════════════════════════════════╗
║  Configuration CHAG terminée                                 ║
║                                                              ║
║  Lance maintenant :  python main.py                         ║
║  Puis connecte-toi : http://localhost:8000                  ║
╚══════════════════════════════════════════════════════════════╝
""")
