"""
models.py — Tous les modèles SQLAlchemy — SCRIBE v5
Ajouts v5 : User, Notification, Task, RexEntry
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Hospital(Base):
    __tablename__ = "hospitals"
    id              = Column(Integer, primary_key=True, index=True)
    nom             = Column(String, unique=True, index=True)
    code_finess     = Column(String, unique=True, nullable=True)
    latitude        = Column(Float)
    longitude       = Column(Float)
    adresse         = Column(String, nullable=True)
    telephone_garde = Column(String, nullable=True)
    units = relationship("UniteFonctionnelle", back_populates="hospital", cascade="all, delete-orphan")

class UniteFonctionnelle(Base):
    __tablename__ = "unites_fonctionnelles"
    id          = Column(Integer, primary_key=True, index=True)
    code_uf     = Column(String, index=True)
    libelle     = Column(String)
    pole        = Column(String, nullable=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"))
    hospital    = relationship("Hospital", back_populates="units")

class SitrepEntry(Base):
    __tablename__ = "sitrep_entries"
    id        = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    declarant_nom       = Column(String, nullable=False)
    directeur_crise     = Column(String, nullable=True)
    site_id             = Column(String, nullable=False)
    unite_fonctionnelle = Column(String, nullable=True)
    type_crise          = Column(String, default="CYBER")
    urgency             = Column(Integer, default=1)
    fait                = Column(Text, nullable=False)
    analyse             = Column(Text, nullable=True)
    moyens_engages      = Column(Text, nullable=True)
    actions_remediation = Column(Text, nullable=True)
    intervenant_nom     = Column(String, nullable=True)
    intervenant_contact = Column(String, nullable=True)
    status              = Column(String, default="SIGNALÉ")
    completion_percent  = Column(Integer, default=0)
    estimated_resolution = Column(DateTime, nullable=True)
    resolved_at         = Column(DateTime, nullable=True)
    jalons              = Column(Text, nullable=True)
    albert_avis         = Column(Text, nullable=True)
    attachments = relationship("Attachment", back_populates="entry", cascade="all, delete-orphan")
    tasks       = relationship("Task", back_populates="incident", cascade="all, delete-orphan")

class Decision(Base):
    __tablename__ = "decisions"
    id                 = Column(Integer, primary_key=True, index=True)
    timestamp          = Column(DateTime(timezone=True), server_default=func.now())
    contenu            = Column(Text, nullable=False)
    responsable        = Column(String, nullable=True)
    base_reglementaire = Column(String, default="Plan Blanc")
    statut_validation  = Column(String, default="VALIDÉ")

class Presence(Base):
    __tablename__ = "presences"
    id        = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    nom       = Column(String, nullable=False)
    role      = Column(String, nullable=True)
    action    = Column(String, nullable=False)

class Consigne(Base):
    __tablename__ = "consignes"
    id        = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    pour      = Column(String, nullable=False)
    texte     = Column(Text, nullable=False)
    accuse    = Column(Boolean, default=False)
    accuse_at = Column(DateTime, nullable=True)

class Attachment(Base):
    __tablename__ = "attachments"
    id        = Column(Integer, primary_key=True, index=True)
    filename  = Column(String)
    file_path = Column(String)
    entry_id  = Column(Integer, ForeignKey("sitrep_entries.id"))
    entry     = relationship("SitrepEntry", back_populates="attachments")

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String, unique=True, index=True, nullable=False)
    display_name  = Column(String, nullable=False)
    role          = Column(String, default="directeur")  # admin | directeur | observateur
    hashed_password = Column(String, nullable=False)
    perimetre     = Column(String, nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    active        = Column(Boolean, default=True)
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

class Notification(Base):
    __tablename__ = "notifications"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp   = Column(DateTime(timezone=True), server_default=func.now())
    titre       = Column(String, nullable=False)
    message     = Column(Text, nullable=False)
    type_notif  = Column(String, default="INCIDENT")  # INCIDENT | TACHE | SYSTEME
    incident_id = Column(Integer, ForeignKey("sitrep_entries.id"), nullable=True)
    task_id     = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    lu          = Column(Boolean, default=False)
    user        = relationship("User", back_populates="notifications")

class Task(Base):
    __tablename__ = "tasks"
    id          = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("sitrep_entries.id"), nullable=True)
    titre       = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    assignee    = Column(String, nullable=True)
    priorite    = Column(Integer, default=2)  # 1=basse 2=normale 3=haute 4=critique
    colonne     = Column(String, default="BACKLOG")  # BACKLOG | EN_COURS | EN_ATTENTE | TERMINÉ
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())
    due_at      = Column(DateTime, nullable=True)
    incident    = relationship("SitrepEntry", back_populates="tasks")

class ServiceStatus(Base):
    """Statut manuel des services transverses (sécurité physique, logistique…)."""
    __tablename__ = "service_status"
    id         = Column(Integer, primary_key=True, index=True)
    service_id = Column(String, unique=True, index=True, nullable=False)  # ex: "securite_physique"
    libelle    = Column(String, nullable=False)                            # ex: "Sécurité physique"
    statut     = Column(String, default="OK")                             # OK | DEGRADE | CRITIQUE
    commentaire= Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RexEntry(Base):
    __tablename__ = "rex_entries"
    id              = Column(Integer, primary_key=True, index=True)
    incident_id     = Column(Integer, ForeignKey("sitrep_entries.id"), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    titre           = Column(String, nullable=False)
    type_crise      = Column(String, nullable=True)
    duree_minutes   = Column(Integer, nullable=True)
    nb_poles        = Column(Integer, default=0)
    nb_decisions    = Column(Integer, default=0)
    nb_jalons_total = Column(Integer, default=0)
    nb_jalons_done  = Column(Integer, default=0)
    mttd_minutes    = Column(Integer, nullable=True)
    mttr_minutes    = Column(Integer, nullable=True)
    points_positifs = Column(Text, nullable=True)
    points_amelio   = Column(Text, nullable=True)
    actions_futures = Column(Text, nullable=True)
    lecons          = Column(Text, nullable=True)
    redacteur       = Column(String, nullable=True)
