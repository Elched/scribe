"""
collecteur.py — Collecteur de supervision territoriale SCRIBE

Reçoit les pushs JSON des instances SCRIBE des établissements.
Interface web en lecture seule pour CERT Santé, ARS, supervision GHT.

Usage :
  python collecteur.py

Accès : http://localhost:9000
Admin : http://localhost:9000/admin  (pour gérer les tokens établissements)
"""

import hashlib
import json
import logging
import os
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("collecteur")

# ── Fichiers de persistance ───────────────────────────────────────────────
DATA_FILE   = os.environ.get("COLLECTEUR_DATA",   "collecteur_data.json")
TOKENS_FILE = os.environ.get("COLLECTEUR_TOKENS", "collecteur_tokens.json")
ADMIN_FILE  = os.environ.get("COLLECTEUR_ADMIN",  "collecteur_admin.json")

# Structure en mémoire
etablissements: dict = {}   # sigle → dernière remontée
tokens: dict = {}           # token → sigle établissement


def _load_or_create_admin_token() -> str:
    """Charge le token admin depuis le fichier, ou le crée une seule fois."""
    # Priorité 1 : variable d'environnement
    if os.environ.get("ADMIN_TOKEN"):
        return os.environ["ADMIN_TOKEN"]
    # Priorité 2 : fichier persistant
    p = Path(ADMIN_FILE)
    if p.exists():
        try:
            return json.loads(p.read_text()).get("admin_token", "")
        except Exception:
            pass
    # Première fois : générer et sauvegarder
    token = secrets.token_hex(32)
    p.write_text(json.dumps({"admin_token": token}, indent=2))
    return token


ADMIN_TOKEN = _load_or_create_admin_token()


def load_tokens():
    global tokens
    if Path(TOKENS_FILE).exists():
        try:
            tokens = json.loads(Path(TOKENS_FILE).read_text())
        except Exception:
            tokens = {}

def save_tokens():
    Path(TOKENS_FILE).write_text(json.dumps(tokens, ensure_ascii=False, indent=2))

def load_data():
    global etablissements
    if Path(DATA_FILE).exists():
        try:
            etablissements = json.loads(Path(DATA_FILE).read_text())
        except Exception:
            etablissements = {}

def save_data():
    Path(DATA_FILE).write_text(json.dumps(etablissements, ensure_ascii=False, indent=2))

# ── App FastAPI ───────────────────────────────────────────────────────────

app = FastAPI(title="SCRIBE Collecteur territorial", version="1.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

security = HTTPBearer(auto_error=False)


def get_etab_from_token(credentials: Optional[HTTPAuthorizationCredentials]) -> Optional[str]:
    if not credentials:
        return None
    return tokens.get(credentials.credentials)


def require_admin(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not credentials or credentials.credentials != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Token admin invalide")
    return True


# ── Endpoint de réception (appelé par les SCRIBE) ─────────────────────────

@app.post("/api/push")
async def receive_push(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Reçoit un push JSON d'un SCRIBE établissement."""
    sigle = get_etab_from_token(credentials)
    if not sigle:
        tok_short = credentials.credentials[:12] if credentials and credentials.credentials else "?"
        print(f"""
  TOKEN INCONNU - ENREGISTREMENT REQUIS
  IP source  : {request.client.host}
  Token recu : {tok_short}...

  Executez cette commande pour enregistrer l'etablissement :

  curl -X POST http://localhost:9000/api/admin/tokens \
    -H "Authorization: Bearer {ADMIN_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{{"sigle":"MON_ETAB","token":"TOKEN_QUE_VOUS_AVEZ_CHOISI"}}'

  TOKEN_QUE_VOUS_AVEZ_CHOISI = token choisi librement (16+ chars)
  Ce token doit etre identique dans config.xml <federation><token>
""")
        logger.warning("Push refusé — token inconnu depuis %s", request.client.host)
        raise HTTPException(status_code=401, detail="Token inconnu ou révoqué")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON invalide")

    # Enrichissement serveur
    payload["_received_at"] = datetime.now(timezone.utc).isoformat()
    payload["_source_ip"]   = request.client.host

    # Vérification cohérence sigle
    etab_sigle = payload.get("etablissement", {}).get("sigle", sigle)

    etablissements[sigle] = payload
    save_data()

    logger.info(f"Push reçu — {sigle} | niveau: {payload.get('niveau_global','?')} | "
                f"{payload.get('kpis',{}).get('incidents_ouverts',0)} incidents ouverts")
    return {"ok": True, "sigle": sigle, "received_at": payload["_received_at"]}


@app.post("/api/push-status")
async def receive_status_push(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Reçoit le push de la page de statut publique d'un établissement."""
    sigle = get_etab_from_token(credentials)
    if not sigle:
        raise HTTPException(status_code=401, detail="Token inconnu ou révoqué")
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON invalide")
    payload["_received_at"] = datetime.now(timezone.utc).isoformat()
    # Stocker le statut public : global + sites individuels
    if sigle in etablissements:
        etablissements[sigle]["_status_page"] = payload
        # Stocker les statuts par site s'ils existent
        if payload.get("_statuts_sites"):
            etablissements[sigle]["_statuts_sites"] = payload["_statuts_sites"]
    else:
        etablissements[sigle] = {
            "_status_page": payload,
            "_statuts_sites": payload.get("_statuts_sites", []),
            "_received_at": payload["_received_at"]
        }
    save_data()
    return {"ok": True, "sigle": sigle}


@app.get("/api/status/{sigle}")
async def get_etab_status(sigle: str):
    """Retourne la page de statut publique d'un établissement (si disponible)."""
    data = etablissements.get(sigle, {})
    sp = data.get("_status_page")
    if not sp:
        return {"published": False, "sigle": sigle}
    return sp


# ── API lecture (pour dashboard et intégrations tierces) ──────────────────

@app.get("/api/summary")
async def get_summary():
    """Vue consolidée de tous les établissements. Lecture seule, sans auth."""
    now = time.time()
    result = []
    for sigle, data in etablissements.items():
        # Fraîcheur de la donnée
        received_str = data.get("_received_at", "")
        try:
            received_ts = datetime.fromisoformat(received_str).timestamp()
            age_minutes = int((now - received_ts) / 60)
            fresh = age_minutes < 10
        except Exception:
            age_minutes = -1
            fresh = False

        result.append({
            "sigle":            sigle,
            "nom":              data.get("etablissement", {}).get("nom", sigle),
            "niveau_global":    data.get("niveau_global", "INCONNU"),
            "kpis":             data.get("kpis", {}),
            "services_transverses": data.get("services_transverses", {}),
            "poles_impactes":   data.get("poles_impactes", []),
            "incidents":        data.get("incidents", []),
            "last_update":      received_str,
            "age_minutes":      age_minutes,
            "fresh":            fresh,
            "_status_page":     data.get("_status_page"),
            "_statuts_sites":   data.get("_statuts_sites", []),
            "latitude":         data.get("latitude"),
            "longitude":        data.get("longitude"),
            "sites":            data.get("sites", []),
        })

    # Trier par niveau de gravité décroissant
    ORDRE = {"CRITIQUE": 4, "CRISE": 3, "ALERTE": 2, "VEILLE": 1, "NOMINAL": 0, "INCONNU": -1}
    result.sort(key=lambda x: ORDRE.get(x["niveau_global"], -1), reverse=True)
    return result


@app.get("/api/etablissement/{sigle}")
async def get_etablissement(sigle: str):
    """Détail d'un établissement."""
    if sigle not in etablissements:
        raise HTTPException(status_code=404, detail=f"Établissement {sigle} inconnu")
    return etablissements[sigle]


# ── Admin (gestion des tokens) ─────────────────────────────────────────────

@app.get("/api/admin/tokens", dependencies=[Depends(require_admin)])
async def list_tokens():
    return [{"sigle": v, "token_preview": k[:8] + "..."} for k, v in tokens.items()]


@app.post("/api/admin/tokens", dependencies=[Depends(require_admin)])
async def create_token(body: dict):
    """Crée un token pour un nouvel établissement.
    body: {sigle, nom, token (optionnel)}
    Si token est fourni, il est utilisé tel quel — utile pour synchroniser avec config.xml."""
    sigle = body.get("sigle", "").strip().upper()
    if not sigle:
        raise HTTPException(status_code=400, detail="sigle requis")
    token = body.get("token", "").strip() or secrets.token_hex(32)
    if len(token) < 16:
        raise HTTPException(status_code=400, detail="token trop court (min 16 caractères)")
    tokens[token] = sigle
    save_tokens()
    logger.info(f"Token {'importé' if body.get('token') else 'généré'} pour {sigle}")
    return {"sigle": sigle, "token": token, "message": "Token enregistré pour " + sigle}


@app.delete("/api/admin/tokens/{token_prefix}", dependencies=[Depends(require_admin)])
async def revoke_token(token_prefix: str):
    """Révoque un token par ses 8 premiers caractères."""
    to_delete = [k for k in tokens if k.startswith(token_prefix)]
    if not to_delete:
        raise HTTPException(status_code=404, detail="Token non trouvé")
    for k in to_delete:
        sigle = tokens.pop(k)
        logger.info(f"Token révoqué pour {sigle}")
    save_tokens()
    return {"ok": True, "revoked": len(to_delete)}


# ── Interface web (dashboard lecture seule) ────────────────────────────────

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SCRIBE — Supervision Territoriale</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow+Condensed:wght@300;400;600;700;900&family=Barlow:wght@300;400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
:root {
  --bg:      #060608;
  --s1:      #0d0d12;
  --s2:      #111118;
  --s3:      #18181f;
  --border:  #1f1f2e;
  --border2: #2a2a3d;
  --text:    #dde4f0;
  --muted:   #4a5070;
  --muted2:  #6b7494;
  --mono:    'Share Tech Mono', monospace;
  --head:    'Barlow Condensed', sans-serif;
  --body:    'Barlow', sans-serif;
  --green:   #00e5a0;
  --yellow:  #f5c518;
  --orange:  #ff7b2c;
  --red:     #ff2d55;
  --blue:    #3d9eff;
  --purple:  #a855f7;
  --cyan:    #00cfff;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:var(--body);overflow:hidden}

/* ── SCANLINE OVERLAY ── */
body::before{
  content:'';
  content:'';position:fixed;inset:0;pointer-events:none;z-index:9999;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.03) 2px,rgba(0,0,0,.03) 4px);
}

/* ── LAYOUT ── */
#app{display:flex;flex-direction:column;height:100vh}

/* ── HEADER ── */
#header{
  display:flex;align-items:center;gap:0;
  background:var(--s1);border-bottom:1px solid var(--border2);
  height:52px;flex-shrink:0;position:relative;overflow:hidden;
}
#header::after{
  content:'';position:absolute;bottom:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,var(--cyan),var(--blue),transparent);
  animation:scanH 4s linear infinite;
}
@keyframes scanH{from{transform:translateX(-100%)}to{transform:translateX(100%)}}

