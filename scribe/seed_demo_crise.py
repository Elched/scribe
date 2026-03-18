"""
seed_demo_crise.py — Scénario de crise complet sur 2 jours
Centre Hospitalier de Valmont (CHV)

Scénario : Cyberattaque par ransomware initiée dans la nuit du J1,
se propageant aux systèmes cliniques, entraînant des impacts sanitaires
sur plusieurs services. Activation cellule de crise, gestion de crise
sur 48h, retour progressif à la normale.

Usage :
  1. python setup_demo1.py      (crée la base avec sites + UF)
  2. python seed_demo_crise.py  (injecte le scénario de crise)
  3. python main.py
  4. Se connecter, exporter la main courante (EXPORT MAIN COURANTE)
  5. Aller dans l'onglet ANALYSE, charger le ZIP → démonstration complète

Identifiants : dircrise / Scribe2026!
"""

import sys, os, json, hashlib
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, engine, Base
import app.models
import app.api.status_page
from app.models import (
    SitrepEntry, Decision, Presence, Consigne,
    Task, RexEntry, User, Hospital, UniteFonctionnelle, ServiceStatus
)
from app.api.status_page import StatusPage, StatusPageChronologie

print("\n" + "═"*62)
print("  🎭  SCRIBE — Injection scénario de crise (2 jours)")
print("═"*62)

# ── Vérification base existante ────────────────────────────────
db = SessionLocal()
sites = db.query(Hospital).all()
if not sites:
    print("\n  ✗ Base vide — lancez d'abord : python setup_demo1.py")
    sys.exit(1)

# Récupérer les IDs de sites
site_map = {s.nom: s.id for s in sites}
main_id  = next((v for k,v in site_map.items() if "Principal" in k or "Valmont" in k), 1)
sec_id   = next((v for k,v in site_map.items() if "Crestval" in k or "Secondaire" in k), 2)
psy_id   = next((v for k,v in site_map.items() if "Pins" in k or "Psy" in k), 3)
ehpad_id = next((v for k,v in site_map.items() if "EHPAD" in k or "Lac" in k), 4)
samu_id  = next((v for k,v in site_map.items() if "SAMU" in k or "Centre 15" in k), 5)

site_noms = {v:k for k,v in site_map.items()}
print(f"\n  Sites trouvés : {list(site_map.keys())}")

# ── Nettoyage données opérationnelles (conserver sites/UF/users) ──
print("\n  Nettoyage des données existantes...")
for model in [StatusPageChronologie, StatusPage, RexEntry, Task, Consigne,
              Presence, Decision, SitrepEntry]:
    db.query(model).delete()
db.commit()
print("  ✓ Tables opérationnelles vidées")

# ── Temporalité ────────────────────────────────────────────────
# J1 = hier à 02h00, crise sur 48h
NOW   = datetime.now(timezone.utc)
J1_00 = NOW.replace(hour=2, minute=0, second=0, microsecond=0) - timedelta(days=1)

def t(h, m=0, day=0):
    """Retourne un datetime : day=0 → J1, day=1 → J2"""
    return J1_00 + timedelta(hours=h + day*24, minutes=m)

def ts(h, m=0, day=0):
    return t(h, m, day)

print(f"\n  Début de crise simulé : {J1_00.strftime('%d/%m/%Y %H:%M')} UTC")
print(f"  Fin de crise simulée  : {(J1_00+timedelta(hours=46)).strftime('%d/%m/%Y %H:%M')} UTC")

# ══════════════════════════════════════════════════════════════
#  INCIDENTS (15 alertes sur les 5 sites, UF variées)
# ══════════════════════════════════════════════════════════════
print("\n  [1/7] Création des incidents...")

JALONS_PREDEFINIS = [
    "Passé d'ordi","DSI contacté","RSSI alerté","Cellule activée",
    "CERT Santé","Isolation réseau","Sauvegarde OK","Retour normal"
]

def make_jalons(done_list, timestamps):
    jalons = []
    for i, label in enumerate(JALONS_PREDEFINIS):
        done = label in done_list
        jalons.append({
            "label": label,
            "done": done,
            "done_at": timestamps.get(label, "").isoformat() if done and label in timestamps else None,
            "done_by": "Équipe DSI" if done else None
        })
    return json.dumps(jalons)

