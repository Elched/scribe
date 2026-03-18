"""
main.py — SCRIBE v6
"""
import asyncio
import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
import app.models  # noqa
import app.api.status_page  # noqa — enregistre les tables StatusPage

from app.api import sitrep, cellule, releve, cartographie, albert, attachments, i18n
from app.api import auth, tasks, rapport, federation, status_page

logging.basicConfig(level=logging.INFO)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SCRIBE v6 Crisis OS", version="6.0.0")
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
app.include_router(federation.router,   prefix="/api/v1/federation",   tags=["Fédération"])
app.include_router(status_page.router,  prefix="/api/v1/status",       tags=["Status Page"])
app.include_router(i18n.router,         prefix="",                     tags=["i18n"])


@app.on_event("startup")
async def startup():
    asyncio.create_task(federation.federation_loop())


@app.get("/")
async def root():
    from fastapi.responses import FileResponse
    from starlette.responses import Response
    resp = FileResponse(
        os.path.join(STATIC_DIR, "index.html"),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }
    )
    return resp


@app.get("/status", response_class=HTMLResponse)
async def public_status():
    """Page de statut publique — accessible sans authentification."""
    return HTMLResponse(open(os.path.join(STATIC_DIR, "status.html"), encoding="utf-8").read())


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.2.0"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
