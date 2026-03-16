"""
api/attachments.py — Upload de pièces jointes liées à un incident.
"""
import os, shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SitrepEntry, Attachment

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/{incident_id}/upload")
async def upload_document(incident_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    incident = db.query(SitrepEntry).filter(SitrepEntry.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident non trouvé")

    safe_name = f"{incident_id}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    with open(file_path, "wb") as buf:
        shutil.copyfileobj(file.file, buf)

    attachment = Attachment(filename=file.filename, file_path=file_path, entry_id=incident_id)
    db.add(attachment)
    db.commit()
    return {"status": "ok", "filename": file.filename, "url": f"/uploads/{safe_name}"}


@router.get("/{incident_id}")
def get_attachments(incident_id: int, db: Session = Depends(get_db)):
    return db.query(Attachment).filter(Attachment.entry_id == incident_id).all()