incidents_data = [
    # ── J1 Nuit : premiers signaux ──────────────────────────────
    {
        "timestamp": ts(2, 14),
        "declarant_nom": "Cadre de nuit FME",
        "directeur_crise": "DSI",
        "site_id": "Site Principal — Valmont",
        "unite_fonctionnelle": "FME",
        "type_crise": "CYBER",
        "urgency": 2,
        "fait": "Impossible d'accéder au DPI Axigate depuis les postes du service FME",
        "analyse": "Peut-être une panne serveur ou mise à jour non planifiée. 3 postes concernés.",
        "moyens_engages": "Appel astreinte DSI",
        "intervenant_nom": "Astreinte DSI",
        "intervenant_contact": "6501",
        "status": "RÉSOLU",
        "resolved_at": ts(4, 30),
        "jalons": make_jalons(
            ["Passé d'ordi","DSI contacté","Retour normal"],
            {"DSI contacté": ts(2,20), "Retour normal": ts(4,30)}
        ),
    },
    {
        "timestamp": ts(2, 47),
        "declarant_nom": "Cadre de nuit Chirurgie",
        "directeur_crise": "DSI",
        "site_id": "Site Principal — Valmont",
        "unite_fonctionnelle": "CHIRURGIE ANESTHESIE",
        "type_crise": "CYBER",
        "urgency": 2,
        "fait": "Les postes du bloc opératoire affichent un message d'erreur inhabituel au démarrage. Système lent.",
        "analyse": "Comportement anormal généralisé. Possible infection malware.",
        "moyens_engages": "DSI alerté, vérification en cours",
        "intervenant_nom": "Technicien DSI",
        "intervenant_contact": "6502",
        "status": "RÉSOLU",
        "resolved_at": ts(18, 0),
        "jalons": make_jalons(
            ["Passé d'ordi","DSI contacté","RSSI alerté","Isolation réseau","Retour normal"],
            {"DSI contacté": ts(3,0), "RSSI alerté": ts(3,15), "Isolation réseau": ts(5,0), "Retour normal": ts(18,0)}
        ),
    },
    # ── J1 Matin : escalade ──────────────────────────────────────
    {
        "timestamp": ts(3, 52),
        "declarant_nom": "RSSI",
        "directeur_crise": "DSI",
        "site_id": "Site Principal — Valmont",
        "unite_fonctionnelle": "DSI — Informatique",
        "type_crise": "CYBER",
        "urgency": 4,
        "fait": "Ransomware confirmé sur l'Active Directory. Chiffrement en cours sur les serveurs de fichiers. Attaque de type LockBit identifiée.",
        "analyse": "Compromission de l'AD. Propagation rapide. Tous les services connectés au réseau principal sont potentiellement touchés. Impact sur l'ensemble du CHV.",
        "moyens_engages": "Isolation réseau engagée. CERT Santé contacté. Cellule de crise activée.",
        "intervenant_nom": "CERT Santé",
        "intervenant_contact": "cyberveille@sante.gouv.fr",
        "status": "EN COURS",
        "jalons": make_jalons(
            ["Passé d'ordi","DSI contacté","RSSI alerté","Cellule activée","CERT Santé","Isolation réseau"],
            {"RSSI alerté": ts(3,52), "Cellule activée": ts(5,30), "CERT Santé": ts(6,0), "Isolation réseau": ts(5,0)}
        ),
    },
    {
        "timestamp": ts(5, 10),
        "declarant_nom": "Directeur des Soins",
        "directeur_crise": "DG",
        "site_id": "Site Principal — Valmont",
        "unite_fonctionnelle": "URGENCES",
        "type_crise": "MIXTE",
        "urgency": 3,
        "fait": "Le logiciel de régulation des urgences est inaccessible. Prise en charge patients en mode papier.",
        "analyse": "Impact direct sur la gestion des flux patients. Risque de délai de prise en charge.",
        "moyens_engages": "Procédure mode dégradé urgences activée. Fiches papier distribuées.",
        "intervenant_nom": "Cadre supérieur urgences",
        "intervenant_contact": "5001",
        "status": "RÉSOLU",
        "resolved_at": ts(14, 0),
        "jalons": make_jalons(
            ["Passé d'ordi","DSI contacté","Retour normal"],
            {"DSI contacté": ts(5,15), "Retour normal": ts(14,0)}
        ),
    },
    {
        "timestamp": ts(5, 35),
        "declarant_nom": "Cadre bloc opératoire",
        "directeur_crise": "DSI",
        "site_id": "Site Principal — Valmont",
        "unite_fonctionnelle": "CHIRURGIE ANESTHESIE",
        "type_crise": "MIXTE",
        "urgency": 4,
        "fait": "Les postes de pilotage des respirateurs connectés au réseau sont inaccessibles. Passage en mode manuel sur 8 respirateurs en réanimation.",
        "analyse": "Risque patient direct. Équipes soignantes mobilisées en surveillance manuelle renforcée.",
        "moyens_engages": "Surveillance manuelle renforcée. Médecin senior rappelé.",
        "intervenant_nom": "Dr. MARTIN — Anesthésiste référent",
        "intervenant_contact": "5120",
        "status": "RÉSOLU",
        "resolved_at": ts(10, 0),
        "jalons": make_jalons(
            ["Passé d'ordi","DSI contacté","Retour normal"],
            {"DSI contacté": ts(5,40), "Retour normal": ts(10,0)}
        ),
    },
    {
        "timestamp": ts(6, 20),
        "declarant_nom": "Responsable téléphonie CHV",
        "directeur_crise": "DSI",
        "site_id": "Site Principal — Valmont",
        "unite_fonctionnelle": "Services Techniques",
        "type_crise": "CYBER",
        "urgency": 3,
        "fait": "La centrale téléphonique IPBX est hors service. Seuls les téléphones fixes analogiques fonctionnent.",
        "analyse": "Communication interne sévèrement perturbée. Numéros courts inaccessibles.",
        "moyens_engages": "Activation téléphonie de secours. Distribution liste numéros fixes.",
        "intervenant_nom": "Prestataire téléphonie",
        "intervenant_contact": "0800 000 001",
        "status": "RÉSOLU",
        "resolved_at": ts(20, 0, 1),
        "jalons": make_jalons(
            ["Passé d'ordi","DSI contacté","Retour normal"],
            {"DSI contacté": ts(6,30), "Retour normal": ts(20,0,1)}
        ),
    },
    # ── J1 Matin : sites secondaires touchés ─────────────────────
    {
        "timestamp": ts(7, 5),
        "declarant_nom": "Cadre responsable site Crestval",
        "directeur_crise": "DSI",
        "site_id": "Site Secondaire — Crestval",
        "unite_fonctionnelle": "DSI secondaire",
        "type_crise": "CYBER",
        "urgency": 3,
        "fait": "Site Crestval : tous les postes windows affichent une note de rançon. Réseau isolé en urgence par l'équipe locale.",
        "analyse": "Propagation via VPN inter-sites. Même souche que le site principal.",
        "moyens_engages": "VPN coupé. Réseau local isolé. Fonctionnement en mode île.",
        "intervenant_nom": "Technicien local Crestval",
        "intervenant_contact": "6601",
        "status": "EN COURS",
        "jalons": make_jalons(
            ["Isolation réseau","RSSI alerté","CERT Santé"],
            {"Isolation réseau": ts(7,10), "RSSI alerté": ts(7,15), "CERT Santé": ts(8,0)}
        ),
    },
    {
        "timestamp": ts(8, 30),
        "declarant_nom": "Directeur EHPAD",
        "directeur_crise": "DGA",
        "site_id": "EHPAD — Résidence du Lac",
        "unite_fonctionnelle": "EHPAD — Unité A",
        "type_crise": "MIXTE",
        "urgency": 2,
        "fait": "Le logiciel de gestion médicamenteuse est inaccessible. Distribution médicaments en cours avec fiches papier de sauvegarde.",
        "analyse": "Risque d'erreur médicamenteuse limité par les procédures papier. Situation maîtrisée mais contraignante.",
        "moyens_engages": "Procédure mode dégradé médicaments activée. Médecin coordinateur prévenu.",
        "intervenant_nom": "Médecin coordinateur EHPAD",
        "intervenant_contact": "6702",
        "status": "RÉSOLU",
        "resolved_at": ts(22, 0),
        "jalons": make_jalons(
            ["Passé d'ordi","Retour normal"],
            {"Retour normal": ts(22,0)}
        ),
    },
    {
        "timestamp": ts(9, 15),
        "declarant_nom": "RSSI",
        "directeur_crise": "DSI",
        "site_id": "Site Principal — Valmont",
        "unite_fonctionnelle": "DSI — Informatique",
        "type_crise": "CYBER",
        "urgency": 4,
        "fait": "Identification complète de l'attaque : ransomware LockBit 3.0. Demande de rançon de 500 000€. Refus catégorique conforme à la politique ANSSI.",
        "analyse": "Attaque sophistiquée. Vecteur d'entrée : phishing ciblé reçu 4 jours avant. Données potentiellement exfiltrées avant chiffrement.",
        "moyens_engages": "ANSSI contacté. Prestataire cybersécurité mandaté. Investigations forensiques lancées.",
        "intervenant_nom": "Prestataire CERT privé",
        "intervenant_contact": "soc@prestataire.fr",
        "status": "EN COURS",
        "jalons": make_jalons(
            ["RSSI alerté","CERT Santé","Isolation réseau"],
            {"RSSI alerté": ts(3,52), "CERT Santé": ts(6,0), "Isolation réseau": ts(5,0)}
        ),
    },
    # ── J1 Après-midi ────────────────────────────────────────────
    {
        "timestamp": ts(11, 45),
        "declarant_nom": "Cadre service imagerie",
        "directeur_crise": "DSI",
        "site_id": "Site Principal — Valmont",
        "unite_fonctionnelle": "MEDICO-TECHNIQUE ET REEDUCATION",
        "type_crise": "CYBER",
        "urgency": 3,
        "fait": "PACS et RIS (imagerie) hors service. Impossibilité de consulter les images radiologiques numériques.",
        "analyse": "Blocage des prescriptions d'imagerie urgente. Les examens en cours sont réalisés mais non lisibles.",
        "moyens_engages": "Contact fournisseur PACS. Solution de contournement en cours d'évaluation.",
        "intervenant_nom": "Support PACS",
        "intervenant_contact": "0800 000 002",
        "status": "RÉSOLU",
        "resolved_at": ts(8, 0, 1),
        "jalons": make_jalons(
            ["DSI contacté","Sauvegarde OK","Retour normal"],
            {"DSI contacté": ts(12,0), "Sauvegarde OK": ts(20,0), "Retour normal": ts(8,0,1)}
        ),
    },
    {
        "timestamp": ts(13, 0),
        "declarant_nom": "Directrice des soins",
        "directeur_crise": "DG",
        "site_id": "Unité Psychiatrique — Les Pins",
        "unite_fonctionnelle": "Psychiatrie de liaison",
        "type_crise": "SANITAIRE",
        "urgency": 2,
        "fait": "Rupture de communication entre l'unité de psychiatrie Les Pins et le site principal. Prise en charge des patients en autonomie.",
        "analyse": "Pas de risque immédiat. Protocoles de crise internes activés. Liaison assurée par téléphone fixe.",
        "moyens_engages": "Liaison téléphonique fixe établie. Cadre de garde renforcé.",
        "intervenant_nom": "Cadre de garde Les Pins",
        "intervenant_contact": "04 50 00 03 01",
        "status": "RÉSOLU",
        "resolved_at": ts(19, 0),
        "jalons": make_jalons(
            ["Passé d'ordi","Retour normal"],
            {"Retour normal": ts(19,0)}
        ),
    },
    # ── J2 Matin : restauration progressive ─────────────────────
    {
        "timestamp": ts(6, 0, 1),
        "declarant_nom": "DSI",
        "directeur_crise": "DSI",
        "site_id": "Site Principal — Valmont",
        "unite_fonctionnelle": "DSI — Informatique",
        "type_crise": "CYBER",
        "urgency": 2,
        "fait": "Restauration des serveurs de fichiers depuis les sauvegardes hors-ligne (J-3). Vérification d'intégrité en cours.",
        "analyse": "Sauvegardes saines. Perte de données limitée à 3 jours. Retour progressif prévu sur 8h.",
        "moyens_engages": "Équipe DSI au complet. Prestataire présent sur site.",
        "intervenant_nom": "Prestataire + équipe DSI",
        "intervenant_contact": "Salle informatique",
        "status": "RÉSOLU",
        "resolved_at": ts(16, 0, 1),
        "jalons": make_jalons(
            ["Sauvegarde OK","Retour normal"],
            {"Sauvegarde OK": ts(10,0,1), "Retour normal": ts(16,0,1)}
        ),
    },
    {
        "timestamp": ts(9, 30, 1),
        "declarant_nom": "Responsable pharmacie",
        "directeur_crise": "DGA",
        "site_id": "Site Principal — Valmont",
        "unite_fonctionnelle": "Pharmacie",
        "type_crise": "CYBER",
        "urgency": 2,
        "fait": "Le logiciel de prescription informatisée reste indisponible. Délai de retour estimé à 24h supplémentaires.",
        "analyse": "Mode dégradé papier maintenu. Procédure rodée depuis J1. Pas de rupture de soins.",
        "moyens_engages": "Mode dégradé pharmacie maintenu. Traçabilité papier.",
        "intervenant_nom": "Pharmacien chef",
        "intervenant_contact": "5300",
        "status": "RÉSOLU",
        "resolved_at": ts(22, 0, 1),
        "jalons": make_jalons(
            ["Retour normal"],
            {"Retour normal": ts(22,0,1)}
        ),
    },
    {
        "timestamp": ts(14, 0, 1),
        "declarant_nom": "DSI",
        "directeur_crise": "DSI",
        "site_id": "Site Principal — Valmont",
        "unite_fonctionnelle": "DSI — Informatique",
        "type_crise": "CYBER",
        "urgency": 1,
        "fait": "DPI Axigate restauré sur le site principal. Authentification testée et validée sur 20 postes pilotes.",
        "analyse": "Retour progressif. Montée en charge sur 4h. Surveillance renforcée.",
        "moyens_engages": "Équipe DSI en surveillance. Hotline interne activée.",
        "intervenant_nom": "DSI + support Axigate",
        "intervenant_contact": "6500",
        "status": "RÉSOLU",
        "resolved_at": ts(22, 0, 1),
        "jalons": make_jalons(
            ["Sauvegarde OK","Retour normal"],
            {"Sauvegarde OK": ts(14,30,1), "Retour normal": ts(22,0,1)}
        ),
    },
    {
        "timestamp": ts(20, 0, 1),
        "declarant_nom": "DG",
        "directeur_crise": "DG",
        "site_id": "Site Principal — Valmont",
        "unite_fonctionnelle": "Direction Générale",
        "type_crise": "CYBER",
        "urgency": 1,
        "fait": "Retour à la normale progressif constaté sur l'ensemble des sites. Maintien de la vigilance 72h.",
        "analyse": "Crise principale maîtrisée. Investigation forensique en cours. Plan de renforcement sécurité à élaborer.",
        "moyens_engages": "Surveillance maintenue. Rapport incident à transmettre à l'ARS.",
        "intervenant_nom": "Cellule de crise CHV",
        "intervenant_contact": "Salle de crise",
        "status": "RÉSOLU",
        "resolved_at": ts(22, 0, 1),
        "jalons": make_jalons(
            ["Retour normal"],
            {"Retour normal": ts(22,0,1)}
        ),
    },
]

