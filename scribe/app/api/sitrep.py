"""
api/sitrep.py — Main courante complète v2.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel
import json

from app.database import get_db
from app.models import SitrepEntry, Attachment
try:
    from app.api.auth import notify_incident
except Exception:
    def notify_incident(db, incident, action='INCIDENT'): pass

router = APIRouter()


class IncidentCreate(BaseModel):
    declarant_nom: str
    directeur_crise: Optional[str] = None
    site_id: str
    unite_fonctionnelle: Optional[str] = ""
    type_crise: Optional[str] = "CYBER"
    urgency: int = 1
    fait: str
    analyse: Optional[str] = ""
    moyens_engages: Optional[str] = ""
    actions_remediation: Optional[str] = ""
    intervenant_nom: Optional[str] = ""
    intervenant_contact: Optional[str] = ""
    estimated_resolution: Optional[datetime] = None
    # Jalons prédéfinis (liste de labels)
    jalons_labels: Optional[List[str]] = []

class IncidentOut(BaseModel):
    id: int
    timestamp: datetime
    declarant_nom: str
    directeur_crise: Optional[str]
    site_id: str
    unite_fonctionnelle: Optional[str]
    type_crise: str
    urgency: int
    fait: str
    analyse: Optional[str]
    moyens_engages: Optional[str]
    actions_remediation: Optional[str]
    intervenant_nom: Optional[str]
    intervenant_contact: Optional[str]
    status: str
    completion_percent: int
    estimated_resolution: Optional[datetime]
    resolved_at: Optional[datetime]
    jalons: Optional[str]
    albert_avis: Optional[str]
    class Config:
        from_attributes = True

class StatusUpdate(BaseModel):
    status: str
    completion_percent: Optional[int] = None

class JalonUpdate(BaseModel):
    jalons: List[dict]  # [{label, done, done_at}]

class AlbertAvisUpdate(BaseModel):
    avis: str


@router.post("/post", response_model=IncidentOut)
def create_incident(entry: IncidentCreate, db: Session = Depends(get_db)):
    data = entry.dict(exclude={"jalons_labels"})
    # Construire les jalons depuis les labels
    jalons_labels = entry.jalons_labels or []
    if jalons_labels:
        jalons = [{"label": l, "done": False, "done_at": None} for l in jalons_labels]
        data["jalons"] = json.dumps(jalons, ensure_ascii=False)
    new_incident = SitrepEntry(**data)
    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)
    try:
        notify_incident(db, new_incident)
    except Exception:
        pass
    return new_incident


@router.get("/history", response_model=List[IncidentOut])
def get_history(
    site: Optional[str] = None,
    urgency: Optional[int] = None,
    status: Optional[str] = None,
    type_crise: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(SitrepEntry)
    if site:       q = q.filter(SitrepEntry.site_id == site)
    if urgency:    q = q.filter(SitrepEntry.urgency == urgency)
    if status:     q = q.filter(SitrepEntry.status == status)
    if type_crise: q = q.filter(SitrepEntry.type_crise == type_crise)
    return q.order_by(SitrepEntry.timestamp.desc()).all()


@router.put("/{incident_id}/status")
def update_status(incident_id: int, update: StatusUpdate, db: Session = Depends(get_db)):
    inc = db.query(SitrepEntry).filter(SitrepEntry.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident non trouvé")
    inc.status = update.status
    if update.completion_percent is not None:
        inc.completion_percent = update.completion_percent
    if update.status == "RÉSOLU" and not inc.resolved_at:
        inc.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "updated", "new_status": inc.status, "resolved_at": inc.resolved_at}


@router.put("/{incident_id}/jalons")
def update_jalons(incident_id: int, update: JalonUpdate, db: Session = Depends(get_db)):
    inc = db.query(SitrepEntry).filter(SitrepEntry.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident non trouvé")
    inc.jalons = json.dumps(update.jalons, ensure_ascii=False, default=str)
    # Auto-calcul completion
    total = len(update.jalons)
    done  = sum(1 for j in update.jalons if j.get("done"))
    inc.completion_percent = int(done / total * 100) if total else 0
    db.commit()
    return {"status": "ok", "completion": inc.completion_percent}


@router.put("/{incident_id}/albert-avis")
def save_albert_avis(incident_id: int, update: AlbertAvisUpdate, db: Session = Depends(get_db)):
    inc = db.query(SitrepEntry).filter(SitrepEntry.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident non trouvé")
    inc.albert_avis = update.avis
    db.commit()
    return {"status": "ok"}


@router.delete("/{incident_id}")
def delete_incident(incident_id: int, db: Session = Depends(get_db)):
    inc = db.query(SitrepEntry).filter(SitrepEntry.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident non trouvé")
    db.delete(inc)
    db.commit()
    return {"status": "deleted"}


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total     = db.query(SitrepEntry).count()
    critical  = db.query(SitrepEntry).filter(SitrepEntry.urgency >= 3, SitrepEntry.status != "RÉSOLU").count()
    ouverts   = db.query(SitrepEntry).filter(SitrepEntry.status != "RÉSOLU").count()
    cyber     = db.query(SitrepEntry).filter(SitrepEntry.type_crise == "CYBER").count()
    sanitaire = db.query(SitrepEntry).filter(SitrepEntry.type_crise == "SANITAIRE").count()

    by_site = db.query(
        SitrepEntry.site_id,
        sqlfunc.count(SitrepEntry.id).label("count")
    ).filter(SitrepEntry.status != "RÉSOLU").group_by(SitrepEntry.site_id).all()

    return {
        "total": total, "critical": critical, "ouverts": ouverts,
        "cyber": cyber, "sanitaire": sanitaire,
        "by_site": [{"site": r.site_id, "count": r.count} for r in by_site]
    }


@router.get("/export-csv")
def export_csv(db: Session = Depends(get_db)):
    """Export de la main courante en CSV."""
    from fastapi.responses import StreamingResponse
    import csv, io
    incidents = db.query(SitrepEntry).order_by(SitrepEntry.timestamp.asc()).all()
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL)
    writer.writerow([
        "ID","Horodatage","Type","Urgence","Site","UF","Déclarant","Directeur",
        "Fait","Analyse","Moyens","Intervenant","Contact","Statut","Résolu le","Actions"
    ])
    for i in incidents:
        writer.writerow([
            i.id,
            i.timestamp.strftime("%d/%m/%Y %H:%M:%S") if i.timestamp else "",
            i.type_crise, i.urgency, i.site_id, i.unite_fonctionnelle or "",
            i.declarant_nom, i.directeur_crise or "",
            i.fait, i.analyse or "", i.moyens_engages or "",
            i.intervenant_nom or "", i.intervenant_contact or "",
            i.status,
            i.resolved_at.strftime("%d/%m/%Y %H:%M:%S") if i.resolved_at else "",
            i.actions_remediation or ""
        ])
    output.seek(0)
    filename = f"main_courante_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
