"""
Point d'entree FastAPI - Unmask Backend.

Lancement : uvicorn app.main:app --reload
Docs auto  : http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.compliance import router as compliance_router
from app.api.legal_identity import router as legal_identity_router
from app.api.partnerships import router as partnerships_router
from app.api.discourse import router as discourse_router
from app.api.youtube import router as youtube_router
from app.api.osint import router as osint_router
from app.api.full_audit import router as full_audit_router

app = FastAPI(
    title="Unmask API",
    description="API d'audit de crédibilité pour influenceurs et marques. 6 piliers factuels.",
    version="2.0.0",
)

# CORS - restreindre en production (jamais * en prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Pilier 1 — Identité légale (data.gouv.fr)
app.include_router(legal_identity_router)

# Pilier 2 — Transparence partenariats (loi 2023)
app.include_router(partnerships_router)

# Pilier 3 — Analyse du discours (Claude API)
app.include_router(discourse_router)

# Pilier 4 — Cohérence engagement (YouTube Data API)
app.include_router(youtube_router)

# Pilier 5 — Réputation externe OSINT
app.include_router(osint_router)

# Pilier 6 — Conformité institutionnelle (AMF/ACPR)
app.include_router(compliance_router)

# Orchestrateur — Audit complet (6 piliers)
app.include_router(full_audit_router)


@app.get("/health", tags=["Santé"])
def health_check():
    """Vérifie que l'API est opérationnelle."""
    return {"status": "ok", "version": "2.0.0"}