inc_objects = []
for d in incidents_data:
    inc = SitrepEntry(**d)
    db.add(inc)
    db.flush()
    inc_objects.append(inc)
db.commit()
print(f"  ✓ {len(inc_objects)} incidents créés")

# ID des incidents principaux pour référence
INC_AD      = inc_objects[2].id   # Ransomware AD
INC_RESP    = inc_objects[4].id   # Respirateurs
INC_TEL     = inc_objects[5].id   # Téléphonie
INC_CRESTVAL= inc_objects[6].id   # Crestval
INC_PACS    = inc_objects[9].id   # PACS imagerie
INC_RESTORE = inc_objects[11].id  # Restauration

# ══════════════════════════════════════════════════════════════
#  PRÉSENCES CELLULE (entrées/sorties sur 2 jours)
# ══════════════════════════════════════════════════════════════
print("\n  [2/7] Création des présences cellule...")

PRESENCES = [
    # ── J1 Activation cellule 05h30 ──────────────────────────
    (ts(5, 30), "M. BERNARD",         "Directeur Général",           "ENTREE"),
    (ts(5, 32), "Mme LECONTE",   "Directrice Générale Adjointe","ENTREE"),
    (ts(5, 35), "M. DUPUIS",        "DSI",                         "ENTREE"),
    (ts(5, 38), "M. FONTAINE",          "RSSI",                        "ENTREE"),
    (ts(5, 45), "Mme AUBERT",       "Directrice des Soins",        "ENTREE"),
    (ts(6, 0), "M. GIRARD",            "DAF",                         "ENTREE"),
    (ts(6, 10), "Mme CHEVALIER",         "Direction Médicale",          "ENTREE"),
    (ts(6, 15), "M. LAMBERT",           "Direction Achats",            "ENTREE"),
    # ── J1 Rotations ────────────────────────────────────────
    (ts(12, 0), "M. BERNARD",         "Directeur Général",           "SORTIE"),
    (ts(12, 5), "Mme LECONTE",   "Directrice Générale Adjointe","SORTIE"),
    (ts(12,10), "M. MOREAU",           "DRH",                         "ENTREE"),
    (ts(12,15), "Mme PERRIN",    "DUQEP",                       "ENTREE"),
    (ts(14, 0), "M. ROUSSEAU",           "Direction",                   "ENTREE"),
    (ts(18, 0), "M. DUPUIS",        "DSI",                         "SORTIE"),
    (ts(18, 5), "M. FONTAINE",          "RSSI",                        "SORTIE"),
    (ts(18,10), "Mme RENARD",        "Direction soins (remplaçante)","ENTREE"),
    (ts(18,20), "M. SIMON",           "Direction",                   "ENTREE"),
    # ── J1 Nuit ─────────────────────────────────────────────
    (ts(22, 0), "M. MOREAU",           "DRH",                         "SORTIE"),
    (ts(22, 5), "Mme PERRIN",    "DUQEP",                       "SORTIE"),
    (ts(22,15), "M. GARCIA",        "Direction",                   "ENTREE"),
    # ── J2 Matin ────────────────────────────────────────────
    (ts(6, 0, 1), "M. BERNARD",       "Directeur Général",           "ENTREE"),
    (ts(6, 5, 1), "M. DUPUIS",      "DSI",                         "ENTREE"),
    (ts(6,10, 1), "M. FONTAINE",        "RSSI",                        "ENTREE"),
    (ts(6,30, 1), "Mme AUBERT",     "Directrice des Soins",        "ENTREE"),
    (ts(7, 0, 1), "Mme CHEVALIER",       "Direction Médicale",          "ENTREE"),
    (ts(8, 0, 1), "M. GARCIA",      "Direction",                   "SORTIE"),
    (ts(14, 0,1), "M. GIRARD",          "DAF",                         "ENTREE"),
    # ── J2 Fin de crise ──────────────────────────────────────
    (ts(21, 0,1), "M. BERNARD",        "Directeur Général",           "SORTIE"),
    (ts(21,10,1), "M. DUPUIS",      "DSI",                         "SORTIE"),
    (ts(21,15,1), "M. FONTAINE",        "RSSI",                        "SORTIE"),
    (ts(21,30,1), "Mme AUBERT",     "Directrice des Soins",        "SORTIE"),
    (ts(22, 0,1), "Mme CHEVALIER",       "Direction Médicale",          "SORTIE"),
]

