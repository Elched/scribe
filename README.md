# SCRIBE — Release Candidate 1.0.0

> Main courante numérique de gestion de crise hospitalière  
> Cyber · Sanitaire · Mixte · Plan Blanc · ORSAN  
> Open source — Licence MIT — https://github.com/nocomp/scribe

---

## Supervision territoriale multi-établissements

![Collecteur territorial — supervision temps réel](screenshots/supervision.png)

*Collecteur territorial — 1 établissement en ALERTE, incident cyber actif, statut public publié*

---

## Fonctionnalités

### 🌐 Veille — Main courante

![Onglet Veille](screenshots/acc.png)

Formulaire de déclaration d'incident à gauche, liste des incidents filtrables à droite avec carte Leaflet multi-sites. Jalons de résolution pré-configurés (CERT Santé, isolation réseau…), pièces jointes, analyse IA Albert en un clic.

---

### 🏥 Soins — Cartographie de situation

![Onglet Soins](screenshots/soin.png)

Vue par pôles cliniques avec statut opérationnel / mode dégradé / impact critique. Projection temporelle de retour à la normale. Analyse capacitaire IA. Services transverses (sécurité physique, logistique).

---

### 🏛️ Cellule — Coordination

![Onglet Cellule](screenshots/celulle.png)

Registre des présences en temps réel (entrées/sorties horodatées). Chronologie décisionnelle avec base réglementaire (Plan Blanc, NIS2…). Traçabilité complète des décisions de crise.

---

### 📋 Kanban — Tableau de bord opérationnel

![Onglet Kanban](screenshots/kaban.png)

Tableau Backlog / En cours / En attente / Terminé. Glisser-déposer. Liaison directe avec les incidents. Priorités et assignataires.

---

### 📊 REX — Retour d'expérience

![Onglet REX](screenshots/rex.png)

Fiche REX structurée en 3 sections : informations générales, chronologie (MTTD/MTTR), bilan. Génération automatique depuis un incident existant. Export DOCX. Dashboard agrégé.

---

### 🔄 Relève — Consignes de prise en charge

![Onglet Relève](screenshots/releve.png)

Transmission de consignes horodatées avec accusé de réception. Traçabilité des passations entre équipes. Journal de relève chronologique.

---

### 📞 Annuaire — Contacts nominaux et de secours

![Onglet Annuaire](screenshots/annuaire.png)

Annuaire alphabétique avec recherche instantanée. Basculement en un clic entre téléphonie normale et téléphonie de secours. Instructions de secours affichées en cas de crise cyber/IPBX.

---

## Architecture

```
scribe_suite/
├── README.md
├── screenshots/              ← Captures d'écran
├── collecteur/               ← Superviseur territorial (CERT Santé, ARS, GHT)
│   ├── collecteur.py
│   ├── collecteur_requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
└── scribe/                   ← Client SCRIBE (un déploiement par établissement)
    ├── main.py
    ├── setup.py              ← Init depuis config.xml
    ├── setup_demo1.py        ← Init démo CHV Valmont (prêt à l'emploi)
    ├── setup_demo2.py        ← Init démo CSBM Montrelay (prêt à l'emploi)
    ├── setup_chag.py         ← Init avec uf.xlsx FICOM (usage interne CHAG)
    ├── import_uf2.py         ← Import UF depuis Excel FICOM
    ├── config.xml            ← Template de configuration
    ├── config_demo1.xml      ← Config démo CHV
    ├── config_demo2.xml      ← Config démo CSBM
    ├── uf_modele.xlsx        ← Modèle Excel 37 UF génériques
    ├── requirements.txt
    └── app/
        ├── api/              ← 14 modules FastAPI
        ├── static/           ← SPA index.html (8 onglets), status.html
        ├── models.py         ← 14 tables SQLAlchemy
        └── database.py
```

---

## Prérequis

```bash
Python 3.9+
pip install -r requirements.txt             # SCRIBE
pip install -r collecteur_requirements.txt  # Collecteur
```

---

## Démarrage rapide — Instance unique

```powershell
# Windows PowerShell
copy config_demo1.xml config.xml
python setup_demo1.py
python main.py
```

Ouvrir http://localhost:8000 — login : `dircrise` / `Scribe2026!`

```bash
# Linux / Mac
cp config_demo1.xml config.xml
python3 setup_demo1.py
python3 main.py
```

---


---

## ⚠️ Comprendre les deux tokens — LIRE AVANT TOUT

La connexion entre SCRIBE et le collecteur repose sur **deux tokens distincts** qui ont des rôles différents. C'est le point qui prête le plus à confusion.