.h-logo{
  padding:0 20px;border-right:1px solid var(--border2);height:100%;
  display:flex;align-items:center;gap:10px;
}
.h-logo-text{font-family:var(--head);font-size:20px;font-weight:900;
  letter-spacing:4px;color:var(--text);text-transform:uppercase;}
.h-logo-sub{font-family:var(--mono);font-size:8px;color:var(--muted2);letter-spacing:2px}

.h-tabs{display:flex;height:100%;margin-left:8px}
.h-tab{
  font-family:var(--head);font-size:12px;font-weight:600;letter-spacing:2px;
  text-transform:uppercase;padding:0 20px;cursor:pointer;
  border:none;background:transparent;color:var(--muted2);
  border-bottom:2px solid transparent;transition:all .2s;height:100%;
}
.h-tab:hover{color:var(--text);background:var(--s2)}
.h-tab.active{color:var(--cyan);border-bottom-color:var(--cyan);background:rgba(0,207,255,.04)}

.h-right{margin-left:auto;display:flex;align-items:center;gap:16px;padding:0 20px}
#clock{font-family:var(--mono);font-size:18px;color:var(--cyan);letter-spacing:2px}
#date-str{font-family:var(--mono);font-size:9px;color:var(--muted);letter-spacing:1px}
.h-level-pill{
  font-family:var(--head);font-size:11px;font-weight:700;letter-spacing:2px;
  padding:4px 14px;border-radius:2px;border:1px solid;
  animation:pulse-border 2s ease-in-out infinite;
}
@keyframes pulse-border{0%,100%{opacity:1}50%{opacity:.6}}
.level-CRITIQUE{color:var(--red);border-color:var(--red);background:rgba(255,45,85,.12)}
.level-CRISE{color:var(--orange);border-color:var(--orange);background:rgba(255,123,44,.12)}
.level-ALERTE{color:var(--yellow);border-color:var(--yellow);background:rgba(245,197,24,.12)}
.level-VEILLE{color:var(--blue);border-color:var(--blue);background:rgba(61,158,255,.12)}
.level-NOMINAL{color:var(--green);border-color:var(--green);background:rgba(0,229,160,.12)}
.level-INCONNU{color:var(--muted);border-color:var(--muted);background:rgba(74,80,112,.12)}

/* ── GLOBAL KPI BAR ── */
#kpi-bar{
  display:flex;align-items:stretch;
  background:var(--s1);border-bottom:1px solid var(--border);
  height:54px;flex-shrink:0;
}
.kpi-cell{
  display:flex;flex-direction:column;justify-content:center;align-items:center;
  padding:0 24px;border-right:1px solid var(--border);min-width:100px;
}
.kpi-val{font-family:var(--head);font-size:26px;font-weight:900;line-height:1}
.kpi-lbl{font-family:var(--mono);font-size:8px;color:var(--muted);letter-spacing:1px;margin-top:2px}
.kpi-cell.danger .kpi-val{color:var(--red)}
.kpi-cell.warn .kpi-val{color:var(--orange)}
.kpi-cell.ok .kpi-val{color:var(--green)}
.kpi-cell.info .kpi-val{color:var(--cyan)}
.kpi-cell.neutral .kpi-val{color:var(--text)}

#last-tick{
  margin-left:auto;padding:0 20px;display:flex;flex-direction:column;
  justify-content:center;align-items:flex-end;gap:2px;
}
.tick-dot{width:6px;height:6px;border-radius:50%;background:var(--green);
  animation:blink 1.5s ease-in-out infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
.tick-row{display:flex;align-items:center;gap:6px;font-family:var(--mono);font-size:9px;color:var(--muted)}

/* ── TABS CONTENT ── */
#tabs-content{flex:1;overflow:hidden;display:flex;flex-direction:column;min-height:0}
.tab-pane{display:none;flex:1;min-height:0;overflow:hidden}
.tab-pane.active{display:flex;min-height:0;overflow:hidden}

/* ══════════════════════════════════════════════
   TAB 1 — SUPERVISION
══════════════════════════════════════════════ */
#pane-supervision{flex-direction:row;gap:0;overflow:hidden;min-height:0}

/* Panel gauche : liste établissements */
#etab-list{
  width:300px;min-width:240px;border-right:1px solid var(--border);
  background:var(--s1);display:flex;flex-direction:column;overflow:hidden;flex-shrink:0;
}
#etab-list-header{
  padding:12px 14px 10px;border-bottom:1px solid var(--border);flex-shrink:0;
}
#etab-list-header h3{font-family:var(--head);font-size:11px;font-weight:700;
  letter-spacing:3px;color:var(--muted2);text-transform:uppercase}
#etab-scroll{flex:1;overflow-y:auto;min-height:0;height:0}
#etab-scroll::-webkit-scrollbar{width:4px}
#etab-scroll::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px}

.etab-row{
  display:flex;align-items:center;gap:10px;padding:11px 14px;
  border-bottom:1px solid var(--border);cursor:pointer;
  transition:background .15s;position:relative;
}
.etab-row:hover{background:var(--s2)}
.etab-row.selected{background:rgba(0,207,255,.05);border-left:2px solid var(--cyan)}
.etab-row.selected{padding-left:12px}
.etab-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.etab-dot.CRITIQUE{background:var(--red);box-shadow:0 0 6px var(--red)}
.etab-dot.CRISE{background:var(--orange);box-shadow:0 0 6px var(--orange)}
.etab-dot.ALERTE{background:var(--yellow);box-shadow:0 0 4px var(--yellow)}
.etab-dot.VEILLE{background:var(--blue)}
.etab-dot.NOMINAL{background:var(--green)}
.etab-dot.INCONNU{background:var(--muted)}
.etab-row-info{flex:1;min-width:0}
.etab-row-nom{font-family:var(--head);font-size:13px;font-weight:700;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.etab-row-sigle{font-family:var(--mono);font-size:9px;color:var(--muted2)}
.etab-row-right{display:flex;flex-direction:column;align-items:flex-end;gap:2px}
.etab-badge{font-family:var(--head);font-size:9px;font-weight:700;
  padding:1px 6px;border-radius:1px;letter-spacing:1px}
.etab-badge.CRITIQUE{color:var(--red);background:rgba(255,45,85,.15)}
.etab-badge.CRISE{color:var(--orange);background:rgba(255,123,44,.15)}
.etab-badge.ALERTE{color:var(--yellow);background:rgba(245,197,24,.15)}
.etab-badge.VEILLE{color:var(--blue);background:rgba(61,158,255,.15)}
.etab-badge.NOMINAL{color:var(--green);background:rgba(0,229,160,.15)}
.etab-badge.INCONNU{color:var(--muted);background:rgba(74,80,112,.15)}
.etab-age{font-family:var(--mono);font-size:8px;color:var(--muted)}
.etab-stale .etab-row-nom{opacity:.5}

/* Panel central : détail établissement */
#detail-panel{
  flex:1;overflow-y:auto;background:var(--bg);
  padding:16px 20px;display:flex;flex-direction:column;gap:12px;
  min-height:0;
}
#detail-panel::-webkit-scrollbar{width:4px}
#detail-panel::-webkit-scrollbar-thumb{background:var(--border2);border-radius:2px}

.detail-empty{
  flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;
  color:var(--muted);gap:10px;
}
.detail-empty-icon{font-size:36px;opacity:.3}
.detail-empty-txt{font-family:var(--mono);font-size:11px;letter-spacing:2px}

/* Header du detail */
.detail-header{
  display:flex;align-items:flex-start;justify-content:space-between;
  padding:16px 20px;background:var(--s1);border:1px solid var(--border2);border-radius:4px;
}
.detail-nom{font-family:var(--head);font-size:24px;font-weight:900;line-height:1}
.detail-sigle{font-family:var(--mono);font-size:10px;color:var(--muted2);margin-top:2px}
.detail-ts{font-family:var(--mono);font-size:9px;color:var(--muted);margin-top:6px}
.detail-level{
  font-family:var(--head);font-size:14px;font-weight:900;letter-spacing:2px;
  padding:6px 18px;border-radius:2px;border:1px solid;
}

/* KPIs detail */
.detail-kpis{display:flex;gap:10px;flex-wrap:wrap}
.dkpi{
  flex:1;min-width:80px;background:var(--s1);border:1px solid var(--border);
  border-radius:4px;padding:12px 14px;text-align:center;
}
.dkpi-val{font-family:var(--head);font-size:28px;font-weight:900}
.dkpi-lbl{font-family:var(--mono);font-size:8px;color:var(--muted);letter-spacing:1px;margin-top:2px}

/* Section card */
.detail-section{background:var(--s1);border:1px solid var(--border);border-radius:4px;overflow:visible}
.detail-section+.detail-section{margin-top:0}
.detail-section-header{
  padding:8px 14px;border-bottom:1px solid var(--border);
  font-family:var(--head);font-size:9px;font-weight:700;
  letter-spacing:2px;color:var(--muted2);text-transform:uppercase;
  display:flex;align-items:center;gap:8px;background:var(--s2);
}
.detail-section-body{padding:12px 14px;display:flex;flex-direction:column;gap:6px}

/* Services transverses */
.svc-chips{display:flex;gap:8px;flex-wrap:wrap;padding:12px 14px}
.svc-chip{
  display:flex;align-items:center;gap:6px;
  font-family:var(--mono);font-size:10px;padding:5px 10px;
  border-radius:2px;border:1px solid;
}
.svc-chip.OK{color:var(--green);border-color:rgba(0,229,160,.3);background:rgba(0,229,160,.06)}
.svc-chip.DEGRADE{color:var(--yellow);border-color:rgba(245,197,24,.3);background:rgba(245,197,24,.06)}
.svc-chip.CRITIQUE{color:var(--red);border-color:rgba(255,45,85,.3);background:rgba(255,45,85,.06)}
.svc-dot{width:5px;height:5px;border-radius:50%;background:currentColor}

/* Incidents list */
.inc-row{
  display:flex;flex-direction:column;gap:5px;
  padding:10px 0;border-top:1px solid var(--border);
  font-family:var(--mono);font-size:10px;
}
.inc-row:first-child{border-top:none;padding-top:0}
.inc-urg-badge{
  font-family:var(--head);font-size:10px;font-weight:700;
  padding:1px 6px;border-radius:1px;flex-shrink:0;
}
.inc-u4{color:var(--red);background:rgba(255,45,85,.15)}
.inc-u3{color:var(--orange);background:rgba(255,123,44,.15)}
.inc-u2{color:var(--yellow);background:rgba(245,197,24,.15)}
.inc-u1{color:var(--blue);background:rgba(61,158,255,.15)}
.inc-type{color:var(--purple);font-size:9px;flex-shrink:0;padding-top:2px}
.inc-fait{color:var(--text);flex:1;line-height:1.6;white-space:normal;word-break:break-word}
.inc-site{color:var(--muted);font-size:9px;flex-shrink:0}
.inc-status{font-size:9px;color:var(--muted2);flex-shrink:0}