for (time, nom, role, action) in PRESENCES:
    db.add(Presence(timestamp=time, nom=nom, role=role, action=action))
db.commit()
print(f"  ✓ {len(PRESENCES)} mouvements cellule créés")

# ══════════════════════════════════════════════════════════════
#  DÉCISIONS CELLULE
# ══════════════════════════════════════════════════════════════
print("\n  [3/7] Création des décisions...")

DECISIONS = [
    (ts(5,45), "Activation officielle de la cellule de crise CHV", "M. BERNARD", "Plan Blanc"),
    (ts(5,50), "Isolation complète du réseau informatique principal — coupure VPN inter-sites", "M. DUPUIS", "NIS2"),
    (ts(5,55), "Déclenchement du plan de continuité d'activité (PCA) informatique", "M. FONTAINE", "NIS2"),
    (ts(6, 0), "Contact immédiat du CERT Santé et signalement à l'ANS", "M. FONTAINE", "NIS2"),
    (ts(6, 5), "Activation des procédures mode dégradé sur tous les services cliniques", "Mme AUBERT", "Plan Blanc"),
    (ts(6,10), "Annulation des blocs opératoires programmés non urgents de la journée J1", "Mme CHEVALIER", "Plan Blanc"),
    (ts(6,20), "Information de l'ARS Auvergne-Rhône-Alpes — signalement obligatoire NIS2", "M. BERNARD", "NIS2"),
    (ts(6,30), "Refus catégorique de payer la rançon — conformité ANSSI et position nationale", "M. BERNARD", "Règlement intérieur"),
    (ts(7, 0), "Mandatement d'un prestataire de réponse à incident cybersécurité", "M. DUPUIS", "Plan Blanc"),
    (ts(8, 0), "Point de situation toutes les 2h — prochaine réunion 10h00", "M. BERNARD", "Plan Blanc"),
    (ts(10,0), "Maintien des urgences en mode dégradé — renfort infirmier bloc urgences", "Mme AUBERT", "Plan Blanc"),
    (ts(10,5), "Communication interne aux équipes : message rassurant, consignes pratiques", "Mme LECONTE", "Plan Blanc"),
    (ts(12,0), "Décision : pas de communication presse à ce stade — suivi ARS suffisant", "M. BERNARD", "Plan Blanc"),
    (ts(14,0), "Validation du plan de restauration par priorité : urgences > soins critiques > autres", "M. DUPUIS", "NIS2"),
    (ts(16,0), "Autorisation de rappel exceptionnel du personnel DSI — heures supplémentaires", "M. MOREAU", "Plan Blanc"),
    (ts(18,0), "Communiqué public sur le site CHV : information patients et familles", "M. BERNARD", "Plan Blanc"),
    # J2
    (ts(7, 0,1), "Levée partielle de l'isolation réseau sur le site principal après validation sécurité", "M. FONTAINE", "NIS2"),
    (ts(9, 0,1), "Priorisation de la restauration : DPI > PACS > téléphonie > autres", "M. DUPUIS", "NIS2"),
    (ts(12, 0,1), "Mise en place d'une surveillance SOC renforcée 24/7 pendant 30 jours", "M. FONTAINE", "NIS2"),
    (ts(16, 0,1), "Décision de levée de la cellule de crise à J+2 22h après retour à la normale confirmé", "M. BERNARD", "Plan Blanc"),
    (ts(18, 0,1), "Engagement d'un audit de sécurité complet dans les 30 jours", "M. BERNARD", "NIS2"),
    (ts(20, 0,1), "Levée officielle de la cellule de crise — passage en phase de surveillance", "M. BERNARD", "Plan Blanc"),
]

