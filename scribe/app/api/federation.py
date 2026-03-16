"""
app/api/federation.py — Push JSON vers un collecteur territorial (CERT Santé, ARS, supervision GHT)

Principe :
  - SCRIBE envoie périodiquement un résumé JSON signé vers une URL externe (collecteur)
  - Sens unique : push uniquement, jamais de pull depuis l'extérieur
  - Aucune donnée nominative dans le payload
  - Si le collecteur est injoignable → SCRIBE continue normalement, erreur loggée silencieusement
  - Activé uniquement si <federation><enabled>true</enabled> dans config.xml / config.js

Configuration dans config.xml :
  <federation>
    <enabled>true</enabled>
    <collecteur_url>https://supervision.cert-sante74.fr/api/push</collecteur_url>
    <token>TOKEN_256BITS_GENERE_PAR_LE_COLLECTEUR</token>
    <intervalle_secondes>120</intervalle_secondes>   <!-- défaut : 120s -->
    <share_details>true</share_details>              <!-- inclure résumés incidents ou KPIs seuls -->
    <share_min_urgency>1</share_min_urgency>         <!-- urgence minimale pour inclure un incident -->
  </federation>
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import SitrepEntry, ServiceStatus, Hospital
from app.api.status_page import _get_or_create as _get_status, _row_to_dict as _status_to_dict, StatusPageChronologie

logger = logging.getLogger("scribe.federation")
router = APIRouter()

# ── Configuration fédération (chargée au démarrage) ────────────────────────

class FederationConfig:
    def __init__(self):
        self.enabled            = False
        self.collecteur_url     = ""
        self.token              = ""
        self.intervalle         = 120       # secondes
        self.share_details      = True
        self.share_min_urgency  = 1
        self.etablissement_nom  = "Établissement"
        self.etablissement_sigle = "ETB"
        self._load()

    def _load(self):
        config_js = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "app", "static", "config.js"
        )
        if not os.path.exists(config_js):
            return
        try:
            raw   = open(config_js, encoding="utf-8").read()
            start = raw.find("const SCRIBE_CONFIG = ") + len("const SCRIBE_CONFIG = ")
            end   = raw.rfind(";")
            cfg   = json.loads(raw[start:end])

            etb = cfg.get("etablissement", {})
            self.etablissement_nom   = etb.get("nom",   "Établissement")
            self.etablissement_sigle = etb.get("sigle", "ETB")

            fed = cfg.get("federation", {})
            self.enabled           = str(fed.get("enabled", "false")).lower() == "true"
            self.collecteur_url    = fed.get("collecteur_url", "").strip()
            self.token             = fed.get("token", "").strip()
            self.intervalle        = int(fed.get("intervalle_secondes", 120))
            self.share_details     = str(fed.get("share_details", "true")).lower() == "true"
            self.share_min_urgency = int(fed.get("share_min_urgency", 1))
        except Exception as e:
            logger.warning(f"Federation config non chargée : {e}")

    @property
    def is_ready(self) -> bool:
        return self.enabled and bool(self.collecteur_url) and bool(self.token)


_fed_config: Optional[FederationConfig] = None

def get_fed_config() -> FederationConfig:
    global _fed_config
    if _fed_config is None:
        _fed_config = FederationConfig()
    return _fed_config


# ── Construction du payload ────────────────────────────────────────────────

def build_payload(db: Session, cfg: FederationConfig) -> dict:
    """Construit le JSON à envoyer au collecteur. Aucune donnée nominative."""

    now = datetime.now(timezone.utc)
    open_incidents = (
        db.query(SitrepEntry)
        .filter(SitrepEntry.status != "RÉSOLU")
        .order_by(SitrepEntry.urgency.desc(), SitrepEntry.timestamp.desc())
        .all()
    )

    # KPIs
    nb_total    = len(open_incidents)
    nb_critique = sum(1 for i in open_incidents if i.urgency >= 4)
    nb_crise    = sum(1 for i in open_incidents if i.urgency == 3)
    nb_cyber    = sum(1 for i in open_incidents if i.type_crise == "CYBER")
    nb_sanit    = sum(1 for i in open_incidents if i.type_crise == "SANITAIRE")
    max_urgency = max((i.urgency for i in open_incidents), default=0)

    # Niveau global
    if max_urgency >= 4:    niveau = "CRITIQUE"
    elif max_urgency >= 3:  niveau = "CRISE"
    elif max_urgency >= 2:  niveau = "ALERTE"
    elif max_urgency >= 1:  niveau = "VEILLE"
    else:                   niveau = "NOMINAL"

    # Services transverses
    services = {}
    try:
        for s in db.query(ServiceStatus).all():
            services[s.service_id] = {
                "libelle": s.libelle,
                "statut":  s.statut,
            }
    except Exception:
        pass

    # Pôles impactés (dédupliqués)
    # Résoudre les libellés UF (code → libellé lisible)
    from app.models import UniteFonctionnelle
    uf_map = {}
    try:
        for uf in db.query(UniteFonctionnelle).all():
            uf_map[uf.code_uf] = uf.libelle
    except Exception:
        pass

    poles_impactes = list({
        uf_map.get(i.unite_fonctionnelle, i.unite_fonctionnelle)
        for i in open_incidents
        if i.unite_fonctionnelle and i.urgency >= cfg.share_min_urgency
    })

    # Coordonnées GPS + infos du site principal (premier hôpital)
    lat, lon = None, None
    sites_db = []
    try:
        sites_db = db.query(Hospital).order_by(Hospital.id).all()
        if sites_db:
            lat, lon = sites_db[0].latitude, sites_db[0].longitude
    except Exception:
        pass

    # Index sites par nom pour retrouver les GPS depuis site_id
    site_by_name = {h.nom: h for h in sites_db}

    payload = {
        "version":    "1",
        "timestamp":  now.isoformat(),
        "etablissement": {
            "nom":   cfg.etablissement_nom,
            "sigle": cfg.etablissement_sigle,
        },
        "latitude":  lat,
        "longitude": lon,
        "niveau_global": niveau,
        "kpis": {
            "incidents_ouverts":   nb_total,
            "incidents_critiques": nb_critique,
            "incidents_crise":     nb_crise,
            "cyber":               nb_cyber,
            "sanitaire":           nb_sanit,
        },
        "services_transverses": services,
        "poles_impactes":       poles_impactes,
        # Sites comme sous-entités avec leurs incidents propres
        "sites": [
            {
                "nom":       h.nom,
                "finess":    h.code_finess or "",
                "latitude":  h.latitude,
                "longitude": h.longitude,
                "adresse":   h.adresse or "",
                "niveau": (
                    lambda incs: (
                        "CRITIQUE" if any(i.urgency >= 4 for i in incs) else
                        "CRISE"    if any(i.urgency >= 3 for i in incs) else
                        "ALERTE"   if any(i.urgency >= 2 for i in incs) else
                        "VEILLE"   if any(i.urgency >= 1 for i in incs) else
                        "NOMINAL"
                    )
                )([i for i in open_incidents if i.site_id == h.nom]),
                "incidents_ouverts": len([i for i in open_incidents if i.site_id == h.nom]),
            }
            for h in sites_db
        ],
    }

    # Détail incidents (si activé et urgence >= seuil)
    if cfg.share_details:
        payload["incidents"] = [
            {
                "type_crise":  i.type_crise,
                "urgency":     i.urgency,
                "fait_resume": (i.fait or "")[:120],
                "site":        i.site_id,
                "status":      i.status,
                "timestamp":   i.timestamp.isoformat() if i.timestamp else "",
            }
            for i in open_incidents
            if i.urgency >= cfg.share_min_urgency
        ]

    # Signature HMAC-SHA256 du payload (intégrité)
    payload_bytes = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    signature = hashlib.sha256(
        (cfg.token + ":" + payload_bytes.decode()).encode()
    ).hexdigest()
    payload["_sig"] = signature[:16]   # 8 bytes visibles pour contrôle rapide

    return payload


# ── Push vers le collecteur ────────────────────────────────────────────────

async def push_to_collecteur(cfg: FederationConfig, payload: dict) -> bool:
    """Envoie le payload. Retourne True si succès, False sinon (silencieux)."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                cfg.collecteur_url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {cfg.token}",
                    "Content-Type":  "application/json",
                    "X-Scribe-Version": "6",
                    "X-Scribe-Etab":    cfg.etablissement_sigle,
                },
            )
        if resp.status_code in (200, 201, 204):
            logger.debug(f"Federation push OK → {cfg.collecteur_url} ({resp.status_code})")
            return True
        else:
            logger.warning(f"Federation push HTTP {resp.status_code} → {cfg.collecteur_url}")
            return False
    except httpx.ConnectError:
        logger.warning(f"Federation : collecteur injoignable ({cfg.collecteur_url})")
        return False
    except httpx.TimeoutException:
        logger.warning(f"Federation : timeout ({cfg.collecteur_url})")
        return False
    except Exception as e:
        logger.warning(f"Federation : erreur inattendue : {e}")
        return False