/* Pôles impactés */
.poles-chips{display:flex;flex-wrap:wrap;gap:6px;padding:12px 14px}
.pole-chip{
  font-family:var(--mono);font-size:9px;padding:3px 8px;
  border:1px solid var(--border2);border-radius:2px;color:var(--muted2);
  background:var(--s2);
}

/* Sites sous-entités */
.sites-list{display:flex;flex-direction:column;gap:0}
.site-row{
  display:flex;align-items:center;gap:10px;
  padding:8px 14px;border-top:1px solid var(--border);
  font-family:var(--mono);font-size:10px;cursor:default;
  transition:background .15s;
}
.site-row:first-child{border-top:none}
.site-row:hover{background:var(--s2)}
.site-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.site-nom{flex:1;color:var(--text)}
.site-adresse{font-size:9px;color:var(--muted);flex:1}
.site-badge{
  font-family:var(--head);font-size:8px;font-weight:700;
  padding:2px 7px;border-radius:2px;flex-shrink:0;
}
.site-inc{font-size:9px;color:var(--muted);flex-shrink:0}

/* Panel droit : timeline incidents tous établissements */
#timeline-panel{
  width:320px;min-width:260px;border-left:1px solid var(--border);
  background:var(--s1);display:flex;flex-direction:column;overflow:hidden;flex-shrink:0;
}
#timeline-header{
  padding:12px 14px 10px;border-bottom:1px solid var(--border);flex-shrink:0;
  display:flex;align-items:center;justify-content:space-between;
}
#timeline-header h3{font-family:var(--head);font-size:11px;font-weight:700;
  letter-spacing:3px;color:var(--muted2);text-transform:uppercase}
#timeline-scroll{flex:1;overflow-y:auto;min-height:0;height:0;padding:10px 0}
#timeline-scroll::-webkit-scrollbar{width:3px}
#timeline-scroll::-webkit-scrollbar-thumb{background:var(--border2)}

.tl-etab-group{border-bottom:1px solid var(--border);margin-bottom:2px}
.tl-etab-header{display:flex;align-items:center;gap:6px;padding:8px 10px 4px;background:var(--surface2)}
.tl-site-group{border-left:2px solid var(--border2);margin:2px 10px 4px 16px}
.tl-item{
  display:flex;gap:10px;padding:8px 14px;border-bottom:1px solid var(--border);
  cursor:pointer;transition:background .15s;
}
.tl-item:hover{background:var(--s2)}
.tl-line{display:flex;flex-direction:column;align-items:center;gap:0;flex-shrink:0}
.tl-dot{width:8px;height:8px;border-radius:50%;margin-top:3px;flex-shrink:0}
.tl-stem{width:1px;flex:1;background:var(--border);margin:3px 0;min-height:20px}
.tl-item:last-child .tl-stem{display:none}
.tl-content{flex:1;min-width:0}
.tl-etab{font-family:var(--head);font-size:9px;font-weight:700;color:var(--muted2);letter-spacing:1px}
.tl-fait{font-family:var(--mono);font-size:10px;color:var(--text);line-height:1.4;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tl-meta{display:flex;gap:6px;margin-top:2px;font-family:var(--mono);font-size:8px;color:var(--muted)}
.tl-badge{font-family:var(--head);font-size:9px;font-weight:700;padding:1px 5px;border-radius:1px}

/* ══════════════════════════════════════════════
   TAB 2 — CARTOGRAPHIE
══════════════════════════════════════════════ */
#pane-carto{position:relative;overflow:hidden}
#map{width:100%;height:100%;background:#0a0f14}
.leaflet-container{background:#0a0f14}

/* Style carte dark */
.map-popup{
  background:var(--s2);border:1px solid var(--border2);border-radius:4px;
  font-family:var(--mono);padding:0;min-width:220px;
}
.map-popup-header{
  padding:8px 12px;border-bottom:1px solid var(--border);
  font-family:var(--head);font-size:13px;font-weight:700;
}
.map-popup-body{padding:8px 12px;font-size:10px;color:var(--muted2);line-height:1.8}
.leaflet-popup-content-wrapper{background:transparent;box-shadow:none;padding:0;border:none}
.leaflet-popup-content{margin:0}
.leaflet-popup-tip-container{display:none}

/* Légende carte */
#carto-legend{
  position:absolute;bottom:20px;left:20px;z-index:1000;
  background:rgba(13,13,18,.92);border:1px solid var(--border2);
  border-radius:4px;padding:12px 14px;backdrop-filter:blur(8px);
}
.legend-title{font-family:var(--head);font-size:10px;font-weight:700;
  letter-spacing:2px;color:var(--muted2);margin-bottom:8px}
.legend-row{display:flex;align-items:center;gap:8px;margin-bottom:4px;
  font-family:var(--mono);font-size:9px;color:var(--muted2)}
.legend-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}

/* ══════════════════════════════════════════════
   TAB 3 — AIDE À LA DÉCISION (ALBERT)
══════════════════════════════════════════════ */
#pane-albert{flex-direction:row;overflow:hidden}

#albert-left{
  width:340px;min-width:280px;background:var(--s1);
  border-right:1px solid var(--border);display:flex;flex-direction:column;overflow:hidden;
}
#albert-left-header{
  padding:14px 16px;border-bottom:1px solid var(--border);flex-shrink:0;
}
#albert-left-header h3{font-family:var(--head);font-size:11px;font-weight:700;
  letter-spacing:3px;color:var(--muted2);text-transform:uppercase;margin-bottom:8px}

.albert-form{display:flex;flex-direction:column;gap:10px}
.albert-form label{font-family:var(--mono);font-size:9px;color:var(--muted);letter-spacing:1px;text-transform:uppercase}
.albert-form select,.albert-form textarea,.albert-form input{
  background:var(--s2);border:1px solid var(--border2);color:var(--text);
  font-family:var(--mono);font-size:11px;padding:7px 10px;border-radius:3px;width:100%;
  outline:none;transition:border-color .2s;
}
.albert-form select:focus,.albert-form textarea:focus{border-color:var(--cyan)}
.albert-form textarea{resize:vertical;min-height:80px;line-height:1.5}

.btn-albert{
  font-family:var(--head);font-size:12px;font-weight:700;letter-spacing:2px;
  text-transform:uppercase;padding:10px 16px;border:none;border-radius:3px;
  cursor:pointer;transition:all .2s;
  background:linear-gradient(135deg,rgba(0,207,255,.15),rgba(61,158,255,.15));
  color:var(--cyan);border:1px solid rgba(0,207,255,.3);width:100%;
}
.btn-albert:hover{background:linear-gradient(135deg,rgba(0,207,255,.25),rgba(61,158,255,.25))}
.btn-albert:disabled{opacity:.4;cursor:not-allowed}

#albert-history{flex:1;overflow-y:auto;padding:10px}
#albert-history::-webkit-scrollbar{width:3px}
#albert-history::-webkit-scrollbar-thumb{background:var(--border2)}

.hist-item{
  background:var(--s2);border:1px solid var(--border);border-radius:4px;
  margin-bottom:8px;overflow:hidden;cursor:pointer;transition:border-color .2s;
}
.hist-item:hover{border-color:var(--border2)}
.hist-item.active{border-color:var(--cyan)}
.hist-header{padding:8px 10px;display:flex;justify-content:space-between;align-items:center}
.hist-ts{font-family:var(--mono);font-size:8px;color:var(--muted)}
.hist-ctx{font-family:var(--mono);font-size:9px;color:var(--muted2);
  padding:0 10px 8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}

/* Panel analyse albert */
#albert-right{
  flex:1;display:flex;flex-direction:column;overflow:hidden;background:var(--bg);
}
#albert-right-header{
  padding:14px 20px;border-bottom:1px solid var(--border);flex-shrink:0;
  display:flex;align-items:center;gap:12px;background:var(--s1);
}
#albert-right-header h3{font-family:var(--head);font-size:11px;font-weight:700;
  letter-spacing:3px;color:var(--muted2);text-transform:uppercase;flex:1}
#albert-niveau-badge{font-family:var(--head);font-size:11px;font-weight:700;
  letter-spacing:2px;padding:4px 14px;border-radius:2px;border:1px solid}
#albert-source{font-family:var(--mono);font-size:9px;color:var(--muted)}

#albert-output{
  flex:1;overflow-y:auto;padding:24px;
}
#albert-output::-webkit-scrollbar{width:4px}
#albert-output::-webkit-scrollbar-thumb{background:var(--border2)}

.albert-empty{
  height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;
  gap:12px;color:var(--muted);
}
.albert-empty-icon{font-size:40px;opacity:.2}
.albert-empty-txt{font-family:var(--mono);font-size:11px;letter-spacing:2px}

.albert-response{
  font-family:var(--mono);font-size:12px;line-height:1.9;color:var(--muted2);
  white-space:pre-wrap;
}
.albert-response .section-title{
  color:var(--cyan);font-family:var(--head);font-size:13px;font-weight:700;
  letter-spacing:2px;display:block;margin:18px 0 8px;
  border-bottom:1px solid rgba(0,207,255,.15);padding-bottom:4px;
}
.albert-response .section-title:first-child{margin-top:0}

/* ══ STATUTS PUBLICS ══ */
.status-card{background:var(--s1);border:1px solid var(--border);border-radius:4px;overflow:hidden}
.status-card-hdr{padding:10px 14px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}
.status-card-nom{font-family:var(--head);font-size:13px;font-weight:700}
.status-level-pill{font-family:var(--head);font-size:9px;font-weight:700;padding:2px 9px;border-radius:2px;border:1px solid;letter-spacing:1px}
.status-card-body{padding:10px 14px}
.status-msg{font-family:var(--mono);font-size:10px;color:var(--muted2);margin-bottom:8px;line-height:1.5}
.status-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-bottom:8px}
.status-svc{font-family:var(--mono);font-size:9px;display:flex;align-items:center;gap:5px;color:var(--muted2)}
.status-svc-dot{width:5px;height:5px;border-radius:50%}
.status-chron{font-family:var(--mono);font-size:9px;color:var(--muted2);border-top:1px solid var(--border);padding-top:8px;margin-top:2px}
.status-chron-item{display:flex;gap:8px;margin-bottom:3px}
.status-chron-ts{color:var(--muted);flex-shrink:0;min-width:40px}
.status-link{font-family:var(--mono);font-size:8px;color:var(--cyan);margin-top:6px;display:block}
.status-no-data{font-family:var(--mono);font-size:10px;color:var(--muted);padding:40px;text-align:center;grid-column:1/-1}