for (time, contenu, resp, base) in DECISIONS:
    db.add(Decision(timestamp=time, contenu=contenu, responsable=resp,
                    base_reglementaire=base, statut_validation="VALIDÉ"))
db.commit()
print(f"  ✓ {len(DECISIONS)} décisions créées")

# ══════════════════════════════════════════════════════════════
#  KANBAN
# ══════════════════════════════════════════════════════════════
print("\n  [4/7] Création des tâches kanban...")

TASKS = [
    # TERMINÉ
    (ts(5,50), "Couper le VPN inter-sites", "M. DUPUIS", 4, "TERMINÉ", INC_AD,
     "Isolation immédiate pour stopper la propagation"),
    (ts(5,55), "Contacter le CERT Santé", "M. FONTAINE", 4, "TERMINÉ", INC_AD,
     "Signalement obligatoire NIS2"),
    (ts(6, 0), "Activer la procédure mode dégradé urgences", "Mme AUBERT", 4, "TERMINÉ", None,
     "Distribution fiches papier + formation rapide cadres"),
    (ts(6, 5), "Prévenir le médecin senior réanimation", "Mme CHEVALIER", 4, "TERMINÉ", INC_RESP,
     "Surveillance manuelle des respirateurs"),
    (ts(6,10), "Informer l'ARS par écrit", "M. BERNARD", 3, "TERMINÉ", INC_AD,
     "Email + appel téléphonique"),
    (ts(6,30), "Mandater prestataire cybersécurité", "M. DUPUIS", 3, "TERMINÉ", INC_AD,
     "CERT privé — contrat cadre existant"),
    (ts(7, 0), "Activer liste de contacts téléphoniques de crise", "Mme LECONTE", 3, "TERMINÉ", INC_TEL,
     "Distribution physique aux cadres de chaque service"),
    (ts(7,30), "Annuler les blocs programmés du matin", "Mme CHEVALIER", 3, "TERMINÉ", None,
     "Contact chirurgiens + patients"),
    (ts(8, 0), "Vérifier intégrité des sauvegardes hors-ligne", "M. DUPUIS", 4, "TERMINÉ", INC_AD,
     "Sauvegardes J-3 confirmées saines"),
    (ts(10,0), "Préparer message interne aux équipes", "Mme LECONTE", 2, "TERMINÉ", None,
     "Ton rassurant, consignes pratiques mode dégradé"),
    (ts(12,0), "Rédiger communiqué ARS J1", "M. BERNARD", 3, "TERMINÉ", INC_AD,
     "Rapport intermédiaire"),
    # EN COURS
    (ts(14,0), "Restaurer les serveurs par priorité", "M. DUPUIS", 4, "EN COURS", INC_RESTORE,
     "Priorité : urgences > soins critiques > admin"),
    (ts(16,0), "Investigations forensiques — analyse des logs", "M. FONTAINE", 3, "EN COURS", INC_AD,
     "Prestataire CERT sur site"),
    (ts(18,0, 0), "Préparer rapport complet pour ARS sous 72h", "M. BERNARD", 3, "EN COURS", INC_AD,
     "Rapport obligatoire NIS2 art. 23"),
    # EN ATTENTE
    (ts(6,0,1), "Restaurer PACS imagerie", "M. DUPUIS", 3, "EN ATTENTE", INC_PACS,
     "En attente validation serveurs fichiers"),
    (ts(8,0,1), "Auditer tous les postes avant reconnexion réseau", "M. FONTAINE", 3, "EN ATTENTE", INC_AD,
     "Scan antivirus + validation individuelle"),
    (ts(10,0,1), "Former les équipes à la détection de phishing", "M. MOREAU", 2, "EN ATTENTE", None,
     "Plan de formation sécurité — à planifier sous 30j"),
    # BACKLOG
    (ts(12,0,1), "Réviser la politique de sauvegarde", "M. FONTAINE", 2, "BACKLOG", None,
     "Passer à une sauvegarde quotidienne hors-ligne"),
    (ts(12,5,1), "Tester le PCA complet sur scénario ransomware", "M. DUPUIS", 2, "BACKLOG", None,
     "Exercice à planifier dans les 6 mois"),
    (ts(12,10,1), "Déployer solution EDR sur tous les postes", "M. FONTAINE", 3, "BACKLOG", None,
     "Budget à valider en COPIL SI"),
]

