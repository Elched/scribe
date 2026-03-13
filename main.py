"""
main.py — SCRIBE v5
"""
import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.database import engine, Base
import app.models  # noqa

from app.api import sitrep, cellule, releve, cartographie, albert, attachments
from app.api import auth, tasks, rapport

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SCRIBE v5 Crisis OS", version="5.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

STATIC_DIR = os.path.join(os.path.dirname(__file__), "app", "static")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/static",  StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(sitrep.router,       prefix="/api/v1/sitrep",       tags=["Incidents"])
app.include_router(cellule.router,      prefix="/api/v1/cellule",      tags=["Cellule"])
app.include_router(releve.router,       prefix="/api/v1/releve",       tags=["Relève"])
app.include_router(cartographie.router, prefix="/api/v1/cartographie", tags=["Cartographie"])
app.include_router(albert.router,       prefix="/api/v1/albert",       tags=["Albert AI"])
app.include_router(attachments.router,  prefix="/api/v1/attachments",  tags=["PJ"])
app.include_router(auth.router,         prefix="/api/v1/auth",         tags=["Auth"])
app.include_router(tasks.router,        prefix="/api/v1/tasks",        tags=["Kanban"])
app.include_router(rapport.router,      prefix="/api/v1/rapport",      tags=["Rapport"])

@app.get("/")
async def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/health")
def health():
    return {"status": "ok", "version": "5.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