| Token | Où il apparaît | À quoi il sert |
|---|---|---|
| **Token admin collecteur** | Affiché au démarrage du collecteur | Administrer le collecteur (créer/supprimer des établissements) |
| **Token établissement** | Dans `config.xml` de SCRIBE | Authentifier les pushs de données de SCRIBE vers le collecteur |

### Règle absolue

```
Token admin   → uniquement dans le -H "Authorization: Bearer ..."  de la commande curl
Token établissement → dans config.xml <federation><token> ET dans le -d '{"token":"..."}' du curl
```

**Ces deux tokens ne doivent jamais être identiques.**

---

### Exemple concret pas à pas

**1. Démarrer le collecteur — noter le token admin**

```
Token admin : 5de7a658292d49f90284e45185c500eeb982ce3934c6cd8977b708dd5c0e532c
```
→ Ce token sert **uniquement** à administrer le collecteur. Il ne va nulle part dans SCRIBE.

**2. Choisir un token pour l'établissement CHV**

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
# → a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2
```

**3. Mettre CE token dans config.xml de SCRIBE**

```xml
<federation>
  <enabled>true</enabled>
  <collecteur_url>http://192.168.1.109:9000/api/push</collecteur_url>
  <token>a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2</token>
</federation>
```

**4. Relancer SCRIBE**

```powershell
python setup_demo1.py
python main.py
```

**5. Enregistrer l'établissement dans le collecteur**

```bash
curl -X POST http://localhost:9000/api/admin/tokens   -H "Authorization: Bearer 5de7a658292d49f90284e45185c500eeb982ce3934c6cd8977b708dd5c0e532c"   -H "Content-Type: application/json"   -d '{"sigle":"CHV","token":"a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"}'
```

→ `Authorization: Bearer` = **token admin** (affiché au démarrage du collecteur)  
→ `"token":` dans `-d` = **token établissement** (celui que tu as mis dans config.xml)

**6. Vérification**

Dans les logs SCRIBE dans les 30 secondes :
```
INFO:httpx:HTTP Request: POST http://192.168.1.109:9000/api/push "HTTP/1.1 200 OK"
```

---

## Déploiement multi-sites — Séquence de démarrage

> **Règle absolue : toujours démarrer le collecteur en premier**, avant les instances SCRIBE.

### Étape 1 — Démarrer le collecteur

```bash
cd collecteur/
python3 collecteur.py
```

Au démarrage, le token admin s'affiche — il est **persistant entre les redémarrages** :

```
╔══════════════════════════════════════════════╗
║  SCRIBE Collecteur territorial               ║
╚══════════════════════════════════════════════╝
Dashboard     : http://0.0.0.0:9000
Token admin   : abc123def456...
(persistant dans collecteur_admin.json)
```

### Étape 2 — Choisir un token pour chaque établissement

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
# → f3a8b2c1d4e5f6a7b8c9d0e1f2a3b4c5...
```

### Étape 3 — Configurer config.xml côté SCRIBE

```xml
<federation>
  <enabled>true</enabled>
  <collecteur_url>http://[IP_COLLECTEUR]:9000/api/push</collecteur_url>
  <token>f3a8b2c1d4e5f6a7b8c9d0e1f2a3b4c5...</token>
  <intervalle_secondes>30</intervalle_secondes>
  <share_details>true</share_details>
  <share_min_urgency>1</share_min_urgency>
</federation>
```

### Étape 4 — Initialiser et démarrer SCRIBE

```powershell
python setup_demo1.py
python main.py
```

### Étape 5 — Enregistrer l'établissement dans le collecteur

```bash
curl -X POST http://[IP_COLLECTEUR]:9000/api/admin/tokens \
  -H "Authorization: Bearer TOKEN_ADMIN_COLLECTEUR" \
  -H "Content-Type: application/json" \
  -d '{"sigle":"CHV","token":"f3a8b2c1d4e5f6a7b8c9d0e1f2a3b4c5..."}'
```

Le token dans `{"token":"..."}` doit correspondre **exactement** à celui dans `config.xml`.

### Vérification

Dans les logs SCRIBE au démarrage :
```
INFO:scribe.federation:Federation activée → http://[IP]:9000/api/push
INFO:httpx:HTTP Request: POST http://[IP]:9000/api/push "HTTP/1.1 200 OK"
```

---

## POC — 2 SCRIBE + 1 collecteur

| Machine | Rôle | IP | Config |
|---|---|---|---|
| PC-A | SCRIBE Démo 1 | 192.168.1.10 | `config_demo1.xml` + token CHV |
| PC-B | SCRIBE Démo 2 | 192.168.1.11 | `config_demo2.xml` + token CSBM |
| PC-C | Collecteur | 192.168.1.20 | — |