for (time, titre, assignee, prio, col, inc_id, desc) in TASKS:
    db.add(Task(created_at=time, titre=titre, assignee=assignee,
                priorite=prio, colonne=col, incident_id=inc_id, description=desc))
db.commit()
print(f"  ✓ {len(TASKS)} tâches kanban créées")

# ══════════════════════════════════════════════════════════════
#  RELÈVE / CONSIGNES
# ══════════════════════════════════════════════════════════════
print("\n  [5/7] Création des consignes de relève...")

CONSIGNES = [
    # J1 matin → relève midi
    (ts(11,30), "Équipe de direction de l'après-midi",
     "Situation critique maintenue. VPN coupés, réseau isolé. Mode dégradé actif sur tous services. "
     "Prochain point cellule 14h. Contacter M. DUPUIS pour tout nouveau signe d'infection.",
     True, ts(12, 5), "Sophie"),
    (ts(11,45), "Cadres de nuit / Cadres de jour soins",
     "Procédure mode dégradé papier en vigueur. Ne pas reconnecter de poste au réseau sans accord DSI. "
     "Numéros de secours distribués. Signaler immédiatement toute anomalie informatique.",
     True, ts(12,10), "Jean-Marie"),
    (ts(11,50), "Directeur de nuit J1",
     "Cellule de crise active jusqu'à la fin de l'incident. Décisions prises : voir chronologie. "
     "CERT présent sur site à partir de 14h. Communiqué ARS envoyé.",
     True, ts(13, 0), "Pierre"),
    # J1 soir → relève nuit
    (ts(20,0), "Astreinte de nuit DSI",
     "Serveurs de fichiers en cours de restauration. Ne pas toucher. Sauvegardes validées. "
     "Si anomalie : appeler M. DUPUIS direct portable. Prochaine restauration DPI prévue J2 6h.",
     True, ts(20,30), "Karim"),
    (ts(20,15), "Directeur de nuit",
     "Cellule de crise en veille pour la nuit. Effectif réduit. Contacter M. GARCIA pour toute décision urgente. "
     "Pas de communication externe sans accord DG.",
     True, ts(20,45), "Nathalie"),
    (ts(20,30), "Cadres de nuit tous services",
     "Mode dégradé maintenu cette nuit. Pas de retour réseau prévu avant demain matin. "
     "Urgences opérationnelles en mode papier. Réanimation surveillée manuellement. Situation stable.",
     True, ts(21, 0), "Laurent"),
    # J2 matin → reprise
    (ts(5,45,1), "Équipe de direction J2",
     "Nuit calme. Pas de nouvel incident. Restauration prévue à partir de 6h. "
     "Cellule de crise reprend à 6h30. Point de situation toutes les 2h.",
     True, ts(6,10,1), "Sophie"),
    (ts(6, 0,1), "DSI — Équipe du matin",
     "Restauration AD et serveurs fichiers à lancer dès 6h00. Procédure documentée en salle serveurs. "
     "DPI Axigate à restaurer en priorité 1 dès validation AD.",
     True, ts(6,20,1), "Marc"),
    # J2 → fin de crise
    (ts(20,0,1), "Tous services",
     "Levée de la cellule de crise prévue à 22h. Retour à la normale confirmé sur 90% des systèmes. "
     "Téléphonie IPBX toujours en cours de restauration (24h). Mode de secours maintenu sur téléphonie.",
     False, None, None),
    (ts(21,0,1), "Cadres de nuit — post-crise",
     "Fin de crise officielle. Surveillance renforcée maintenue 72h. "
     "Signaler immédiatement tout comportement anormal des systèmes. SOC externe actif 24/7.",
     False, None, None),
]

for (time, pour, texte, accuse, accuse_at, accuse_par) in CONSIGNES:
    db.add(Consigne(timestamp=time, pour=pour, texte=texte,
                    accuse=accuse, accuse_at=accuse_at, accuse_par=accuse_par))
db.commit()
print(f"  ✓ {len(CONSIGNES)} consignes créées")

# ══════════════════════════════════════════════════════════════
#  REX — Retours d'expérience
# ══════════════════════════════════════════════════════════════
print("\n  [6/7] Création des fiches REX...")