async def push_status_to_collecteur(cfg: "FederationConfig") -> bool:
    """Push le statut public vers le collecteur (endpoint /api/push-status)."""
    try:
        db = SessionLocal()
        row = _get_status(db)
        if not row.published:
            db.close()
            return True  # Pas publié → pas de push, c'est normal
        chrons = db.query(StatusPageChronologie).order_by(
            StatusPageChronologie.timestamp.desc()).limit(10).all()
        chrons_list = [
            {"id": c.id, "ts": c.timestamp.isoformat(), "texte": c.texte, "publie_par": c.publie_par or ""}
            for c in chrons
        ]
        from app.api.status_page import _load_etablissement
        payload = _status_to_dict(row, chrons_list)
        payload["etablissement"] = _load_etablissement()
        payload["_pushed_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        db.close()

        push_url = cfg.collecteur_url.replace("/api/push", "/api/push-status")
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                push_url, json=payload,
                headers={"Authorization": f"Bearer {cfg.token}",
                         "Content-Type": "application/json"},
            )
        return resp.status_code in (200, 201, 204)
    except Exception as e:
        logger.debug(f"push_status silencieux : {e}")
        return False


# ── Boucle périodique (lancée par main.py au démarrage) ───────────────────

async def federation_loop():
    """Tâche asyncio : push périodique vers le collecteur."""
    cfg = get_fed_config()
    if not cfg.is_ready:
        if cfg.enabled:
            logger.warning("Federation activée mais collecteur_url ou token manquant — désactivée.")
        return

    logger.info(
        f"Federation activée → {cfg.collecteur_url} "
        f"(intervalle: {cfg.intervalle}s, détails: {cfg.share_details})"
    )

    while True:
        try:
            db = SessionLocal()
            payload = build_payload(db, cfg)
            db.close()
            ok = await push_to_collecteur(cfg, payload)
            if ok:
                await push_status_to_collecteur(cfg)
        except Exception as e:
            logger.warning(f"Federation loop erreur : {e}")
        await asyncio.sleep(cfg.intervalle)