/* ══ STATUTS PUBLICS ══ */
#pane-statuts{flex:1;display:flex;flex-direction:column;overflow:hidden}
.sp-bar-row{background:var(--s1);border-bottom:1px solid var(--border);padding:9px 16px;font-size:9px;color:var(--muted);font-family:var(--mono);display:flex;align-items:center;gap:12px;flex-shrink:0}
.sp-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;padding:16px}
.sp-card{background:var(--s1);border:1px solid var(--border);border-radius:4px;overflow:hidden}
.sp-card-hdr{padding:10px 14px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:flex-start;gap:8px}
.sp-card-nom{font-family:var(--head);font-size:13px;font-weight:700}
.sp-card-sub{font-family:var(--mono);font-size:8px;color:var(--muted);margin-top:1px}
.sp-level{font-family:var(--head);font-size:9px;font-weight:700;padding:2px 9px;border-radius:2px;border:1px solid;letter-spacing:1px;white-space:nowrap}
.sp-body{padding:10px 14px}
.sp-msg{font-family:var(--mono);font-size:10px;color:var(--muted2);line-height:1.5;margin-bottom:8px}
.sp-services{display:grid;grid-template-columns:1fr 1fr;gap:3px;margin-bottom:8px}
.sp-svc{font-family:var(--mono);font-size:9px;display:flex;align-items:center;gap:5px;color:var(--muted2);overflow:hidden;white-space:nowrap}
.sp-svc-dot{width:5px;height:5px;border-radius:50%;flex-shrink:0}
.sp-chron{border-top:1px solid var(--border);padding-top:8px;margin-top:4px}
.sp-chron-item{font-family:var(--mono);font-size:9px;display:flex;gap:8px;margin-bottom:3px;color:var(--muted2)}
.sp-chron-ts{color:var(--muted);flex-shrink:0;min-width:42px}
.sp-faq{border-top:1px solid var(--border);padding-top:8px;margin-top:6px}
.sp-faq-q{font-family:var(--mono);font-size:9px;color:var(--muted);margin-bottom:2px}
.sp-faq-r{font-family:var(--mono);font-size:9px;color:var(--text);line-height:1.4}
.sp-footer{font-family:var(--mono);font-size:8px;color:var(--cyan);margin-top:8px;display:block}
.sp-empty{grid-column:1/-1;text-align:center;padding:60px 20px;font-family:var(--mono);font-size:10px;color:var(--muted);line-height:2}
.sp-bar{background:var(--s1);border-bottom:1px solid var(--border);padding:10px 16px;font-family:var(--mono);font-size:9px;color:var(--muted);display:flex;align-items:center;gap:16px;flex-shrink:0}

/* Thinking indicator */
.thinking{display:flex;gap:6px;padding:20px;align-items:center}
.thinking-dot{
  width:6px;height:6px;border-radius:50%;background:var(--cyan);
  animation:thinking .8s ease-in-out infinite;
}
.thinking-dot:nth-child(2){animation-delay:.2s}
.thinking-dot:nth-child(3){animation-delay:.4s}
@keyframes thinking{0%,100%{transform:scale(1);opacity:.4}50%{transform:scale(1.4);opacity:1}}
.thinking-lbl{font-family:var(--mono);font-size:10px;color:var(--muted);margin-left:6px}

/* Misc */
.tag{display:inline-block;font-family:var(--mono);font-size:8px;padding:1px 5px;
  border-radius:1px;border:1px solid var(--border2);color:var(--muted);margin-right:4px}
</style>
</head>
<body>
<div id="app">

<!-- ══ HEADER ══ -->
<div id="header">
  <div class="h-logo">
    <div>
      <div class="h-logo-text">SCRIBE</div>
      <div class="h-logo-sub">SUPERVISION TERRITORIALE</div>
    </div>
  </div>
  <div class="h-tabs">
    <button class="h-tab active" onclick="switchTab('supervision',this)">⬡ Supervision</button>
    <button class="h-tab" onclick="switchTab('carto',this)">⊕ Cartographie</button>
    <button class="h-tab" onclick="switchTab('statuts',this)">▦ Statuts publics</button>
    <button class="h-tab" onclick="switchTab('albert',this)">◈ Aide à la décision</button>
  </div>
  <div class="h-right">
    <div>
      <div id="clock"></div>
      <div id="date-str"></div>
    </div>
    <div id="global-level-pill" class="h-level-pill level-INCONNU">—</div>
  </div>
</div>

<!-- ══ KPI BAR ══ -->
<div id="kpi-bar">
  <div class="kpi-cell neutral"><div class="kpi-val" id="k-etab">—</div><div class="kpi-lbl">Établissements</div></div>
  <div class="kpi-cell" id="kc-incidents"><div class="kpi-val" id="k-incidents">—</div><div class="kpi-lbl">Incidents ouverts</div></div>
  <div class="kpi-cell" id="kc-critiques"><div class="kpi-val" id="k-critiques">—</div><div class="kpi-lbl">Critiques</div></div>
  <div class="kpi-cell info"><div class="kpi-val" id="k-cyber">—</div><div class="kpi-lbl">Cyber</div></div>
  <div class="kpi-cell" id="kc-sanit"><div class="kpi-val" id="k-sanit">—</div><div class="kpi-lbl">Sanitaire</div></div>
  <div class="kpi-cell" id="kc-crise"><div class="kpi-val" id="k-en-crise">—</div><div class="kpi-lbl">En crise / critique</div></div>
  <div class="kpi-cell neutral" id="kc-statuts" style="border-right:none"><div class="kpi-val" id="k-statuts" style="color:var(--cyan)">—</div><div class="kpi-lbl">Statuts publiés</div></div>
  <div id="last-tick">
    <div class="tick-row"><div class="tick-dot"></div><span id="tick-txt">–</span></div>
    <div style="font-family:var(--mono);font-size:8px;color:var(--muted);margin-top:2px">Prochaine actualisation : <span id="tick-countdown">30</span>s</div>
  </div>
</div>

<!-- ══ TABS CONTENT ══ -->
<div id="tabs-content">

  <!-- TAB 1 : SUPERVISION -->
  <div id="pane-supervision" class="tab-pane active">
    <div id="etab-list">
      <div id="etab-list-header">
        <h3>Établissements</h3>
      </div>
      <div id="etab-scroll"></div>
    </div>
    <div id="detail-panel">
      <div class="detail-empty">
        <div class="detail-empty-icon">⊡</div>
        <div class="detail-empty-txt">Sélectionner un établissement</div>
      </div>
    </div>
    <div id="timeline-panel">
      <div id="timeline-header">
        <h3>Flux incidents</h3>
        <span style="font-family:var(--mono);font-size:8px;color:var(--muted)">Tous sites</span>
      </div>
      <div id="timeline-scroll"></div>
    </div>
  </div>

  <!-- TAB 2 : CARTOGRAPHIE -->
  <div id="pane-carto" class="tab-pane">
    <div id="map"></div>
    <div id="carto-legend">
      <div class="legend-title">NIVEAU D'ALERTE</div>
      <div class="legend-row"><div class="legend-dot" style="background:var(--red);box-shadow:0 0 6px var(--red)"></div>Critique</div>
      <div class="legend-row"><div class="legend-dot" style="background:var(--orange);box-shadow:0 0 6px var(--orange)"></div>Crise</div>
      <div class="legend-row"><div class="legend-dot" style="background:var(--yellow)"></div>Alerte</div>
      <div class="legend-row"><div class="legend-dot" style="background:var(--blue)"></div>Veille</div>
      <div class="legend-row"><div class="legend-dot" style="background:var(--green)"></div>Nominal</div>
      <div class="legend-row"><div class="legend-dot" style="background:var(--muted)"></div>Inconnu</div>
    </div>
  </div>

  <!-- TAB 3 : STATUTS PUBLICS -->
  <div id="pane-statuts" class="tab-pane"></div>

  <!-- TAB 4 : AIDE À LA DÉCISION -->
  <div id="pane-albert" class="tab-pane">
    <div id="albert-left">
      <div id="albert-left-header">
        <h3>◈ Analyse territoriale</h3>
        <div class="albert-form" style="margin-top:0">
          <div>
            <label>Périmètre d'analyse</label>
            <select id="albert-scope" onchange="updateAlbertContext()">
              <option value="all">Tous les établissements</option>
            </select>
          </div>
          <div>
            <label>Contexte additionnel</label>
            <textarea id="albert-context" placeholder="Ex: Plan ORSAN activé, cellule régionale réunie…" rows="3"></textarea>
          </div>
          <button class="btn-albert" onclick="runAlbert()">⬡ Lancer l'analyse</button>
        </div>
      </div>
      <div id="albert-history"></div>
    </div>
    <div id="albert-right">
      <div id="albert-right-header">
        <h3>Recommandations</h3>
        <span id="albert-niveau-badge" class="h-level-pill level-INCONNU" style="display:none"></span>
        <span id="albert-source"></span>
      </div>
      <div id="albert-output">
        <div class="albert-empty">
          <div class="albert-empty-icon">◈</div>
          <div class="albert-empty-txt">En attente d'analyse</div>
          <div style="font-family:var(--mono);font-size:9px;color:var(--muted);max-width:300px;text-align:center;line-height:1.6;margin-top:4px">
            Sélectionner le périmètre et lancer l'analyse pour obtenir une aide à la décision territoriale
          </div>
        </div>
      </div>
    </div>
  </div>

</div><!-- /tabs-content -->
</div><!-- /app -->

<script>
// ═══════════════════════════════════════════════════
//  STATE
// ═══════════════════════════════════════════════════
let allData      = [];
let selectedSigle = null;
let map          = null;
let mapMarkers   = {};
let albertHistory = [];
let countdown    = 30;
let countdownTimer = null;

const ORDRE = {CRITIQUE:4,CRISE:3,ALERTE:2,VEILLE:1,NOMINAL:0,INCONNU:-1};
const COLORS = {
  CRITIQUE: '#ff2d55',
  CRISE:    '#ff7b2c',
  ALERTE:   '#f5c518',
  VEILLE:   '#3d9eff',
  NOMINAL:  '#00e5a0',
  INCONNU:  '#4a5070',
};
const URG_CLS = ['','inc-u1','inc-u2','inc-u3','inc-u4'];
const URG_LBL = ['','V1','V2','V3','V4'];

// ═══════════════════════════════════════════════════
//  CLOCK
// ═══════════════════════════════════════════════════
function updateClock(){
  const now = new Date();
  document.getElementById('clock').textContent =
    now.toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit',second:'2-digit'});
  document.getElementById('date-str').textContent =
    now.toLocaleDateString('fr-FR',{weekday:'long',day:'2-digit',month:'long',year:'numeric'}).toUpperCase();
}
setInterval(updateClock, 1000);
updateClock();