REXES = [
    {
        "incident_id": INC_AD,
        "created_at": ts(10, 0, 1),
        "titre": "Cyberattaque ransomware LockBit — Site principal",
        "type_crise": "CYBER",
        "duree_minutes": 46*60,
        "nb_poles": 8,
        "nb_decisions": 22,
        "nb_jalons_total": 8,
        "nb_jalons_done": 6,
        "mttd_minutes": 172,
        "mttr_minutes": 46*60,
        "points_positifs": "Sauvegardes hors-ligne disponibles et saines\nActivation rapide de la cellule de crise (1h30 après détection)\nProcédures mode dégradé efficaces sur les urgences\nCoopération excellente entre équipes soignantes et DSI\nCommunication interne rassurante et réactive",
        "points_amelio": "Délai de détection trop long (172 min entre premiers signes et diagnostic)\nPas de détection automatique de la propagation réseau\nAnnuaire de crise papier non à jour sur certains services\nCommunication avec site Crestval difficile en début d'incident",
        "actions_futures": "Déployer solution EDR sur tous les postes sous 3 mois\nTester la détection réseau (segmentation VLAN)\nMettre à jour l'annuaire de crise tous les trimestres\nOrganiser exercice ransomware complet dans les 6 mois\nFormer 100% du personnel à la détection de phishing",
        "lecons": "Un ransomware peut rester silencieux plusieurs jours avant de s'activer. La sauvegarde hors-ligne est notre meilleure protection. La rapidité d'isolation du réseau a limité la propagation.",
        "redacteur": "M. FONTAINE — RSSI",
    },
    {
        "incident_id": INC_RESP,
        "created_at": ts(12, 0, 1),
        "titre": "Perte accès postes respirateurs — Réanimation",
        "type_crise": "MIXTE",
        "duree_minutes": 265,
        "nb_poles": 1,
        "nb_decisions": 3,
        "nb_jalons_total": 3,
        "nb_jalons_done": 3,
        "mttd_minutes": 45,
        "mttr_minutes": 265,
        "points_positifs": "Réactivité exemplaire de l'équipe médicale de réanimation\nPassage en mode manuel immédiat et efficace\nAucun événement indésirable patient",
        "points_amelio": "Les postes de pilotage ne devraient pas dépendre du réseau principal\nProcédure de basculement manuel pas connue de tous les infirmiers",
        "actions_futures": "Isoler les équipements biomédicaux critiques sur un réseau dédié\nFormation annuelle mode dégradé réanimation",
        "lecons": "Les équipements biomédicaux connectés représentent un risque majeur en cas de cyberattaque. L'isolation réseau doit être anticipée.",
        "redacteur": "Dr. MARTIN — Anesthésiste référent",
    },
    {
        "incident_id": INC_TEL,
        "created_at": ts(14, 0, 1),
        "titre": "Panne IPBX — Communication interne dégradée",
        "type_crise": "CYBER",
        "duree_minutes": 42*60,
        "nb_poles": 5,
        "nb_decisions": 2,
        "nb_jalons_total": 3,
        "nb_jalons_done": 2,
        "mttd_minutes": 250,
        "mttr_minutes": 42*60,
        "points_positifs": "Activation rapide de la téléphonie de secours\nAnnuaire de secours disponible et distribué efficacement",
        "points_amelio": "Délai trop long pour distribuer l'annuaire aux étages\nCertains cadres ne connaissaient pas la procédure de secours",
        "actions_futures": "Afficher l'annuaire de secours de façon permanente dans chaque service\nTest annuel de la bascule téléphonie de secours",
        "lecons": "La téléphonie est un service critique souvent sous-estimé. Sa dépendance au réseau IP la rend vulnérable lors d'une cyberattaque.",
        "redacteur": "Responsable téléphonie CHV",
    },
    {
        "incident_id": INC_CRESTVAL,
        "created_at": ts(16, 0, 1),
        "titre": "Propagation ransomware via VPN — Site Crestval",
        "type_crise": "CYBER",
        "duree_minutes": 18*60,
        "nb_poles": 3,
        "nb_decisions": 4,
        "nb_jalons_total": 5,
        "nb_jalons_done": 3,
        "mttd_minutes": 195,
        "mttr_minutes": 18*60,
        "points_positifs": "Isolation locale rapide effectuée par l'équipe sur place\nFonctionnement en mode île efficace",
        "points_amelio": "Le VPN inter-sites aurait dû être coupé plus tôt\nManque de coordination initiale avec le site principal",
        "actions_futures": "Mettre en place une coupure automatique VPN en cas d'alerte critique\nDotation d'un kit de crise cyber autonome sur chaque site secondaire",
        "lecons": "Les sites secondaires sont des vecteurs de propagation. Chaque site doit avoir la capacité d'isolement autonome.",
        "redacteur": "Cadre responsable site Crestval",
    },
    {
        "incident_id": INC_PACS,
        "created_at": ts(18, 0, 1),
        "titre": "PACS/RIS hors service — Impact imagerie médicale",
        "type_crise": "CYBER",
        "duree_minutes": 22*60,
        "nb_poles": 2,
        "nb_decisions": 2,
        "nb_jalons_total": 4,
        "nb_jalons_done": 3,
        "mttd_minutes": 365,
        "mttr_minutes": 22*60,
        "points_positifs": "Continuité des acquisitions d'images (réalisées mais non consultables)\nPas de report des examens urgents",
        "points_amelio": "Aucune procédure de visualisation d'images hors PACS n'existe\nLe délai de restauration (22h) est trop long pour un service critique",
        "actions_futures": "Mettre en place une solution de visualisation d'images hors-réseau\nPrioriser le PACS dans le plan de reprise informatique",
        "lecons": "L'imagerie médicale est désormais 100% numérique. Sa disponibilité doit être traitée comme un service vital au même titre que l'électricité.",
        "redacteur": "Cadre service imagerie",
    },
]

for d in REXES:
    db.add(RexEntry(**d))
db.commit()
print(f"  ✓ {len(REXES)} fiches REX créées")

# ══════════════════════════════════════════════════════════════
#  COMMUNIQUÉS PUBLICS
# ══════════════════════════════════════════════════════════════
print("\n  [7/7] Création des communiqués publics...")

# Récupérer le site principal de StatusPage ou créer
def get_or_create_sp(site_id, site_nom):
    row = db.query(StatusPage).filter_by(site_id=site_id).first()
    if not row:
        row = StatusPage(site_id=site_id, site_nom=site_nom)
        db.add(row)
        db.flush()
    return row

