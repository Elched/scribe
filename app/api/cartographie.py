"""
api/cartographie.py — Sites hospitaliers et Unités Fonctionnelles.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import Hospital, UniteFonctionnelle

router = APIRouter()


class HospitalOut(BaseModel):
    id: int
    nom: str
    code_finess: Optional[str]
    latitude: float
    longitude: float
    adresse: Optional[str]
    telephone_garde: Optional[str]
    class Config:
        from_attributes = True

class UFOut(BaseModel):
    id: int
    code_uf: str
    libelle: str
    pole: Optional[str]
    class Config:
        from_attributes = True


@router.get("/sites", response_model=List[HospitalOut])
def get_sites(db: Session = Depends(get_db)):
    return db.query(Hospital).all()


@router.get("/{hospital_name}/units", response_model=List[UFOut])
def get_units(hospital_name: str, db: Session = Depends(get_db)):
    h = db.query(Hospital).filter(Hospital.nom == hospital_name).first()
    if not h:
        return []
    return (
        db.query(UniteFonctionnelle)
        .filter(UniteFonctionnelle.hospital_id == h.id)
        .order_by(UniteFonctionnelle.libelle)
        .all()
    )


@router.get("/poles")
def get_poles(db: Session = Depends(get_db)):
    """Liste des pôles actifs (hors UF supprimées)."""
    from sqlalchemy import func as sqlfunc
    poles = (
        db.query(UniteFonctionnelle.pole, sqlfunc.count().label("n"))
        .filter(UniteFonctionnelle.pole != "", UniteFonctionnelle.pole != None,
                ~UniteFonctionnelle.pole.like("RAPPEL%"))
        .group_by(UniteFonctionnelle.pole)
        .order_by(UniteFonctionnelle.pole)
        .all()
    )
    return [{"pole": p.pole, "count": p.n} for p in poles]


@router.get("/uf-to-pole")
def get_uf_to_pole(db: Session = Depends(get_db)):
    """Retourne la map code_uf -> pole basée sur les libellés des UF."""
    all_ufs = db.query(
        UniteFonctionnelle.code_uf,
        UniteFonctionnelle.libelle,
        UniteFonctionnelle.pole
    ).distinct().all()

    POLE_KEYWORDS = {
        'CANCEROLOGIE':                   ['CANCERO','ONCOL','RADIOTHER','HDJ CANC','3C 74'],
        'CARDIOVASCULAIRE':               ['CARDIO','CORONAR','USIC','VASCU','AORTIQUE'],
        'CHIRURGIE ANESTHESIE':           ['CHIRUR','ANESTHES','BLOC OP','ORTHO','TRAUMA','VISCERAL','ORL','OPHTAL'],
        'DNA':                            ['DNA','DPI','ARCHIV'],
        'FME':                            ['MATERNIT','GYNECO','NEONATO','OBSTETR','SAGE FEMME','ACCOUCHEMENT','FME'],
        'GERIATRIE':                       ['GERIATR','EHPAD','USLD','SOINS PALLIAT','GERONTOL'],
        'MEDECINE':                       ['ALLERGO','PNEUMOL','NEUROLOG','HEPATO','GASTRO','ENDOCRIN','DIABETOL','RHUMATO','DERMATO','INFECTIOL','NEPHROL','HEMODIALYS','HEMATO'],
        'MEDICO-TECHNIQUE ET REEDUCATION':['LABORATOIR','BIOCHIM','MICROBIOL','IMAGERIE','SCANNER','PHARMA','REEDUCATION','KINESITH','ORTHOPH'],
        'SANTE MENTALE':                  ['PSYCHIATR','SANTE MENTALE','ADDICTOL','UPUP','MONET','PICASSO','GAUGUIN'],
        'SANTE PUBLIQUE ET COMMUNAUTAIRE':['HAD ','PMSI','PREVENTION','HYGIENE','EPIDEMIO','SANTE PUBLIQUE'],
        'SOINS CRITIQUES':                ['REANIM','USIP','SOINS CRITIQUES','SIPO'],
        'URGENCES':                       ['URGENCE','SMUR','SAMU','UHCD','UPUM'],
        'IFSI':                           ['IFSI','FORMATION INFIRM'],
        'SUPPORT':                        ['DIRECTION','DSI','INFORMATIQ','LOGISTIQ','BRANCARDIER','CUISINE','RESTAUR','BLANCHISS','STANDARD','SECURITE','DRH','DAF'],
    }

    uf_to_pole = {}
    for uf in all_ufs:
        if uf.pole and not uf.pole.startswith('RAPPEL'):
            uf_to_pole[uf.code_uf] = uf.pole
            continue
        lib = (uf.libelle or '').upper()
        for pole, kws in POLE_KEYWORDS.items():
            if any(kw in lib for kw in kws):
                uf_to_pole[uf.code_uf] = pole
                break

    return uf_to_pole
