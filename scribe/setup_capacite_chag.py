"""
setup_capacite_chag.py — Charge le référentiel capacitaire CHAG dans la base SCRIBE.
Données extraites du BedManager CHAG (fichier Capacitaire_lits.xlsm).
Lancer après setup.py ou setup_chag.py :  python setup_capacite_chag.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models import CapaciteReferentiel

UNITES = [
    # (service_nom, uf_code, pole, site, capacite_totale, tension_1, tension_2,
    #  accept_H, accept_F, accept_I, telephone_cadre, ordre)

    # ── ANNECY — MÉDECINE ────────────────────────────────────────────────
    ("CARDIO USC",              "5710", "MÉDECINE",    "Annecy", 12, 0, 0, True,  True,  False, "63 67 83 / 63 61 35", 1),
    ("CARDIOLOGIE 1",           "5600", "MÉDECINE",    "Annecy",  9, 1, 0, True,  True,  False, "63 67 83 / 63 66 51", 2),
    ("CARDIOLOGIE 2",           "5600", "MÉDECINE",    "Annecy",  8, 0, 1, True,  True,  False, "63 67 83 / 63 64 32", 3),
    ("DERMATO",                 "4400", "MÉDECINE",    "Annecy",  8, 0, 0, True,  True,  True,  "49 73 72 / 52 20 07", 4),
    ("HDS MÉDECINE",            "2010", "MÉDECINE",    "Annecy", 12, 0, 0, True,  True,  True,  "63 62 41 / 63 61 30", 5),
    ("HÉMATOLOGIE",             "5101", "MÉDECINE",    "Annecy", 20, 0, 0, True,  True,  True,  "63 68 26 / 58 59 62", 6),
    ("HÉPATO/GASTRO",           "5201", "MÉDECINE",    "Annecy", 25, 0, 1, True,  True,  True,  "63 64 84 / 58 57 18", 7),
    ("INFECTIEUX HC",           "5401", "MÉDECINE",    "Annecy", 24, 0, 1, True,  True,  True,  "63 63 16 / 63 67 42", 8),
    ("NÉPHOLOGIE",              "7611", "MÉDECINE",    "Annecy", 16, 0, 1, True,  True,  True,  "63 64 11 / 63 61 29", 9),
    ("NEUROLOGIE",              "5900", "MÉDECINE",    "Annecy", 15, 0, 1, True,  True,  False, "63 68 64 / 49 72 23", 10),
    ("NEUROLOGIE POST AIGU UNV","5940", "MÉDECINE",    "Annecy",  6, 0, 0, True,  True,  True,  "63 68 64 / 49 72 23", 11),
    ("NEUROLOGIE SI UNV",       "5950", "MÉDECINE",    "Annecy",  7, 0, 0, True,  True,  True,  "63 68 64 / 49 72 63", 12),
    ("ONCOLOGIE",               "5110", "MÉDECINE",    "Annecy", 20, 0, 0, True,  True,  True,  "63 61 93 / 63 67 37", 13),
    ("PNEUMOLOGIE",             "6120", "MÉDECINE",    "Annecy", 28, 0, 0, True,  True,  True,  "63 68 65 / 49 73 22", 14),
    ("RHUMATO",                 "4100", "MÉDECINE",    "Annecy", 20, 0, 0, True,  True,  True,  "49 73 72 / 58 41 00", 15),
    ("GÉRIATRIE AIGUË Annecy",  "5500", "MÉDECINE",    "Annecy", 20, 0, 0, True,  True,  True,  "63 67 31 / 63 61 77", 16),
    ("UPUM",                    "7420", "MÉDECINE",    "Annecy", 31, 0, 0, True,  True,  True,  "63 67 40 / 58 54 71", 17),
    ("UNITÉ HIVERNALE",         "7430", "MÉDECINE",    "Annecy", 12, 0, 0, True,  True,  True,  "52 21 24 / 52 21 35", 18),
    ("UNITÉ HIVERNALE 2",       "7431", "MÉDECINE",    "Annecy",  8, 0, 0, True,  True,  True,  "52 21 24 / 52 21 39", 19),

    # ── ANNECY — CHIRURGIE ──────────────────────────────────────────────
    ("CHIR. CARDIAQUE",         "6600", "CHIRURGIE",   "Annecy", 12, 0, 0, True,  True,  True,  "63 69 21 / 63 69 30", 20),
    ("CHIR. DIGESTIVE",         "6001", "CHIRURGIE",   "Annecy", 25, 0, 1, True,  True,  True,  "63 63 76 / 58 53 01", 21),
    ("GYNÉCO",                  "6800", "CHIRURGIE",   "Annecy", 13, 0, 0, False, True,  False, "63 68 20 / 63 61 21", 22),
    ("NEUROCHIRURGIE",          "6010", "CHIRURGIE",   "Annecy", 20, 0, 0, True,  True,  True,  "63 71 18 / 63 71 16", 23),
    ("ORTHO",                   "6711", "CHIRURGIE",   "Annecy", 38, 0, 1, True,  True,  True,  "63 62 62 / 63 63 56", 24),
    ("ORL/OPH/CMF",         "7010/6900","CHIRURGIE",   "Annecy", 20, 0, 0, True,  True,  True,  "63 62 83 / 63 67 47", 25),
    ("URO/THOR/VASCULAIRE",  "6003/6100","CHIRURGIE",  "Annecy", 23, 0, 1, True,  True,  True,  "63 65 08 / 63 65 00", 26),

    # ── ANNECY — REA / URGENCES ─────────────────────────────────────────
    ("RÉANIMATION",             "7900", "REA/URGENCES","Annecy", 16, 0, 0, True,  True,  True,  "63 64 05 / 63 60 95", 30),
    ("SIPO",                    "6610", "REA/URGENCES","Annecy", 12, 0, 0, True,  True,  True,  "63 69 21 / 63 69 31", 31),
    ("UHCD",                    "7410", "REA/URGENCES","Annecy", 14, 0, 0, True,  True,  True,  "63 71 40 / 63 61 17", 32),
    ("USIP",                    "7910", "REA/URGENCES","Annecy",  8, 0, 0, True,  True,  True,  "63 63 98 / 58 52 13", 33),
    ("USIC",                    "5700", "REA/URGENCES","Annecy", 12, 0, 2, True,  True,  True,  "63 67 83 / 63 63 57", 34),

    # ── ANNECY — SOINS PALLIATIFS ───────────────────────────────────────
    ("SOINS PALLIATIFS",        "5121", "SP",          "Annecy", 12, 0, 0, True,  True,  True,  "63 71 08 / 52 20 76", 40),

    # ── ANNECY — FME (Femme-Mère-Enfant) ───────────────────────────────
    ("GRANDS ENFANTS",          "6300", "FME",         "Annecy", 18, 0, 0, True,  True,  True,  "63 66 67 / 63 63 25", 50),
    ("NÉONAT",                  "6220", "FME",         "Annecy",  8, 0, 0, True,  True,  True,  "63 63 23 / 49 74 41", 51),
    ("SI NÉONAT",               None,   "FME",         "Annecy",  6, 0, 0, True,  True,  True,  "63 63 23 / 49 74 41", 52),
    ("NOURRISSONS",             "6200", "FME",         "Annecy", 18, 0, 0, True,  True,  True,  "63 60 43",            53),
    ("OBSTÉTRIQUE",             "7700", "FME",         "Annecy", 40, 0, 0, False, True,  False, "63 61 22 / 58 56 51", 54),
    ("USIP PÉDIATRIE",          "6330", "FME",         "Annecy",  6, 0, 0, True,  True,  True,  "63 66 56 / 63 67 99", 55),

    # ── ANNECY — PSY ────────────────────────────────────────────────────
    ("UNITÉ GAUGUIN",           "8003", "PSY",         "Annecy", 24, 2, 0, True,  True,  True,  "63 70 95 / 63 70 67", 60),
    ("UPUP",                    "8200", "PSY",         "Annecy",  9, 0, 0, True,  True,  True,  "63 65 17 / 63 64 01", 61),
    ("UPUP ADO",                "8250", "PSY",         "Annecy",  6, 0, 0, True,  True,  True,  "52 21 15 / 52 21 00", 62),

    # ── SAINT-JULIEN ─────────────────────────────────────────────────────
    ("ADDICTO St-Julien",       "5020", "MÉDECINE",    "Saint-Julien", 12, 0, 0, True, True, True,  "30 11 52",            70),
    ("CARDIOLOGIE St-Julien",   "5620", "MÉDECINE",    "Saint-Julien", 18, 0, 0, True, True, False, "49 65 69 / 51 14 54", 71),
    ("CHIRURGIE St-Julien",     "7320", "CHIRURGIE",   "Saint-Julien", 18, 0, 1, True, True, True,  "30 10 69 / 30 10 92", 72),
    ("MÉDECINE POLYVALENTE",    "5430", "MÉDECINE",    "Saint-Julien", 24, 0, 1, True, True, True,  "49 67 33 / 30 11 66", 73),
    ("NEURO UNV St-Julien",  "5970/5980","MÉDECINE",   "Saint-Julien", 12, 0, 0, True, True, True,  "49 65 44 / 30 11 51", 74),
    ("OBSTÉTRIQUE St-Julien",   "7740", "FME",         "Saint-Julien", 18, 0, 0, False,True, False, "49 66 09 / 51 18 10", 75),
    ("PNEUMO St-Julien",        "6140", "MÉDECINE",    "Saint-Julien", 10, 0, 0, True, True, True,  "49 65 99 / 49 67 52", 76),
    ("SOINS CONTINUS St-Julien","7920", "REA/URGENCES","Saint-Julien",  8, 1, 0, True, True, True,  "49 67 13 / 49 65 84", 77),
    ("GÉRIATRIE AIGUË St-Julien","5550","MÉDECINE",    "Saint-Julien", 10, 0, 1, True, True, True,  "49 65 99 / 51 17 19", 78),

    # ── RUMILLY ──────────────────────────────────────────────────────────
    ("CARDIO GÉRIATRIE Rumilly",None,   "MÉDECINE",    "Rumilly", 10, 0, 0, True, True, True,  "04 50 01 80 67", 80),
    ("MÉDECINE Rumilly",        None,   "MÉDECINE",    "Rumilly", 15, 0, 0, True, True, True,  "04 50 01 80 31", 81),

    # ── USLD / EHPAD ─────────────────────────────────────────────────────
    ("USLD",                    None,   "LONG SÉJOUR", "USLD/EHPAD", 30, 0, 0, True, True, True, "49 77 70", 90),
    ("UHR",                     None,   "LONG SÉJOUR", "USLD/EHPAD", 12, 0, 0, True, True, True, "49 77 70", 91),
    ("UCC",                     None,   "LONG SÉJOUR", "USLD/EHPAD",  5, 0, 0, True, True, True, "49 77 67", 92),
    ("SMR",                     None,   "LONG SÉJOUR", "USLD/EHPAD", 28, 0, 0, True, True, True, "49 77 67", 93),
    ("EHPAD St François",       None,   "EHPAD",       "USLD/EHPAD", 36, 0, 0, True, True, True, "30 30 09", 94),
    ("EHPAD Baudelaire",        None,   "EHPAD",       "USLD/EHPAD", 88, 0, 0, True, True, True, "49 66 12", 95),
]

def run():
    db = SessionLocal()
    try:
        existants = {r.service_nom for r in db.query(CapaciteReferentiel).all()}
        nb_crees = 0
        for row in UNITES:
            nom = row[0]
            if nom in existants:
                continue
            ref = CapaciteReferentiel(
                service_nom=nom, uf_code=row[1], pole=row[2],
                site=row[3], capacite_totale=row[4],
                tension_1=row[5], tension_2=row[6],
                accept_homme=row[7], accept_femme=row[8],
                accept_indiffer=row[9], telephone_cadre=row[10],
                ordre_affichage=row[11],
            )
            db.add(ref)
            nb_crees += 1
        db.commit()
        print(f"  ✓ {nb_crees} unités créées ({len(existants)} existantes ignorées)")
        print(f"  ✓ Total référentiel : {db.query(CapaciteReferentiel).count()} unités")
    finally:
        db.close()

if __name__ == "__main__":
    run()