# ── Endpoint de test (admin seulement) ────────────────────────────────────

@router.get("/info")
def federation_info():
    """Retourne les infos de fédération — token, URL collecteur, commande d'enregistrement."""
    cfg = get_fed_config()
    cmd = ""
    if cfg.token and cfg.collecteur_url:
        register_url = cfg.collecteur_url.replace("/api/push", "/api/admin/tokens")
        cmd = (
            f'curl -X POST {register_url} \\\n'
            f'  -H "Authorization: Bearer TOKEN_ADMIN_COLLECTEUR" \\\n'
            f'  -H "Content-Type: application/json" \\\n'
            f'  -d \'{{"sigle":"{cfg.etablissement_sigle}","token":"{cfg.token}"}}\''
        )
    return {
        "enabled":        cfg.enabled,
        "collecteur_url": cfg.collecteur_url,
        "sigle":          cfg.etablissement_sigle,
        "token":          cfg.token,
        "commande_enregistrement": cmd,
        "message": "Copiez la commande ci-dessus et exécutez-la sur le serveur collecteur" if cmd else "Fédération non configurée"
    }


@router.post("/test")
async def test_push():
    """Déclenche un push immédiat vers le collecteur (diagnostic)."""
    cfg = get_fed_config()
    if not cfg.is_ready:
        return {"ok": False, "detail": "Federation non configurée ou désactivée"}
    db = SessionLocal()
    payload = build_payload(db, cfg)
    db.close()
    success = await push_to_collecteur(cfg, payload)
    return {
        "ok":        success,
        "payload":   payload,
        "collecteur": cfg.collecteur_url,
    }

@router.get("/status")
async def federation_status():
    """Retourne l'état de la configuration fédération."""
    cfg = get_fed_config()
    return {
        "enabled":        cfg.enabled,
        "is_ready":       cfg.is_ready,
        "collecteur_url": cfg.collecteur_url if cfg.is_ready else "(non configuré)",
        "etablissement":  cfg.etablissement_sigle,
        "intervalle":     cfg.intervalle,
        "share_details":  cfg.share_details,
    }