// ═══════════════════════════════════════════════════
//  TAB SWITCHING
// ═══════════════════════════════════════════════════
function switchTab(name, btn){
  document.querySelectorAll('.h-tab').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('pane-' + name).classList.add('active');
  if(name === 'carto') initMap();
  if(name === 'statuts') renderStatuts();
}

// ═══════════════════════════════════════════════════
//  DATA LOADING
// ═══════════════════════════════════════════════════
async function loadData(){
  try {
    const r = await fetch('/api/summary');
    allData = await r.json();
    renderAll();
    if(map) renderMapMarkers();
    document.getElementById('tick-txt').textContent =
      'Actualisé ' + new Date().toLocaleTimeString('fr-FR');
  } catch(e){
    console.error('Erreur chargement:', e);
  }
}

function startCountdown(){
  clearInterval(countdownTimer);
  countdown = 30;
  document.getElementById('tick-countdown').textContent = countdown;
  countdownTimer = setInterval(() => {
    countdown--;
    document.getElementById('tick-countdown').textContent = countdown;
    if(countdown <= 0){ loadData(); countdown = 30; }
  }, 1000);
}

// ═══════════════════════════════════════════════════
//  RENDER ALL
// ═══════════════════════════════════════════════════
function renderAll(){
  renderKpiBar();
  renderEtabList();
  renderTimeline();
  updateAlbertScope();
  if(map) renderMapMarkers();
  if(selectedSigle){
    const e = allData.find(x => x.sigle === selectedSigle);
    if(e) renderDetail(e);
  }
  const maxNiveau = allData.reduce((m,e) => Math.max(m, ORDRE[e.niveau_global]||0), 0);
  const maxLabel  = Object.keys(ORDRE).find(k => ORDRE[k] === maxNiveau) || 'INCONNU';
  const pill = document.getElementById('global-level-pill');
  pill.textContent = maxLabel;
  pill.className   = 'h-level-pill level-' + maxLabel;
}

// ═══════════════════════════════════════════════════
//  KPI BAR
// ═══════════════════════════════════════════════════
function renderKpiBar(){
  const nb      = allData.length;
  const inc     = allData.reduce((s,e)=>s+(e.kpis?.incidents_ouverts||0),0);
  const crit    = allData.reduce((s,e)=>s+(e.kpis?.incidents_critiques||0),0);
  const cyber   = allData.reduce((s,e)=>s+(e.kpis?.cyber||0),0);
  const sanit   = allData.reduce((s,e)=>s+(e.kpis?.sanitaire||0),0);
  const enCrise = allData.filter(e=>['CRITIQUE','CRISE'].includes(e.niveau_global)).length;

  set('k-etab', nb);
  set('k-incidents', inc);
  set('k-critiques', crit);
  set('k-cyber', cyber);
  set('k-sanit', sanit);
  set('k-en-crise', enCrise);

  cls('kc-incidents', inc>0?'warn':'ok');
  cls('kc-critiques', crit>0?'danger':inc>0?'warn':'ok');
  cls('kc-sanit', sanit>0?'warn':'ok');
  cls('kc-crise', enCrise>0?'danger':'ok');
}
function set(id,v){ const el=document.getElementById(id); if(el) el.textContent=v; }
function cls(id,c){
  const el=document.getElementById(id);
  if(el) el.className='kpi-cell '+c;
}

// ═══════════════════════════════════════════════════
//  ETAB LIST
// ═══════════════════════════════════════════════════
function renderEtabList(){
  const container = document.getElementById('etab-scroll');
  if(!allData.length){
    container.innerHTML = '<div style="padding:20px 14px;font-family:var(--mono);font-size:10px;color:var(--muted)">En attente de remontées…</div>';
    return;
  }
  container.innerHTML = allData.map(e => {
    const lvl   = e.niveau_global;
    const stale = !e.fresh ? ' etab-stale' : '';
    const sel   = selectedSigle===e.sigle ? ' selected' : '';
    const age   = e.age_minutes>=0 ? (e.age_minutes<1?'< 1 min':e.age_minutes+'min') : '—';
    return `<div class="etab-row${stale}${sel}" onclick="selectEtab('${e.sigle}')">
      <div class="etab-dot ${lvl}"></div>
      <div class="etab-row-info">
        <div class="etab-row-nom">${e.nom}</div>
        <div class="etab-row-sigle">${e.sigle}</div>
      </div>
      <div class="etab-row-right">
        <span class="etab-badge ${lvl}">${lvl}</span>
        <span class="etab-age">${age}${!e.fresh?' ⚠':''}</span>
      </div>
    </div>`;
  }).join('');
}

function selectEtab(sigle){
  selectedSigle = sigle;
  renderEtabList();
  const e = allData.find(x=>x.sigle===sigle);
  if(e) renderDetail(e);
}

