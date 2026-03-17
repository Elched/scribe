# SCRIBE — Version 1.1.0
## Main courante numérique de gestion de crise hospitalière

> **English version below** — [Jump to English](#scribe--hospital-crisis-management-platform)

---

**SCRIBE** est une application open-source de gestion de crise pour les établissements de santé.  
Elle fonctionne en **réseau isolé**, sans Internet, sans LDAP, sans dépendance cloud.  
Licence MIT — Dépôt : https://github.com/nocomp/scribe

---

## Captures d'écran

| Veille & Incidents | Soins |
|---|---|
| ![Veille](screenshots/acc.png) | ![Soins](screenshots/soin.png) |

| Cellule | Kanban |
|---|---|
| ![Cellule](screenshots/celulle.png) | ![Kanban](screenshots/kaban.png) |

| REX | Relève |
|---|---|
| ![REX](screenshots/rex.png) | ![Relève](screenshots/releve.png) |

| Annuaire | Collecteur — Supervision |
|---|---|
| ![Annuaire](screenshots/annuaire.png) | ![Collecteur](screenshots/collecteur_supervision.png) |

| Collecteur — Statuts publics | Collecteur — Cartographie |
|---|---|
| ![Statuts](screenshots/collecteur_statuts.png) | ![Carto](screenshots/collecteur_carto.png) |

---

## Fonctionnalités

- **Veille & Incidents** — Déclaration, suivi, jalons de résolution, IA intégrée
- **Soins** — Cartographie des pôles cliniques, projection retour à la normale
- **Cellule de crise** — Registre présences, chronologie décisionnelle
- **Kanban** — Tableau opérationnel, drag & drop
- **REX** — Retour d'expérience structuré, export DOCX
- **Relève** — Consignes horodatées, accusé de réception
- **Annuaire** — Contacts nominaux et secours, bascule téléphonie
- **COMMUNIQUÉ** — Statut public par site, push vers collecteur territorial
- **Supervision territoriale** — Collecteur multi-établissements, carte GPS, statuts publics
- **Internationalisation** — 8 langues européennes (fr, en, de, es, it, nl, pl, pt)

---

## Installation rapide

### 1. SCRIBE (établissement)

```bash
cd scribe/
pip install -r requirements.txt
cp config_demo1.xml config.xml
python setup.py
python main.py
# → http://localhost:8000
```

**Démos :** `setup_demo1.py` → CHV Valmont (5 sites) · `setup_demo2.py` → CSBM Montrelay (4 sites)

### 2. Collecteur territorial

```bash
cd collecteur/
pip install -r collecteur_requirements.txt
python collecteur.py
# → http://localhost:9000
```

---

## Configuration (`config.xml`)

```xml
<scribe>
  <etablissement>
    <nom>Mon Établissement</nom>
    <sigle>MES</sigle>
  </etablissement>
  <admin>
    <login>dircrise</login>
    <password>MonMotDePasse!</password>
  </admin>
  <!-- Langue : fr en de es it nl pl pt -->
  <langue>fr</langue>
  <sites>
    <site>
      <nom>Site Principal</nom>
      <adresse>1 rue de la Santé, 75000 Paris</adresse>
      <latitude>48.8566</latitude>
      <longitude>2.3522</longitude>
    </site>
  </sites>
  <ia>
    <fournisseur>albert</fournisseur>
    <cle_api>sk-...</cle_api>
    <modele>mistralai/Ministral-3-8B-Instruct-2512</modele>
    <url_base>https://albert.api.etalab.gouv.fr/v1/chat/completions</url_base>
  </ia>
  <federation>
    <enabled>true</enabled>
    <collecteur_url>http://IP-COLLECTEUR:9000/api/push</collecteur_url>
    <token>CHOISIR_16_CARACTERES_MIN</token>
    <intervalle_secondes>30</intervalle_secondes>
    <share_details>true</share_details>
    <share_min_urgency>1</share_min_urgency>
  </federation>
</scribe>
```

---

## Fournisseurs IA

| Fournisseur | Config | Notes |
|---|---|---|
| Albert (DINUM) | `albert` | Recommandé ES publics français |
| Ollama | `ollama` | Local, http://localhost:11434 |
| OpenAI | `openai` | GPT-4 |
| Anthropic | `anthropic` | Claude |
| Mistral | `mistral` | https://api.mistral.ai |
| Gemini | `gemini` | Google |
| Compatible OpenAI | `openai_compat` | LM Studio, vLLM, Jan |

---

## Fédération territoriale

### ⚠️ Deux tokens — règle absolue

| Token | Rôle | Emplacement |
|---|---|---|
| **Token admin collecteur** | Administrer le collecteur | `-H "Authorization: Bearer ..."` curl uniquement |
| **Token établissement** | Authentifier les pushs | `config.xml <federation><token>` ET `-d '{"token":"..."}'` curl |

**Ces deux tokens ne doivent jamais être identiques.**

```bash
# Générer un token établissement
python3 -c "import secrets; print(secrets.token_hex(16))"

# Enregistrer l'établissement dans le collecteur
curl -X POST http://IP-COLLECTEUR:9000/api/admin/tokens \
  -H "Authorization: Bearer TOKEN_ADMIN_COLLECTEUR" \
  -H "Content-Type: application/json" \
  -d '{"sigle":"MES","token":"votre_token_etablissement"}'
```

### Séquence de démarrage

1. Démarrer le collecteur **en premier**
2. Configurer `<federation>` dans chaque `config.xml`
3. `python setup.py` + `python main.py` sur chaque SCRIBE
4. Enregistrer chaque établissement (curl ci-dessus)
5. Vérifier dans les logs : `push_status OK`

---

## Changelog

### v1.1.0
- Internationalisation — 8 langues européennes
- Marqueurs GPS distincts par site dans le collecteur
- Statuts publics par site (COMMUNIQUÉ multi-sites)
- Supervision collecteur : sites en sous-entités
- Correctif : référence circulaire dans le push fédération
- Correctif : scroll supervision collecteur
- Boutons RESANA et LA SUITE dans le header
- SITE_MAPPING `import_uf2.py` corrigé

### v1.0.0 (RC)
- Main courante complète (8 onglets)
- Collecteur territorial multi-établissements
- Module COMMUNIQUÉ / statut public
- IA Albert + 6 fournisseurs
- Export DOCX rapport / REX

---

## Licence

MIT — Centre Hospitalier Annecy-Genevois (CHAG) — RSSI

---
---

# SCRIBE — Hospital Crisis Management Platform

> **Version française ci-dessus**

---

**SCRIBE** is an open-source crisis management logbook for healthcare facilities.  
Runs on an **isolated network** — no Internet, no LDAP, no cloud dependency.  
MIT License — Repository: https://github.com/nocomp/scribe

---

## Screenshots

| Watch & Incidents | Care Map |
|---|---|
| ![Watch](screenshots/acc.png) | ![Care](screenshots/soin.png) |

| Crisis Cell | Kanban |
|---|---|
| ![Cell](screenshots/celulle.png) | ![Kanban](screenshots/kaban.png) |

| AAR | Handover |
|---|---|
| ![AAR](screenshots/rex.png) | ![Handover](screenshots/releve.png) |

| Directory | Collector — Supervision |
|---|---|
| ![Directory](screenshots/annuaire.png) | ![Collector](screenshots/collecteur_supervision.png) |

| Collector — Public Status | Collector — Map |
|---|---|
| ![Status](screenshots/collecteur_statuts.png) | ![Map](screenshots/collecteur_carto.png) |

---

## Features

- **Watch & Incidents** — Declaration, tracking, milestones, integrated AI
- **Care** — Clinical department map, return-to-normal projection
- **Crisis Cell** — Attendance register, decision timeline
- **Kanban** — Operational dashboard, drag & drop
- **AAR** — After-action review, DOCX export
- **Handover** — Timestamped notes, acknowledgement receipts
- **Directory** — Nominal and backup contacts, telephony toggle
- **Bulletin** — Public status per site, push to territorial collector
- **Territorial Supervision** — Multi-facility collector, GPS map, public statuses
- **Internationalisation** — 8 European languages (fr, en, de, es, it, nl, pl, pt)

---

## Quick Start

### 1. SCRIBE (facility)

```bash
cd scribe/
pip install -r requirements.txt
cp config_demo1.xml config.xml
python setup.py
python main.py
# → http://localhost:8000
```

**Demos:** `setup_demo1.py` → CHV Valmont (5 sites) · `setup_demo2.py` → CSBM Montrelay (4 sites)

### 2. Territorial Collector

```bash
cd collecteur/
pip install -r collecteur_requirements.txt
python collecteur.py
# → http://localhost:9000
```

---

## Configuration (`config.xml`)

```xml
<scribe>
  <etablissement>
    <nom>My Hospital</nom>
    <sigle>MYH</sigle>
  </etablissement>
  <admin>
    <login>crisisdir</login>
    <password>ChangeThisPassword!</password>
  </admin>
  <!-- Language: fr en de es it nl pl pt -->
  <langue>en</langue>
  <sites>
    <site>
      <nom>Main Site</nom>
      <adresse>1 Health Street, 75000 Paris</adresse>
      <latitude>48.8566</latitude>
      <longitude>2.3522</longitude>
    </site>
  </sites>
  <ia>
    <fournisseur>albert</fournisseur>
    <cle_api>sk-...</cle_api>
    <modele>mistralai/Ministral-3-8B-Instruct-2512</modele>
    <url_base>https://albert.api.etalab.gouv.fr/v1/chat/completions</url_base>
  </ia>
  <federation>
    <enabled>true</enabled>
    <collecteur_url>http://COLLECTOR-IP:9000/api/push</collecteur_url>
    <token>CHOOSE_16_CHARS_MIN</token>
    <intervalle_secondes>30</intervalle_secondes>
    <share_details>true</share_details>
    <share_min_urgency>1</share_min_urgency>
  </federation>
</scribe>
```

---

## Supported AI Providers

| Provider | Config | Notes |
|---|---|---|
| Albert (DINUM) | `albert` | Recommended for French public facilities |
| Ollama | `ollama` | Local, http://localhost:11434 |
| OpenAI | `openai` | GPT-4 |
| Anthropic | `anthropic` | Claude |
| Mistral | `mistral` | https://api.mistral.ai |
| Gemini | `gemini` | Google |
| OpenAI-compatible | `openai_compat` | LM Studio, vLLM, Jan |

---

## Territorial Federation

### ⚠️ Two tokens — absolute rule

| Token | Role | Where |
|---|---|---|
| **Collector admin token** | Administer the collector | `-H "Authorization: Bearer ..."` curl only |
| **Facility token** | Authenticate SCRIBE pushes | `config.xml <federation><token>` AND `-d '{"token":"..."}'` curl |

**These two tokens must never be identical.**

```bash
# Generate a facility token
python3 -c "import secrets; print(secrets.token_hex(16))"

# Register a facility with the collector
curl -X POST http://COLLECTOR-IP:9000/api/admin/tokens \
  -H "Authorization: Bearer COLLECTOR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sigle":"MYH","token":"your_facility_token"}'
```

### Startup sequence

1. Start the collector **first**
2. Configure `<federation>` in each facility's `config.xml`
3. Run `python setup.py` + `python main.py` on each SCRIBE
4. Register each facility (curl above)
5. Check logs for: `push_status OK`

---

## Changelog

### v1.1.0
- Internationalisation — 8 European languages
- Collector map: distinct GPS markers per site
- Public status per individual site (multi-site Bulletin)
- Collector supervision: sites as sub-entities
- Fix: circular reference in federation push payload
- Fix: collector supervision scroll
- RESANA and LA SUITE buttons in header
- `import_uf2.py`: CHAG SITE_MAPPING fixed

### v1.0.0 (RC)
- Full crisis logbook (8 tabs)
- Multi-facility territorial collector
- Bulletin / public status module
- Albert AI + 6 other providers
- DOCX closure report / AAR export

---

## Licence

MIT — Centre Hospitalier Annecy-Genevois (CHAG)