# Communiqué global établissement
sp_global = get_or_create_sp(0, "")
sp_global.niveau_global = "PERTURBE"
sp_global.message_public = (
    "Le Centre Hospitalier de Valmont a été victime d'une cyberattaque dans la nuit du "
    + J1_00.strftime("%d/%m/%Y") +
    ". Nos équipes travaillent activement au rétablissement complet de nos systèmes. "
    "La continuité des soins est assurée. Toutes les urgences sont opérationnelles."
)
sp_global.services_si = json.dumps([
    {"id": "dpi",       "label": "Logiciels métier / DPI",    "statut": "DEGRADE"},
    {"id": "pacs",      "label": "Imagerie (PACS / RIS)",     "statut": "CRITIQUE"},
    {"id": "telephonie","label": "Téléphonie",                "statut": "DEGRADE"},
    {"id": "messagerie","label": "Messagerie interne",        "statut": "DEGRADE"},
    {"id": "internet",  "label": "Accès Internet",            "statut": "CRITIQUE"},
    {"id": "vpn",       "label": "Accès distants / VPN",      "statut": "CRITIQUE"},
])
sp_global.prise_en_charge = json.dumps([
    {"id": "urgences",    "label": "Urgences",               "statut": "OK"},
    {"id": "blocs",       "label": "Blocs opératoires",      "statut": "DEGRADE"},
    {"id": "consultations","label": "Consultations",         "statut": "OK"},
    {"id": "hospit",      "label": "Hospitalisations programmées", "statut": "DEGRADE"},
    {"id": "imagerie",    "label": "Imagerie patients",      "statut": "CRITIQUE"},
    {"id": "labo",        "label": "Laboratoire",            "statut": "OK"},
])
sp_global.faq = json.dumps([
    {"question": "Mes données personnelles sont-elles compromises ?",
     "reponse": "Une enquête est en cours. Par précaution, considérez que vos données ont pu être exposées. Nous vous tiendrons informés.",
     "visible": True},
    {"question": "Puis-je venir à mes rendez-vous prévus ?",
     "reponse": "Les consultations urgentes et les hospitalisations en cours sont maintenues. Les consultations programmées non urgentes peuvent être reportées. Contactez votre service.",
     "visible": True},
    {"question": "Les urgences sont-elles opérationnelles ?",
     "reponse": "Oui, les urgences restent pleinement opérationnelles. Une procédure de prise en charge adaptée est en place.",
     "visible": True},
])
sp_global.published = True
sp_global.updated_by = "M. BERNARD — DG"
db.flush()

# Communiqué site secondaire Crestval
sp_crestval = get_or_create_sp(sec_id, "Site Secondaire — Crestval")
sp_crestval.niveau_global = "ALERTE"
sp_crestval.message_public = "Site Crestval : systèmes informatiques isolés par mesure de précaution. Les soins sont assurés en mode dégradé. Retour à la normale en cours."
sp_crestval.services_si = json.dumps([
    {"id": "dpi",       "label": "DPI",           "statut": "CRITIQUE"},
    {"id": "telephonie","label": "Téléphonie",     "statut": "DEGRADE"},
    {"id": "internet",  "label": "Accès Internet", "statut": "CRITIQUE"},
])
sp_crestval.published = True
sp_crestval.updated_by = "Cadre Crestval"
db.flush()

# Chronologie publique
chrons = [
    (ts(6, 30),  "Incident informatique en cours — nos équipes mobilisées. Urgences opérationnelles.", "M. BERNARD"),
    (ts(8, 0),   "Cyberattaque confirmée. Cellule de crise activée. Autorités compétentes prévenues (ARS, CERT Santé).", "M. BERNARD"),
    (ts(12, 0),  "Situation stabilisée. Soins continus assurés en mode adapté. Restauration en cours.", "Mme LECONTE"),
    (ts(18, 0),  "Bilan J1 : pas d'impact patient. Restauration des systèmes prioritaires entamée.", "M. BERNARD"),
    (ts(8, 0, 1), "J+1 : restauration progressive. DPI en cours de remise en service.", "M. DUPUIS"),
    (ts(16, 0,1), "Retour à la normale en cours. DPI opérationnel sur le site principal.", "M. DUPUIS"),
    (ts(22, 0,1), "Fin de la phase de crise. Surveillance renforcée maintenue 72h. Merci de votre compréhension.", "M. BERNARD"),
]
for (time, texte, auteur) in chrons:
    db.add(StatusPageChronologie(timestamp=time, texte=texte, publie_par=auteur))
db.commit()
print(f"  ✓ Communiqué global publié + {len(chrons)} entrées chronologie")

# ══════════════════════════════════════════════════════════════
#  RÉCAPITULATIF
# ══════════════════════════════════════════════════════════════
db.close()

print("\n" + "═"*62)
print("  ✅  Scénario de crise injecté avec succès !")
print("═"*62)
print(f"""
  Contenu injecté :
  • {len(incidents_data)} incidents  (J1 02h → J2 22h)
  • {len(PRESENCES)} mouvements cellule de crise
  • {len(DECISIONS)} décisions actées
  • {len(TASKS)} tâches kanban
  • {len(CONSIGNES)} consignes de relève
  • {len(REXES)} fiches REX
  • 1 communiqué public + {len(chrons)} entrées chronologie

  ─── DÉMARRAGE ──────────────────────────────────────────
  $ python main.py
  Puis ouvrez : http://localhost:8000

  ─── CONNEXION ──────────────────────────────────────────
  Login    : dircrise
  Mot de passe : Scribe2026!

  ─── POUR TESTER L'ONGLET ANALYSE ───────────────────────
  1. Connectez-vous sur http://localhost:8000
  2. Onglet VEILLE → bouton 📋 EXPORT MAIN COURANTE
  3. Bouton 🔄 NOUVELLE CRISE → archiver → ZIP créé dans archives/
  4. Onglet ANALYSE → glisser le ZIP
  5. Explorer la frise chronologique, poser des questions à Albert
  6. Exporter le rapport DOCX de debriefing

  ─── SCÉNARIO ───────────────────────────────────────────
  Cyberattaque ransomware LockBit sur le CHV Valmont
  Début : {J1_00.strftime('%d/%m/%Y %H:%M')} UTC
  Fin   : {(J1_00+timedelta(hours=46)).strftime('%d/%m/%Y %H:%M')} UTC
  Impact : 5 sites, 8 pôles cliniques, 15 incidents

""")
