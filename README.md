<div align="center">

```
███████╗ ██████╗██████╗ ██╗██████╗ ███████╗
██╔════╝██╔════╝██╔══██╗██║██╔══██╗██╔════╝
███████╗██║     ██████╔╝██║██████╔╝█████╗
╚════██║██║     ██╔══██╗██║██╔══██╗██╔══╝
███████║╚██████╗██║  ██║██║██████╔╝███████╗
╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═════╝ ╚══════╝
```

# 🏥 SCRIBE — Hospital Crisis Management Log

[![Version](https://img.shields.io/badge/version-1.3.0-blue)](https://github.com/nocomp/scribe)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Stack](https://img.shields.io/badge/stack-Python%20%7C%20FastAPI%20%7C%20SQLite-orange)](https://github.com/nocomp/scribe)
[![Languages](https://img.shields.io/badge/languages-EN%20FR-blueviolet)](README_FR.MD)

</div>

> 📋 **Real-time incident logging, capacity management, and crisis coordination** — offline first, designed for healthcare

---

## 🌍 Languages
**[English](#overview)** | **[🇫🇷 Français](README_FR.MD)**

---

## 📖 Overview

SCRIBE is an open-source crisis management and bed-capacity coordination application originally developed by the CISOs and crisis teams at CHAG. It provides:

| Feature | Description |
|---------|-------------|
| 📋 **Incident Log** | sitrep with milestones, attachments, timeline |
| 🛏️ **Capacity Dashboard** | bed/RH/material management per clinical unit |
| 🏛️ **Crisis Room** | presence register, decisions, Kanban |
| 🌐 **Territorial Collector** | multi-site data aggregation & supervision |
| 🤖 **AI Analysis** | configurable providers (Albert, OpenAI, Anthropic, etc.) |

---

## 💡 Design Principles

✅ **Offline first** — no mandatory cloud, works on-premise  
✅ **Non-technical users** — simple UI for nurses, managers, crisis directors  
✅ **Lightweight** — Python + FastAPI + SQLite

---

## 🚀 Quick Start

### Docker Compose (recommended)

```powershell
git clone https://github.com/nocomp/scribe.git
cd scribe
docker compose up -d
# Open http://localhost:8000 (demo: dircrise / Scribe2026!)
```

#### 🌐 Local Network (LAN) Access

To access SCRIBE from remote computers on the same hospital network:

1. **Find your server's IP address:**
   ```powershell
   ipconfig /all
   # Look for IPv4 Address (e.g., 192.168.1.50 or 10.0.0.50)
   ```

2. **Create or update `.env` file:**
   ```bash
   SCRIBE_HOST=192.168.1.50
   # Or use hostname if DNS is configured:
   # SCRIBE_HOST=scribe.hospital.local
   ```

3. **Update CORS for remote access:**
   ```bash
   CORS_ORIGINS=http://192.168.1.50,http://192.168.1.50:80,https://192.168.1.50:443,http://localhost
   ```

4. **Restart containers:**
   ```powershell
   docker compose up -d
   ```

5. **Access from remote computer:**
   - From same LAN: `http://192.168.1.50`
   - From another network (VPN): Configure firewall & reverse proxy rules

**Note:** In production with HTTPS/TLS, use valid certificates (not self-signed) to avoid browser warnings.

### Local development (no Docker)

```powershell
pip install -r scribe/requirements.txt
python scribe/setup_demo1.py
python scribe/seed_demo_crise.py
python scribe/main.py
# Open http://localhost:8000
```

---

## ✨ Main Features

| Feature | Details |
|---------|---------|
| 📊 **Incident Management** | Create incidents, track milestones, attach files, mark statuses |
| 📈 **Capacity Dashboard** | Three daily reports per unit, bed counts (M/F/Mixed), tension levels |
| 🏢 **Crisis Room** | Timestamped attendance, decision timeline, after-action review (REX) |
| 🎯 **Kanban Board** | Drag & drop tasks, priorities, assignees, due dates |
| 📄 **Exports** | Public status page, archive exports (ZIP/DOCX) |
| 🤖 **Multi-Provider AI** | Albert (DINUM), OpenAI, Anthropic, Gemini, Mistral, Ollama, local

---

## 🏗️ Architecture

```
scribe/
├─ scribe/                    # Main application (FastAPI)
│  ├─ app/static/             # Frontend (single-page app)
│  ├─ app/lang/               # Translations (JSON)
│  ├─ app/api/                # Server API endpoints
│  └─ requirements.txt         # Python dependencies
└─ collecteur/                # Territorial collector (FastAPI)
   ├─ collecteur.py           # Aggregator service
   └─ collecteur_requirements.txt
```

---

## ⚙️ Configuration
Primary configuration is `config.xml` located inside `scribe/`. It contains:
- Site metadata (name, FINESS code, geographic coordinates)
- Admin credentials (used for first-run initialization)
- Default language (i18n)
- AI provider settings

For Docker deployments, mount your custom `config.xml` into `/data/config.xml` or persist the generated `config.js` in `/data` volume.

---

## 🌐 Internationalization (i18n)
Translations live in `scribe/app/lang/` as JSON files named by language code (e.g., `en.json`, `fr.json`).

**To add or edit a language:**
1. Edit `scribe/app/lang/<code>.json`
2. Update the `_meta` block (`code`, `name`, `flag`, `direction`)
3. Restart the service to flush the in-memory cache
4. Inspect via `/api/v1/i18n/<code>` API endpoint

---

## 📦 Collector (Territorial Aggregator)
The `collecteur` service aggregates data from multiple SCRIBE instances and exposes a read-only supervision UI (default port `9000`).

**Push routes:**
- `/api/push` — crisis state (incidents & KPIs) → CERT Santé
- `/api/push-capacite` — capacity state (beds & resources) → ARS/GHT

---

## 🎬 Demo Scenario
`seed_demo_crise.py` seeds a realistic ransomware scenario for testing and demos: multiple incidents, decisions, tasks, and handovers.

---

## 📋 Compliance & Regulations
- ✅ **NIS2** — decision traceability, CERT Santé milestones, timeline
- ✅ **Plan Blanc** — cell activation, attendance register, communications
- ✅ **ORSAN** — regulatory basis for crisis decisions
- ✅ **HDS/RGPD** — local deployment, zero mandatory cloud

---

## 🐳 Docker Deployment (Production)
### Environment Setup

Create a `.env` file next to `docker-compose.yml` with your production secrets:

```bash
# SCRIBE application
SCRIBE_SECRET=ReplaceWithAStrongRandomValue_32chars_or_more
ADMIN_PASSWORD=ChangeThisAdminPass!
CORS_ORIGINS=https://your.domain.example
LOG_LEVEL=info

# AI provider (optional)
SCRIBE_IA_PROVIDER=albert
SCRIBE_IA_KEY=
SCRIBE_IA_MODEL=
SCRIBE_IA_URL=

# Database (optional — use PostgreSQL for production)
# DATABASE_URL=postgresql://user:password@db:5432/scribe
```

### Start the Stack

```powershell
docker compose pull
docker compose up -d --remove-orphans
docker compose logs -f
```

### ⚠️ Important Notes

| Item | Note |
|------|------|
| **SCRIBE_SECRET** | Signs JWTs — keep secret, rotate regularly |
| **Database** | Use PostgreSQL in production instead of SQLite |
| **.env file** | Never commit to git — add to `.gitignore` |
| **Local build** | Uncomment `build:` in `docker-compose.yml` for local code |
| **TLS/Traefik** | Configure proper certificates and reverse proxy |

---

## 💻 Contributing
- Run tests and keep changes focused
- Use `python -m py_compile` to check syntax before committing
- Keep PRs clear and concise

---

## 📄 License

MIT — Open source, free for use and modification

---

## 📞 Support & Contact

For questions, issues, or contributions, open an issue on [GitHub](https://github.com/nocomp/scribe) or contact the maintainers.

---

<div align="center">

**Made with ❤️ for healthcare crisis management**

</div>

#### Variables d'environnement Docker

| Variable | Défaut | Description |
|---|---|---|
| `SCRIBE_IA_PROVIDER` | `albert` | Fournisseur IA (surpasse config.xml) |
| `SCRIBE_IA_KEY` | — | Clé API IA |
| `SCRIBE_IA_MODEL` | — | Modèle IA |
| `SCRIBE_IA_URL` | — | URL base IA (Ollama, LM Studio…) |
| `SCRIBE_PORT` | `8000` | Port d'écoute |
| `LOG_LEVEL` | `info` | Niveau de log uvicorn |

#### Données persistantes

Le volume Docker `scribe_data` contient :
- `/data/db/scribe.db` — base SQLite
- `/data/uploads/` — pièces jointes incidents
- `/data/config.js` — configuration frontend
- `/data/config.xml` — (optionnel) config montée en volume

#### Collecteur territorial Docker

```bash
cd scribe/collecteur
docker compose up -d
# → http://localhost:9000
```

---

**Production deployment — recommended env & .env template**

Use environment variables to keep secrets out of source control. Below are recommended variables for production; set them in a `.env` file placed next to `docker-compose.yml` or inject them into your orchestrator.

`.env` template (copy to `.env` and update values):

```
# SCRIBE application
SCRIBE_SECRET=ReplaceWithAStrongRandomValue_32chars_or_more
ADMIN_PASSWORD=ChangeThisAdminPass!
CORS_ORIGINS=https://your.domain.example,https://admin.your.domain.example
LOG_LEVEL=info

# IA provider (optional)
SCRIBE_IA_PROVIDER=albert
SCRIBE_IA_KEY=
SCRIBE_IA_MODEL=
SCRIBE_IA_URL=

# Optional: use external DB (example PostgreSQL URL)
# DATABASE_URL=postgresql://user:password@db:5432/scribe

# Traefik / TLS (example: enable LetsEncrypt resolver name)
# TRAEFIK_HOST=your.domain.example
```

Start in production (recommendation):

```powershell
cd 'C:\Users\SALACH\Documents\AzureDevOps\SOC4HEALTH\scribe'
# ensure .env exists and contains the variables above
docker compose pull
docker compose up -d --remove-orphans
docker compose logs -f
```

Notes:
- `SCRIBE_SECRET` must be a long, unpredictable secret used to sign JWTs.
- Prefer mounting an external database (`DATABASE_URL`) for production instead of SQLite.
- Keep `ADMIN_PASSWORD` secret (rotate periodically) and avoid committing `.env` to git.
- If you run the local source (build from `./scribe`), use `docker compose build --no-cache` then `docker compose up -d`.


# Enregistrer un établissement
curl -X POST http://localhost:9000/api/admin/tokens \
  -H "Authorization: Bearer TOKEN_ADMIN" \
  -H "Content-Type: application/json" \
  -d '{"sigle":"MON_CH","token":"TOKEN_ETABLISSEMENT"}'
```

### Déploiement production (Linux systemd)

```ini
[Unit]
Description=SCRIBE Crisis Management
After=network.target

[Service]
User=scribe
WorkingDirectory=/opt/scribe
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## EN SCRIBE — Hospital Crisis Management Log

SCRIBE is an open-source **hospital crisis management and bed capacity monitoring platform** developed by the CISO of Centre Hospitalier Annecy-Genevois (CHAG). It provides a complete digital crisis log, real-time capacity tracking, a multi-facility territorial collector, and an AI-powered post-crisis debriefing module.

**Dual use** — SCRIBE is designed to be useful **both in normal operations and during crises**:
- **Normal mode**: daily capacity tracking (beds, staff, equipment), 3 declarations/day by nurse managers, dashboard for nursing directors and HR
- **Crisis mode**: incident log, crisis room, operational kanban, public bulletins, territorial GHT/ARS coordination

**Designed for non-technical staff** — nurse managers, directors, crisis coordinators — SCRIBE requires no cloud, no LDAP, and runs fully offline on an isolated network.

---

### One-liner start with Docker Compose
- Update config.xml so that it reflects your hospital details
- Run ```sudo docker compose up -d ```

BEWARE: Certificate is self signed and Traeffik management interface is published on port 8080. Change this before production.

### Quick Start

#### Docker (quick start)

```bash
git clone https://github.com/nocomp/scribe
cd scribe/scribe
docker compose up -d
# → http://localhost:8000   login: dircrise / Scribe2026!
```

With custom config:
```bash
# Mount your config.xml
docker compose up -d  # edit docker-compose.yml to uncomment the config.xml volume
```

For the territorial collector:
```bash
cd scribe/collecteur && docker compose up -d
# → http://localhost:9000
```


```powershell
# Windows — double-click SETUP.bat or from PowerShell:
.\SETUP.bat
# Choose [1] for the demo with pre-filled ransomware scenario
```

```bash
# Linux
pip install -r requirements.txt
python setup_demo1.py && python seed_demo_crise.py
python main.py
# → http://localhost:8000  (login: dircrise / Scribe2026!)
```

---

### Features v1.3.0

#### 🌐 WATCH — Incident Log
- Incident declaration: CYBER / HEALTH / MIXED, levels 1 (WATCH) to 4 (CRITICAL)
- Predefined resolution milestones + custom milestones
- AI analysis (Albert DINUM), global situation analysis
- Interactive timeline with return-to-normal projection
- CSV export, complete activity log export (all modules)

#### 🏥 CARE — Capacity Mapping
- 14 clinical department cards with automatic status coloring
- Color driven by open incidents (UF code or keyword matching in incident text)
- **Capacity color override**: nurse manager alert in CAPACITY tab immediately colors the pole in CARE
- Albert capacity analysis
- Transverse services status (Physical Security, Logistics)

#### 🏛️ CELL — Crisis Room
- Timestamped attendance register (entry/exit, name, role)
- Decision log with regulatory basis (White Plan, NIS2, ORSAN)

#### 📋 KANBAN — Operational Board
- 4 columns: BACKLOG / IN PROGRESS / WAITING / DONE
- Drag & drop, priorities, assignees, due dates, incident links

#### 📊 REX — Experience Feedback
- Plain-language form, Albert auto-fill, DOCX export

#### 🔄 HANDOVER — Shift Handover
- Timestamped log, **named acknowledgement** (first name + timestamp)

#### 📞 DIRECTORY — Crisis Directory
- Standard and emergency contacts, automatic telephone failover

#### 📢 BULLETIN — Public Status
- Multi-site independent management
- Levels: OPERATIONAL / DISRUPTED / DEGRADED / ALERT / CRITICAL
- Public page `/status?site_id=N` without authentication

#### 🛏️ CAPACITY — Bed Capacity Management *(new v1.3.0)*

**Normal operations use**:
- Nurse managers declare their service status 3×/day (morning, afternoon, evening/handover)
- Quick form (< 2 min): available beds M/F/N, HR status, equipment status, comment
- Real-time dashboard for nursing directors and HR managers
- Full history for REX and trend graphs

**Crisis use**:
- Alert threshold declared by nurse manager → **automatic incident creation in WATCH**
- Immediate visual impact on department cards in CARE tab
- Silence alerts if service hasn't declared in > 6h
- Push to territorial collector GHT/ARS (route `/api/push-capacite`)

**CHAG specifics**:
- 58 units pre-loaded from BedManager (ANNECY: MEDICINE, SURGERY, ICU/EMERGENCY, PALLIATIVE, FME, PSYCH + SAINT-JULIEN + RUMILLY + LTCU/NURSING HOME)
- M/F/N bed management per unit: male room cannot accommodate female patients in mixed units
- **Albert CAPACITY**: AI analysis of global capacity situation with 4 quick questions + free field

#### 🔬 ANALYSIS — Crisis Debrief
- ZIP archive upload by drag-and-drop (embedded JSZip — 100% offline)
- **8 automatic metrics** + interactive timeline of all activities including **capacity declarations**
- Comparison mode: two archives side by side
- Albert Analysis with 6 quick questions + free question
- DOCX report export

#### 📦 End-of-Crisis Management
- **ARCHIVE button**: creates timestamped ZIP (incidents, decisions, attendance, handover, kanban, REX, bulletins, **capacity declarations**, public timeline)
- **NEW button**: resets dashboard (double confirmation)

---

### Regulatory Compliance

| Framework | Coverage |
|---|---|
| **NIS2** | Decision traceability, CERT Santé milestones, timeline |
| **White Plan** | Cell activation, attendance register, communications |
| **CERT Santé** | Dedicated milestone, integrated reporting |
| **HDS / GDPR** | Local deployment, zero mandatory cloud |
| **ORSAN** | Regulatory basis for decisions |

---

### AI — 7 supported providers

| Provider | Config | Notes |
|---|---|---|
| **Albert (DINUM)** | `albert` | ✅ Recommended for French public health — sovereign |
| **Ollama** | `ollama` | 100% local, fully offline |
| OpenAI | `openai` | GPT-4 |
| Anthropic | `anthropic` | Claude |
| Mistral | `mistral` | api.mistral.ai |
| Gemini | `gemini` | Google |
| OpenAI-compatible | `openai_compat` | LM Studio, vLLM, Jan |

---

## Changelog

### v1.3.0 (current — March 2026)
- **NEW: CAPACITY tab** — bed capacity management with nurse manager declarations (M/F/N beds, HR, equipment), alert thresholds, automatic incident creation, dashboard for nursing directors
- **NEW: Albert CAPACITY** — AI analysis of capacity situation with pre-formed questions
- **NEW: Territorial collector capacity route** — `/api/push-capacite` for ARS/GHT dashboard
- **NEW: `sync_crise` / `sync_sanitaire` config flags** — separate pushes for CERT Santé vs ARS
- Fix: CARE tab coloring — `uf-to-pole` mapping now uses keyword matching first, FICOM pole as fallback (fixes "Total CARDIOVASCULAIRE" misclassification)
- Fix: CARE tab real-time update on new incident (refreshAll now calls renderSoins)
- Fix: Capacity declarations included in main courante export and crisis archive ZIP
- Interactive `SETUP.bat` for Windows (demo / custom config menu)
- PR #4 Elched (SOC-HCL): Docker ai_router.py fix

### v1.2.0
- ANALYSIS tab: offline ZIP debrief, 8 metrics, interactive timeline, comparison mode, Albert analysis, DOCX export
- ARCHIVE / NEW buttons separated
- JSZip 3.10.1 embedded inline (offline)
- Debug console for ANALYSIS tab

### v1.1.1
- Named acknowledgement in HANDOVER (first name + timestamp)
- Full activity log CSV export
- Collector login/password protection
- NEW CRISIS button: ZIP archive + dashboard reset

### v1.1.0
- Internationalisation: 8 European languages
- Collector: distinct GPS markers per geographic site

---

## Contributors

- [@nocomp](https://github.com/nocomp) — RSSI CHAG — project lead
- [@charles-chu-lyon](https://github.com/charles-chu-lyon) — CHU Lyon — PR #1 ai_router fix
- [@Elched](https://github.com/Elched) — SOC-HCL — PR #2-#4 Dockerfile, ai_router fix

---

## License

MIT — Free to use, modify and distribute.
Developed by and for French public healthcare facilities.

**Repository**: https://github.com/nocomp/scribe
**Version**: 1.3.0 — March 2026