// ═══════════════════════════════════════════════════
//  DETAIL PANEL
// ═══════════════════════════════════════════════════
function esc(s){ return String(s||'').replace(/`/g,'\`').replace(/\${/g,'\${'); }

function renderDetail(e){
  try {
  const panel = document.getElementById('detail-panel');
  const lvl   = e.niveau_global || 'INCONNU';
  const ts    = e.last_update ? new Date(e.last_update).toLocaleString('fr-FR') : '—';
  const k     = e.kpis || {};

  // Services transverses
  const svcs = Object.entries(e.services_transverses||{}).map(([id,s])=>`
    <div class="svc-chip ${s.statut||'OK'}">
      <div class="svc-dot"></div>
      ${s.libelle||id}
    </div>`).join('');

  // Incidents — masquer les résolus par défaut
  const allIncs = e.incidents || [];
  const openIncs = allIncs.filter(i => i.status !== 'RÉSOLU');
  const resolvedCount = allIncs.length - openIncs.length;
  const incs = openIncs.map(i=>`
    <div class="inc-row">
      <div style="display:flex;gap:6px;align-items:center;margin-bottom:4px;flex-wrap:wrap">
        <span class="inc-urg-badge ${URG_CLS[i.urgency]||''}">${URG_LBL[i.urgency]||'U?'}</span>
        <span class="inc-type">${esc(i.type_crise)}</span>
        <span class="inc-status">${esc(i.status)}</span>
        <span class="inc-site" style="margin-left:auto">${esc(i.site)}</span>
      </div>
      <div class="inc-fait" style="width:100%">${esc(i.fait_resume)}</div>
    </div>`).join('');

  // Pôles
  const poles = (e.poles_impactes||[]).map(p=>`<span class="pole-chip">${p}</span>`).join('');

  panel.innerHTML = `
    <div class="detail-header">
      <div>
        <div class="detail-nom">${e.nom}</div>
        <div class="detail-sigle">${e.sigle}</div>
        <div class="detail-ts">Dernière remontée : ${ts}${!e.fresh?' — ⚠ donnée ancienne':''}</div>
      </div>
      <div class="detail-level h-level-pill level-${lvl}">${lvl}</div>
    </div>

    <div class="detail-kpis">
      <div class="dkpi"><div class="dkpi-val" style="color:${k.incidents_ouverts?'var(--orange)':'var(--green)'}">${k.incidents_ouverts||0}</div><div class="dkpi-lbl">Ouverts</div></div>
      <div class="dkpi"><div class="dkpi-val" style="color:${k.incidents_critiques?'var(--red)':'var(--green)'}">${k.incidents_critiques||0}</div><div class="dkpi-lbl">Critiques</div></div>
      <div class="dkpi"><div class="dkpi-val" style="color:var(--purple)">${k.cyber||0}</div><div class="dkpi-lbl">Cyber</div></div>
      <div class="dkpi"><div class="dkpi-val" style="color:var(--blue)">${k.sanitaire||0}</div><div class="dkpi-lbl">Sanitaire</div></div>
    </div>

    ${svcs?`<div class="detail-section">
      <div class="detail-section-header">🔧 Services transverses</div>
      <div class="svc-chips">${svcs}</div>
    </div>`:''}

    ${(e.sites&&e.sites.length>1)?`<div class="detail-section">
      <div class="detail-section-header">🏥 Sites — ${e.sigle}</div>
      <div class="sites-list">${(e.sites||[]).map(s=>{
        const SCOL = {CRITIQUE:'var(--red)',CRISE:'var(--orange)',ALERTE:'var(--yellow)',VEILLE:'var(--blue)',NOMINAL:'var(--green)',INCONNU:'var(--muted)'};
        const col  = SCOL[s.niveau]||'var(--muted)';
        const incsLocaux = (e.incidents||[]).filter(i=>i.site===s.nom);
        return `<div class="site-row">
          <div class="site-dot" style="background:${col};${['CRITIQUE','CRISE'].includes(s.niveau)?'box-shadow:0 0 6px '+col:''}"></div>
          <span class="site-nom">${esc(s.nom)}</span>
          <span class="site-adresse">${esc(s.adresse)}</span>
          ${s.incidents_ouverts?`<span class="site-inc">${s.incidents_ouverts} incident(s)</span>`:''}
          <span class="site-badge" style="color:${col};border:1px solid ${col}20;background:${col}12">${s.niveau||'NOMINAL'}</span>
        </div>
        ${incsLocaux.length?`<div style="padding:0 14px 8px;display:flex;flex-direction:column;gap:4px">
          ${incsLocaux.map(i=>`<div class="inc-row" style="padding:6px 0;border-top:1px solid var(--border)">
            <div style="display:flex;gap:6px;align-items:center;margin-bottom:3px">
              <span class="inc-urg-badge ${URG_CLS[i.urgency]||''}">${URG_LBL[i.urgency]||'U?'}</span>
              <span class="inc-type">${i.type_crise||''}</span>
              <span class="inc-status">${i.status||''}</span>
            </div>
            <div class="inc-fait">${esc(i.fait_resume)}</div>
          </div>`).join('')}
        </div>`:''}`;
      }).join('')}</div>
    </div>`:''}

    ${(!e.sites||e.sites.length<=1)?`<div class="detail-section">
      <div class="detail-section-header" style="display:flex;align-items:center;gap:8px">
        ⬡ Incidents en cours
        ${resolvedCount>0?`<span style="font-family:var(--mono);font-size:8px;color:var(--muted);cursor:pointer;text-decoration:underline" onclick="toggleResolved(this,'resolved-${e.sigle}')">${resolvedCount} résolu(s) archivé(s)</span>`:''}
      </div>
      ${incs?`<div class="detail-section-body">${incs}</div>`:'<div class="detail-section-body" style="color:var(--green);font-family:var(--mono);font-size:10px">✓ Aucun incident ouvert</div>'}
      ${resolvedCount>0?`<div id="resolved-${e.sigle}" style="display:none">
        ${allIncs.filter(i=>i.status==='RÉSOLU').map(i=>`<div class="inc-row" style="opacity:.45">
          <div style="display:flex;gap:6px;align-items:center;margin-bottom:4px">
            <span class="inc-urg-badge">${URG_LBL[i.urgency]||'U?'}</span>
            <span class="inc-type">${esc(i.type_crise)}</span>
            <span style="color:var(--green);font-family:var(--mono);font-size:9px">✓ RÉSOLU</span>
            <span class="inc-site" style="margin-left:auto">${esc(i.site)}</span>
          </div>
          <div class="inc-fait">${esc(i.fait_resume)}</div>
        </div>`).join('')}
      </div>`:''}
    </div>`:``}

    ${poles?`<div class="detail-section">
      <div class="detail-section-header">⊕ Pôles / services impactés</div>
      <div class="poles-chips">${poles}</div>
    </div>`:''}
  `;
  } catch(err) {
    document.getElementById('detail-panel').innerHTML =
      `<div style="padding:20px;font-family:var(--mono);font-size:10px;color:var(--red)">
        ⚠ Erreur d'affichage : ${err.message}<br>
        <span style="color:var(--muted)">Sigle: ${e.sigle||'?'}</span>
      </div>`;
    console.error('renderDetail error:', err, e);
  }
}

// ═══════════════════════════════════════════════════
//  TIMELINE (flux tous établissements)
// ═══════════════════════════════════════════════════
function renderTimeline(){
  const container = document.getElementById('timeline-scroll');
  const all = [];
  allData.forEach(e => {
    (e.incidents||[]).forEach(i => {
      all.push({...i, _etab_nom:e.nom, _etab_sigle:e.sigle, _etab_niveau:e.niveau_global});
    });
  });
  all.sort((a,b)=>(b.urgency-a.urgency)||((b.timestamp||'')>(a.timestamp||'')?1:-1));
  if(!all.length){
    container.innerHTML='<div style="padding:20px;font-family:var(--mono);font-size:9px;color:var(--muted);text-align:center">Aucun incident actif</div>';
    return;
  }
  // Grouper par établissement puis par site
  const grouped = {};
  all.forEach(i => {
    const key = i._etab_sigle;
    if(!grouped[key]) grouped[key] = {nom:i._etab_nom, sigle:i._etab_sigle, niveau:i._etab_niveau, bySite:{}};
    const site = i.site || '—';
    if(!grouped[key].bySite[site]) grouped[key].bySite[site] = [];
    grouped[key].bySite[site].push(i);
  });
  let html = '';
  Object.values(grouped).forEach(etab => {
    const etabCol = COLORS[etab.niveau]||'#4a5070';
    html += `<div class="tl-etab-group">
      <div class="tl-etab-header" onclick="selectEtab('${etab.sigle}');switchTab('supervision',document.querySelector('.h-tab'))" style="cursor:pointer">
        <div class="tl-dot" style="background:${etabCol};box-shadow:0 0 6px ${etabCol};width:10px;height:10px;border-radius:50%;flex-shrink:0"></div>
        <span style="font-family:var(--mono);font-size:10px;font-weight:700;color:${etabCol}">${etab.sigle}</span>
        <span style="font-family:var(--mono);font-size:8px;color:var(--muted);margin-left:4px">${etab.nom}</span>
        <span style="font-family:var(--mono);font-size:8px;padding:1px 5px;border-radius:3px;background:${etabCol}20;color:${etabCol};margin-left:auto">${etab.niveau}</span>
      </div>`;
    Object.entries(etab.bySite).forEach(([site, incs]) => {
      html += `<div class="tl-site-group">
        <div style="font-family:var(--mono);font-size:8px;color:var(--muted2);padding:3px 8px 3px 18px;letter-spacing:.5px">📍 ${site}</div>`;
      incs.forEach(i => {
        const col = COLORS[['','VEILLE','ALERTE','CRISE','CRITIQUE'][i.urgency]||'INCONNU']||'#4a5070';
        const ts  = i.timestamp ? new Date(i.timestamp).toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'}) : '';
        html += `<div class="tl-item" style="padding-left:18px" onclick="selectEtab('${etab.sigle}');switchTab('supervision',document.querySelector('.h-tab'))">
          <div class="tl-content">
            <div class="tl-fait" style="font-size:9px">${(i.fait_resume||'').substring(0,70)}</div>
            <div class="tl-meta">
              <span class="tl-badge ${URG_CLS[i.urgency]||''}" style="color:${col}">${i.type_crise||''} ${URG_LBL[i.urgency]||''}</span>
              <span style="color:var(--muted);font-family:var(--mono);font-size:8px">${ts}</span>
              <span style="color:var(--muted);font-family:var(--mono);font-size:8px">${i.status||''}</span>
            </div>
          </div>
        </div>`;
      });
      html += `</div>`;
    });
    html += `</div>`;
  });
  container.innerHTML = html;
}

// ═══════════════════════════════════════════════════
//  CARTOGRAPHIE
// ═══════════════════════════════════════════════════
let mapInited = false;
function initMap(){
  if(mapInited) return;
  mapInited = true;

  map = L.map('map', {
    center:[46.5,2.5], zoom:6,
    zoomControl:true,
    attributionControl:false,
  });

  // Tuiles dark
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    maxZoom:18, subdomains:'abcd',
  }).addTo(map);

  renderMapMarkers();
}

function getMarkerIcon(niveau){
  const col = COLORS[niveau] || COLORS.INCONNU;
  const size = ['CRITIQUE','CRISE'].includes(niveau) ? 20 : 14;
  const glow = ['CRITIQUE','CRISE','ALERTE'].includes(niveau)
    ? `box-shadow:0 0 ${size}px ${col},0 0 ${size*2}px ${col}40;animation:markerPulse 1.5s ease-in-out infinite;` : '';
  return L.divIcon({
    html:`<div style="width:${size}px;height:${size}px;border-radius:50%;background:${col};border:2px solid ${col};${glow}"></div>
<style>@keyframes markerPulse{0%,100%{transform:scale(1)}50%{transform:scale(1.2)}}</style>`,
    iconSize:[size,size], className:'',
    iconAnchor:[size/2,size/2],
  });
}

function renderMapMarkers(){
  if(!map) return;
  // Supprimer anciens marqueurs
  Object.values(mapMarkers).forEach(m=>m.remove());
  mapMarkers = {};

  const bounds = [];

  allData.forEach(e=>{
    const sites = e.sites && e.sites.length > 1 ? e.sites : null;

    if(sites) {
      // Afficher un marqueur par site avec son niveau propre
      sites.forEach(s=>{
        const lat = s.latitude, lon = s.longitude;
        if(!lat || !lon) return;
        const niveau = s.niveau || e.niveau_global;
        const icon   = getMarkerIcon(niveau);
        const marker = L.marker([lat,lon],{icon}).addTo(map);
        const incsLocaux = (e.incidents||[]).filter(i=>i.site===s.nom).slice(0,3);
        const incsHtml = incsLocaux.map(i=>
          `<div style="font-size:9px;color:#6b7494;padding:1px 0">[${i.type_crise}] ${(i.fait_resume||'').substring(0,50)}</div>`
        ).join('');
        marker.bindPopup(`
          <div class="map-popup">
            <div class="map-popup-header" style="color:${COLORS[niveau]||'#dde4f0'};font-size:11px">${e.sigle} — ${s.nom}</div>
            <div class="map-popup-body">
              <div style="color:${COLORS[niveau]}">● ${niveau}</div>
              <div>${s.incidents_ouverts||0} incident(s) sur ce site</div>
              ${incsHtml}
              ${s.adresse?`<div style="margin-top:4px;font-size:9px;color:#4a5070">${s.adresse}</div>`:''}
            </div>
          </div>`, {maxWidth:300,className:'custom-popup'});
        marker.on('click', ()=>selectEtab(e.sigle));
        mapMarkers[e.sigle+'_'+s.nom] = marker;
        bounds.push([lat,lon]);
      });
    } else {
      // Site unique — marqueur établissement classique
      const lat = e.latitude || e._latitude;
      const lon = e.longitude || e._longitude;
      if(!lat || !lon) return;
      const icon   = getMarkerIcon(e.niveau_global);
      const marker = L.marker([lat,lon],{icon}).addTo(map);
      const incsHtml = (e.incidents||[]).slice(0,4).map(i=>
        `<div style="font-size:9px;color:#6b7494;padding:1px 0">[${i.type_crise}] ${(i.fait_resume||'').substring(0,50)}</div>`
      ).join('');
      marker.bindPopup(`
        <div class="map-popup">
          <div class="map-popup-header" style="color:${COLORS[e.niveau_global]||'#dde4f0'}">${e.nom}</div>
          <div class="map-popup-body">
            <div style="color:${COLORS[e.niveau_global]}">● ${e.niveau_global}</div>
            <div>${e.kpis?.incidents_ouverts||0} incident(s) ouvert(s)</div>
            ${incsHtml}
          </div>
        </div>`, {maxWidth:280,className:'custom-popup'});
      marker.on('click', ()=>selectEtab(e.sigle));
      mapMarkers[e.sigle] = marker;
      bounds.push([lat,lon]);
    }
  });

  if(bounds.length>1) map.fitBounds(bounds,{padding:[40,40]});
  else if(bounds.length===1) map.setView(bounds[0],12);
}

function toggleResolved(btn, divId) {
  const div = document.getElementById(divId);
  if (!div) return;
  const visible = div.style.display !== 'none';
  div.style.display = visible ? 'none' : 'block';
  btn.textContent = visible
    ? btn.textContent.replace('▲','').trim() + ''
    : '▲ ' + btn.textContent;
}

// ═══════════════════════════════════════════════════
//  ALBERT — AIDE À LA DÉCISION
// ═══════════════════════════════════════════════════
function updateAlbertScope(){
  const sel = document.getElementById('albert-scope');
  if(!sel) return;
  const current = sel.value;
  sel.innerHTML = '<option value="all">Tous les établissements</option>'
    + allData.map(e=>`<option value="${e.sigle}">${e.nom}</option>`).join('');
  if(current && [...sel.options].some(o=>o.value===current)) sel.value = current;
}

function updateAlbertContext(){/* noop — scope is read at runtime */}

async function runAlbert(){
  const scope   = document.getElementById('albert-scope').value;
  const context = document.getElementById('albert-context').value.trim();
  const btn     = document.querySelector('.btn-albert');

  // Filtrer les données selon le scope
  const targets = scope==='all' ? allData : allData.filter(e=>e.sigle===scope);
  if(!targets.length){ alert('Aucune donnée disponible'); return; }

  btn.disabled = true;
  const output = document.getElementById('albert-output');
  output.innerHTML = `<div class="thinking">
    <div class="thinking-dot"></div><div class="thinking-dot"></div><div class="thinking-dot"></div>
    <span class="thinking-lbl">Analyse en cours…</span>
  </div>`;

  // Construire le résumé territorial
  const etabsResume = targets.map(e=>{
    const incs = (e.incidents||[]).map(i=>`    [${i.type_crise}] U${i.urgency} ${i.site||''}: ${i.fait_resume||''}`).join('\n');
    const svcs = Object.entries(e.services_transverses||{}).map(([,s])=>`${s.libelle}:${s.statut}`).join(', ');
    return `ÉTABLISSEMENT: ${e.nom} (${e.sigle}) — NIVEAU: ${e.niveau_global}
  Incidents ouverts: ${e.kpis?.incidents_ouverts||0} (dont ${e.kpis?.incidents_critiques||0} critiques)
  Cyber: ${e.kpis?.cyber||0} / Sanitaire: ${e.kpis?.sanitaire||0}
  Services transverses: ${svcs||'N/A'}
  Pôles impactés: ${(e.poles_impactes||[]).join(', ')||'Aucun'}
${incs?`  Détail incidents:\n${incs}`:''}`;
  }).join('\n\n');

  const maxNiveau = targets.reduce((m,e)=>Math.max(m,ORDRE[e.niveau_global]||0),0);
  const maxLabel  = Object.keys(ORDRE).find(k=>ORDRE[k]===maxNiveau)||'INCONNU';
  const nbEtabs   = targets.length;
  const totalInc  = targets.reduce((s,e)=>s+(e.kpis?.incidents_ouverts||0),0);
  const totalCrit = targets.reduce((s,e)=>s+(e.kpis?.incidents_critiques||0),0);

  const payload = {
    model: 'mistralai/Ministral-3-8B-Instruct-2512',
    max_tokens: 1000,
    messages:[{
      role:'system',
      content:`Tu es conseiller en gestion de crise territoriale pour le secteur hospitalier français.
Tu analyses des remontées de plusieurs établissements de santé et tu fournis une aide à la décision au niveau territorial (GHT, ARS, CERT Santé).
Sois PROPORTIONNEL à la situation réelle. Ne dramatise pas si la situation est sous contrôle.
Cite les obligations NIS2/ANSSI uniquement si des incidents cyber significatifs sont présents.
Réponds en français, de façon structurée et opérationnelle.`,
    },{
      role:'user',
      content:`PÉRIMÈTRE: ${scope==='all'?'Tous les établissements du territoire':'Établissement '+scope}
NIVEAU TERRITORIAL MAX: ${maxLabel}
RÉSUMÉ: ${nbEtabs} établissement(s), ${totalInc} incident(s) ouvert(s), ${totalCrit} critique(s)
CONTEXTE ADDITIONNEL: ${context||'Aucun'}

DONNÉES PAR ÉTABLISSEMENT:
${etabsResume}

Produis EXACTEMENT ces sections:
1. SYNTHÈSE TERRITORIALE (3-4 phrases — situation globale)
2. NIVEAU TERRITORIAL: [NOMINAL|VEILLE|ALERTE|CRISE|CRITIQUE] — justification en 1 phrase
3. ÉTABLISSEMENTS PRIORITAIRES (ceux nécessitant attention immédiate, ou RAS)
4. ACTIONS COORDONNÉES (2-4 actions au niveau territorial, adaptées au niveau réel)
5. POINTS DE VIGILANCE (risques d'escalade ou RAS si situation stable)`
    }]
  };

  try {
    const resp = await fetch('https://api.anthropic.com/v1/messages', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        model:'claude-sonnet-4-20250514',
        max_tokens:1000,
        system:`Tu es conseiller en gestion de crise territoriale pour le secteur hospitalier français.
Tu analyses des remontées de plusieurs établissements de santé et tu fournis une aide à la décision au niveau territorial (GHT, ARS, CERT Santé).
Sois PROPORTIONNEL à la situation réelle. Ne dramatise pas si la situation est sous contrôle.
Cite les obligations NIS2/ANSSI uniquement si des incidents cyber significatifs sont présents.
Réponds en français, de façon structurée et opérationnelle.`,
        messages:[{role:'user',content:payload.messages[1].content}]
      })
    });

    let text = '';
    if(resp.ok){
      const data = await resp.json();
      text = data.content?.[0]?.text || '';
    } else {
      // Fallback : essayer Albert si disponible
      throw new Error('Anthropic API indisponible');
    }

    displayAlbertResult(text, scope, maxLabel);
  } catch(e) {
    // Fallback : afficher message d'erreur avec contexte
    displayAlbertError(etabsResume, maxLabel);
  }
  btn.disabled = false;
}