```bash
# 1. PC-C — démarrer le collecteur, noter le token admin
python3 collecteur.py

# 2. PC-C — enregistrer les deux établissements
curl -X POST http://localhost:9000/api/admin/tokens \
  -H "Authorization: Bearer TOKEN_ADMIN" \
  -H "Content-Type: application/json" \
  -d '{"sigle":"CHV","token":"token_chv_choisi"}'

curl -X POST http://localhost:9000/api/admin/tokens \
  -H "Authorization: Bearer TOKEN_ADMIN" \
  -H "Content-Type: application/json" \
  -d '{"sigle":"CSBM","token":"token_csbm_choisi"}'

# 3. PC-A — éditer collecteur_url + token CHV dans config_demo1.xml
copy config_demo1.xml config.xml
python setup_demo1.py
python main.py

# 4. PC-B — éditer collecteur_url + token CSBM dans config_demo2.xml
copy config_demo2.xml config.xml
python setup_demo2.py
python main.py
```

Dashboard collecteur : http://192.168.1.20:9000

---

## Initialisation from scratch (nouvel établissement)

**1. Remplir `config.xml`**

| Section | Contenu |
|---|---|
| `<etablissement>` | Nom, sigle, FINESS |
| `<admin>` | Login et mot de passe initial |
| `<sites>` | Sites géographiques avec coordonnées GPS |
| `<directeurs>` | Directeurs de crise (liste déroulante formulaire) |
| `<annuaire_normal>` | Contacts nominaux (VoIP/DECT) |
| `<annuaire_secours>` | Contacts de secours (GSM, fixes cuivre) |
| `<ia>` | Fournisseur IA et clé API |
| `<federation>` | Désactivée par défaut |

**2. Initialiser**
```bash
python setup.py
```

**3. Importer les UF FICOM** (optionnel)
```bash
python import_uf2.py votre_export_ficom.xlsx
```

**4. Démarrer**
```bash
python main.py
# → http://localhost:8000
```

---

## Page de statut publique

Chaque SCRIBE expose une page accessible **sans authentification** :

| URL | Usage |
|---|---|
| `http://[IP]:8000/status` | Page HTML — prestataires, journalistes, ARS |
| `http://[IP]:8000/api/v1/status/public` | JSON — intégrations tierces |

**Publication** : onglet **📢 COMMUNIQUÉ** → définir le niveau → rédiger le message → cocher l'état des services SI et PEC → **Publier**

Le collecteur récupère automatiquement les statuts publiés dans l'onglet **▦ Statuts publics**.

---

## Fournisseurs IA

| `<fournisseur>` | Souverain | Clé API | Modèle par défaut |
|---|---|---|---|
| `albert` | ✓ FR (DINUM) | Optionnelle | Ministral-3-8B |
| `ollama` | ✓ Local | Non | llama3 |
| `openai` | ✗ | Oui | gpt-4o-mini |
| `anthropic` | ✗ | Oui | claude-haiku |
| `gemini` | ✗ | Oui | gemini-2.0-flash |
| `mistral` | FR | Oui | mistral-small |
| `openai_compat` | — | Optionnelle | LM Studio / vLLM |

---

## Docker

```bash
# SCRIBE
cd scribe/
docker compose up -d

# Collecteur
cd collecteur/
docker compose up -d
docker compose logs | grep "Token admin"
```

---

## Sécurité et conformité

- **NIS2** : notification suggérée par l'IA pour tout incident cyber U3+
- **CERT Santé** : contact pré-renseigné dans l'annuaire de secours
- **HDS** : 100% on-premise, réseau isolé supporté, aucune donnée externe sans action explicite
- **Fédération** : aucune donnée nominative dans les payloads push
- **Statut public** : publication délibérée uniquement — rien n'est exposé par défaut
- **Auth** : JWT HS256, SHA-256 passwords, pas de LDAP/AD requis

---

## Changelog RC 1.0.0

- 8 onglets : Veille, Soins, Cellule, Kanban, REX, Relève, Annuaire, Communiqué
- Collecteur territorial multi-établissements temps réel
- Cartographie GPS avec marqueurs et niveaux d'alerte
- Statuts publics dans le collecteur (push automatique)
- Page `/status` publique sans authentification
- Services transverses Sécurité physique / Logistique
- Export DOCX rapport de crise
- 7 fournisseurs IA
- Scripts de démo prêts à l'emploi (CHV Valmont, CSBM Montrelay)
- Token admin collecteur persistant entre les redémarrages
- Libellés UF métier dans la supervision territoriale

---

*CERT Santé : cert-sante@esante.gouv.fr — ANSSI : cybermalveillance.gouv.fr*  
*Dépôt : https://github.com/nocomp/scribe — Licence MIT*