function displayAlbertResult(text, scope, niveau){
  // Formatter le texte : détecter les sections numérotées
  const formatted = text
    .replace(/^(\d+\.\s+[A-ZÀÉÈÊ ]+:?)\s*$/gm, '<span class="section-title">$1</span>')
    .replace(/^(\d+\.\s+[A-ZÀÉÈÊ ]{4,})/gm, '<span class="section-title">$1</span>');

  document.getElementById('albert-output').innerHTML =
    `<div class="albert-response">${formatted}</div>`;

  const badge = document.getElementById('albert-niveau-badge');
  badge.textContent = niveau;
  badge.className   = 'h-level-pill level-' + niveau;
  badge.style.display = '';

  document.getElementById('albert-source').textContent = '◈ Claude / Anthropic';

  // Historique
  const ts = new Date().toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'});
  albertHistory.unshift({ts, scope, niveau, text});
  renderAlbertHistory();
}

function displayAlbertError(context, niveau){
  document.getElementById('albert-output').innerHTML = `
    <div class="albert-response">
      <span class="section-title">⚠ Service IA indisponible</span>
Le service d'analyse IA est temporairement inaccessible depuis le collecteur.

Pour obtenir une analyse, configurez un fournisseur IA accessible depuis ce serveur
(Albert, Ollama local, ou autre) dans les paramètres du collecteur.

<span class="section-title">Données disponibles pour analyse manuelle</span>
${context}
    </div>`;
  document.getElementById('albert-source').textContent = '— IA indisponible';
}

function renderAlbertHistory(){
  const container = document.getElementById('albert-history');
  if(!albertHistory.length){
    container.innerHTML='';
    return;
  }
  container.innerHTML = `<div style="padding:8px 10px 4px;font-family:var(--mono);font-size:8px;color:var(--muted);letter-spacing:1px">HISTORIQUE ANALYSES</div>`
    + albertHistory.slice(0,8).map((h,i)=>`
      <div class="hist-item${i===0?' active':''}" onclick="showHistory(${i})">
        <div class="hist-header">
          <span class="etab-badge ${h.niveau}">${h.niveau}</span>
          <span class="hist-ts">${h.ts}</span>
        </div>
        <div class="hist-ctx">${h.scope==='all'?'Territoire complet':h.scope}</div>
      </div>`).join('');
}

function showHistory(idx){
  const h = albertHistory[idx];
  if(!h) return;
  const formatted = h.text
    .replace(/^(\d+\.\s+[A-ZÀÉÈÊ ]+:?)\s*$/gm, '<span class="section-title">$1</span>')
    .replace(/^(\d+\.\s+[A-ZÀÉÈÊ ]{4,})/gm, '<span class="section-title">$1</span>');
  document.getElementById('albert-output').innerHTML =
    `<div class="albert-response">${formatted}</div>`;
  const badge = document.getElementById('albert-niveau-badge');
  badge.textContent = h.niveau;
  badge.className = 'h-level-pill level-' + h.niveau;
  badge.style.display = '';
  document.querySelectorAll('.hist-item').forEach((el,i)=>
    el.classList.toggle('active', i===idx));
}


// ═══════════════════════════════════════════════════
//  STATUTS PUBLICS
// ═══════════════════════════════════════════════════
function renderStatuts(){
  const pane = document.getElementById('pane-statuts');
  if(!pane) return;
  pane.innerHTML = '';  // reset

  const SVC_COL = {OK:'var(--green)',PERTURBE:'var(--yellow)',HS:'var(--red)',MAINTENANCE:'var(--blue)'};
  const LVL_COL = {OPERATIONNEL:'var(--green)',PERTURBE:'var(--yellow)',INCIDENT_MAJEUR:'var(--red)',MAINTENANCE:'var(--blue)',INCONNU:'var(--muted)'};
  const LVL_LBL = {OPERATIONNEL:'OPÉRATIONNEL',PERTURBE:'PERTURBÉ',INCIDENT_MAJEUR:'INCIDENT MAJEUR',MAINTENANCE:'MAINTENANCE'};

  // Chercher les statuts publics dans allData._status_page
  const etabsAvecStatut = allData.filter(e => e._status_page && e._status_page.published);

  // Barre de synthèse
  const nbPublies = etabsAvecStatut.length;
  const nbTotal   = allData.length;

  let html = `<div class="sp-bar-row">
    ▦ ${nbPublies} / ${nbTotal} établissement(s) avec point de situation publié
    <span style="margin-left:auto;color:var(--muted)">URL publique : http://[IP-ETAB]:8000/status</span>
  </div><div class="sp-grid">`;

  if(!nbPublies){
    html += `<div class="sp-empty">
      Aucun établissement n'a publié de point de situation.<br>
      La publication se fait depuis l'onglet <strong>COMMUNIQUÉ</strong> de chaque SCRIBE.<br>
      <span style="color:var(--muted)">Les établissements doivent activer la fédération et publier depuis SCRIBE → COMMUNIQUÉ → Publier</span>
    </div>`;
  } else {
    html += etabsAvecStatut.map(e => {
      // Collecter tous les statuts : global + sites individuels
      const statuts_sites = e._statuts_sites || [];
      const sp = e._status_page || {};
      const lvl = sp.niveau_global || 'OPERATIONNEL';
      const col = LVL_COL[lvl] || 'var(--muted)';
      const etabNom = (sp.etablissement||{}).nom || e.nom || e.sigle;
      const ts = sp.updated_at
        ? new Date(sp.updated_at).toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'})
        : '—';
      const siSvcs  = (sp.services_si||[]).slice(0,6);
      const pecSvcs = (sp.prise_en_charge||[]).slice(0,6);
      const chrons  = (sp.chronologie||[]).slice(0,4);
      const faqs    = (sp.faq||[]).filter(f=>f.visible&&f.reponse).slice(0,2);

      const svcRows = (list) => {
        const degraded = list.filter(s => s.statut && s.statut !== 'OK');
        const ok_count = list.filter(s => !s.statut || s.statut === 'OK').length;
        let rows = degraded.map(s =>
          `<div class="sp-svc" style="background:${SVC_COL[s.statut]}18;border-radius:3px;padding:3px 6px">
            <div class="sp-svc-dot" style="background:${SVC_COL[s.statut]||'var(--muted)'}"></div>
            <span style="color:${SVC_COL[s.statut]||'var(--text)'};font-weight:600">${(s.label||'').substring(0,24)}</span>
            <span style="margin-left:auto;font-size:8px;opacity:.8">${s.statut}</span>
          </div>`
        ).join('');
        if(ok_count > 0) rows += `<div class="sp-svc" style="opacity:.5">
          <div class="sp-svc-dot" style="background:var(--green)"></div>
          <span>${ok_count} service(s) opérationnel(s)</span>
        </div>`;
        return rows || `<div class="sp-svc"><div class="sp-svc-dot" style="background:var(--green)"></div><span>Tous opérationnels</span></div>`;
      };

      const criseCol = COLORS[e.niveau_global]||'var(--muted)';
      return `<div class="sp-card">
        <div class="sp-card-hdr">
          <div>
            <div class="sp-card-nom">${etabNom}</div>
            <div class="sp-card-sub">Publié ${ts}</div>
          </div>
          <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px">
            <span class="sp-level" style="color:${col};border-color:${col};background:${col}18">${LVL_LBL[lvl]||lvl}</span>
            ${e.niveau_global && e.niveau_global!=='NOMINAL'?`<span style="font-family:var(--mono);font-size:8px;color:${criseCol};letter-spacing:1px">⚠ Crise : ${e.niveau_global}</span>`:''}
          </div>
        </div>
        <div class="sp-body">
          ${sp.message_public?`<div class="sp-msg">${(sp.message_public||'').substring(0,140)}</div>`:''}

          ${siSvcs.length?`
          <div style="font-family:var(--mono);font-size:8px;color:var(--muted);letter-spacing:1px;margin-bottom:4px">SYSTÈME D'INFORMATION</div>
          <div class="sp-services">${svcRows(siSvcs)}</div>`:''}

          ${pecSvcs.length?`
          <div style="font-family:var(--mono);font-size:8px;color:var(--muted);letter-spacing:1px;margin-bottom:4px">PRISE EN CHARGE PATIENTS</div>
          <div class="sp-services">${svcRows(pecSvcs)}</div>`:''}

          ${chrons.length?`<div class="sp-chron">
            <div style="font-family:var(--mono);font-size:8px;color:var(--muted);letter-spacing:1px;margin-bottom:5px">CHRONOLOGIE</div>
            ${chrons.map(c=>`<div class="sp-chron-item">
              <span class="sp-chron-ts">${c.ts?new Date(c.ts).toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'}):''}</span>
              <span>${(c.texte||'').substring(0,80)}</span>
            </div>`).join('')}
          </div>`:''}

          ${faqs.length?`<div class="sp-faq">
            ${faqs.map(f=>`
              <div style="margin-bottom:6px">
                <div class="sp-faq-q">${f.question}</div>
                <div class="sp-faq-r">${(f.reponse||'').substring(0,120)}</div>
              </div>`).join('')}
          </div>`:''}

          <span class="sp-footer">↗ Accessible sur /status (sans authentification)</span>
        </div>
      </div>
      ${statuts_sites.length ? statuts_sites.map(ss => {
        const ssLvl = ss.niveau_global || 'OPERATIONNEL';
        const ssCol = LVL_COL[ssLvl] || 'var(--muted)';
        const ssNom = ss.site_nom || `Site ${ss.site_id}`;
        const ssSvcs = [...(ss.services_si||[]).filter(s=>s.statut!=='OK'),
                        ...(ss.prise_en_charge||[]).filter(s=>s.statut!=='OK')];
        return `<div class="sp-card" style="border-color:${ssCol}30;margin-top:4px">
          <div class="sp-card-hdr" style="background:${ssCol}08">
            <div>
              <div class="sp-card-nom" style="font-size:11px">📍 ${ssNom}</div>
              <div class="sp-card-sub">${etabNom} — site individuel</div>
            </div>
            <span class="sp-level" style="color:${ssCol};border-color:${ssCol};background:${ssCol}18">${LVL_LBL[ssLvl]||ssLvl}</span>
          </div>
          <div class="sp-body">
            ${ss.message_public ? `<div class="sp-msg">${(ss.message_public||'').substring(0,120)}</div>` : ''}
            ${ssSvcs.length ? `<div style="font-family:var(--mono);font-size:8px;color:var(--muted);margin:4px 0 2px">Services impactés</div>
              ${ssSvcs.map(s=>`<div class="sp-svc" style="background:${SVC_COL[s.statut]}18;border-radius:3px;padding:2px 6px">
                <div class="sp-svc-dot" style="background:${SVC_COL[s.statut]}"></div>
                <span style="color:${SVC_COL[s.statut]};font-size:9px">${s.label}</span>
              </div>`).join('')}` : `<div class="sp-svc"><div class="sp-svc-dot" style="background:var(--green)"></div><span>Tous opérationnels</span></div>`}
            <span class="sp-footer" style="margin-top:6px">↗ /status?site_id=${ss.site_id}</span>
          </div>
        </div>`;
      }).join('') : ''}`;
    }).join('');
  }

  html += '</div></div>';
  pane.innerHTML = html;
}

// ═══════════════════════════════════════════════════
//  INIT
// ═══════════════════════════════════════════════════
// ── Login UI (si collecteur_ui_auth.json configuré) ──
async function checkLogin() {
  const r = await fetch('/api/ui/auth-required');
  const d = await r.json();
  if (!d.required) { loadData(); startCountdown(); return; }
  const stored = sessionStorage.getItem('coll_token');
  if (stored) { loadData(); startCountdown(); return; }
  showLoginModal(d.login);
}

function showLoginModal(hint) {
  const modal = document.createElement('div');
  modal.id = 'login-modal';
  modal.style.cssText = 'position:fixed;inset:0;background:#0a0d14;display:flex;align-items:center;justify-content:center;z-index:9999';
  modal.innerHTML = `
    <div style="background:var(--s1);border:1px solid var(--border2);border-radius:8px;padding:32px 40px;min-width:320px;display:flex;flex-direction:column;gap:16px">
      <div style="font-family:var(--head);font-size:22px;font-weight:700;color:var(--cyan);letter-spacing:2px">SCRIBE</div>
      <div style="font-family:var(--mono);font-size:10px;color:var(--muted);letter-spacing:1px">SUPERVISION TERRITORIALE</div>
      <input id="login-user" type="text" value="${hint||''}" placeholder="Identifiant"
        style="font-family:var(--mono);font-size:11px;background:var(--surface2);border:1px solid var(--border2);color:var(--text);padding:8px 10px;border-radius:4px;outline:none">
      <input id="login-pass" type="password" placeholder="Mot de passe"
        style="font-family:var(--mono);font-size:11px;background:var(--surface2);border:1px solid var(--border2);color:var(--text);padding:8px 10px;border-radius:4px;outline:none">
      <div id="login-err" style="font-family:var(--mono);font-size:9px;color:var(--red);display:none">Identifiants incorrects</div>
      <button onclick="doLogin()" style="font-family:var(--mono);font-size:11px;font-weight:700;padding:10px;background:var(--cyan);color:#0a0d14;border:none;border-radius:4px;cursor:pointer;letter-spacing:1px">CONNEXION</button>
    </div>`;
  document.body.appendChild(modal);
  document.getElementById('login-pass').addEventListener('keydown', e => { if(e.key==='Enter') doLogin(); });
}

async function doLogin() {
  const login = document.getElementById('login-user').value;
  const pass  = document.getElementById('login-pass').value;
  const r = await fetch('/api/ui/login', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({login, password: pass})
  });
  if (r.ok) {
    const d = await r.json();
    sessionStorage.setItem('coll_token', d.token);
    document.getElementById('login-modal').remove();
    loadData(); startCountdown();
  } else {
    document.getElementById('login-err').style.display = 'block';
  }
}

checkLogin();
</script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(DASHBOARD_HTML)


@app.get("/health")
def health():
    return {"status": "ok", "etablissements": len(etablissements)}


# ── Auth interface web (optionnelle) ─────────────────────────────────────
UI_AUTH_FILE = "collecteur_ui_auth.json"

def load_ui_auth() -> dict:
    """Charge la config login UI depuis le fichier JSON si présent."""
    if Path(UI_AUTH_FILE).exists():
        try:
            return json.loads(Path(UI_AUTH_FILE).read_text())
        except Exception:
            pass
    return {}  # Pas de protection si fichier absent

def check_ui_credentials(login: str, password: str) -> bool:
    """Vérifie login/mot de passe de l'interface web."""
    auth = load_ui_auth()
    if not auth:
        return True  # Pas de protection configurée
    import hashlib
    h = hashlib.sha256(password.encode()).hexdigest()
    return auth.get("login") == login and auth.get("password_hash") == h


@app.post("/api/ui/login")
async def ui_login(request: Request):
    """Authentification interface web du collecteur."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "JSON invalide")
    login = body.get("login","")
    password = body.get("password","")
    auth = load_ui_auth()
    if not auth:
        return {"ok": True, "token": "no-auth"}  # Pas de protection
    if check_ui_credentials(login, password):
        # Token de session simple
        session_token = secrets.token_hex(16)
        return {"ok": True, "token": session_token}
    raise HTTPException(status_code=401, detail="Identifiants invalides")


@app.get("/api/ui/auth-required")
def auth_required():
    """Indique si l'interface nécessite une authentification."""
    auth = load_ui_auth()
    return {"required": bool(auth), "login": auth.get("login","") if auth else ""}


# ── Démarrage ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    load_tokens()
    load_data()

    nb_etab = len(tokens)
    nb_data  = len(etablissements)

    print("\n  ╔══════════════════════════════════════════════╗")
    print("  ║  SCRIBE Collecteur territorial  v1.1.1       ║")
    print("  ╚══════════════════════════════════════════════╝")
    print(f"\n  Dashboard     : http://0.0.0.0:9000")
    print(f"  Etablissements: {nb_etab} token(s) / {nb_data} remontée(s)")
    print(f"\n  Token admin   : {ADMIN_TOKEN}")
    print(f"  (persistant dans {ADMIN_FILE} — identique à chaque redémarrage)\n")
    if nb_etab == 0:
        print("  ► Aucun établissement enregistré.")
        print("    Enregistrez votre SCRIBE avec la commande suivante")
        print("    (remplacez TOKEN_DU_CONFIG_XML par le token de votre config.xml) :\n")
        print(f'  curl -X POST http://localhost:9000/api/admin/tokens \\')
        print(f'    -H "Authorization: Bearer {ADMIN_TOKEN}" \\')
        print( '    -H "Content-Type: application/json" \\')
        print( '    -d \'{"sigle":"MON_ETAB","token":"TOKEN_QUE_VOUS_AVEZ_CHOISI"}\'\n')
    else:
        etabs = list(set(tokens.values()))
        print(f"  ► Etablissements actifs : {', '.join(etabs)}\n")

    uvicorn.run("collecteur:app", host="0.0.0.0", port=9000, reload=False)
