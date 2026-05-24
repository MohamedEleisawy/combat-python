"""
Route POST /audit/full — Orchestrateur des 6 piliers.

Lance tous les piliers disponibles en parallèle et retourne
un rapport unifié avec un score global de crédibilité.
"""

import asyncio
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.siren_checker import check_legal_identity
from app.services.amf_checker import check_compliance
from app.services.partnership_checker import check_partnership_transparency
from app.services.discourse_analyzer import analyze_discourse
from app.services.youtube_checker import check_youtube_engagement
from app.services.osint_checker import check_osint_reputation

router = APIRouter(prefix="/audit", tags=["Audit Complet"])


class FullAuditRequest(BaseModel):
    entity_name: Optional[str] = Field(default=None, description="Nom public de l'entité.")
    siren: Optional[str] = Field(default=None, description="SIREN à 9 chiffres.")
    url: Optional[str] = Field(default=None, description="URL du site ou profil réseau social.")
    youtube_url: Optional[str] = Field(default=None, description="URL de la chaîne YouTube.")
    sector: Optional[str] = Field(default="autre", description="Secteur d'activité.")
    text_to_analyze: Optional[str] = Field(default=None, description="Texte à analyser (discours, description).")


def _global_score(pillars: dict) -> int:
    """Calcule un score global 0-100 à partir des résultats des piliers."""
    scores = []

    # Pilier 1 — identité légale
    legal = pillars.get("legal_identity")
    if legal and not legal.get("warning") and legal.get("found") is not None:
        scores.append(100 if legal["found"] else 30)

    # Pilier 2 — partenariats
    p2 = pillars.get("partnerships")
    if p2 and p2.get("compliance_score") is not None:
        scores.append(p2["compliance_score"])

    # Pilier 3 — discours
    p3 = pillars.get("discourse")
    if p3 and p3.get("available") and p3.get("manipulation_score") is not None:
        scores.append(max(0, 100 - p3["manipulation_score"]))

    # Pilier 4 — YouTube
    p4 = pillars.get("youtube")
    if p4 and p4.get("available") and p4.get("engagement_score") is not None:
        scores.append(p4["engagement_score"])

    # Pilier 5 — OSINT
    p5 = pillars.get("osint")
    if p5 and p5.get("available") and p5.get("reputation_score") is not None:
        scores.append(p5["reputation_score"])

    # Pilier 6 — AMF
    p6 = pillars.get("compliance")
    if p6 and p6.get("is_blacklisted") is not None:
        scores.append(0 if p6["is_blacklisted"] else 100)

    if not scores:
        return 50
    return round(sum(scores) / len(scores))


@router.post("/full", summary="Audit complet — 6 piliers de crédibilité")
async def full_audit(body: FullAuditRequest):
    """
    Lance tous les piliers disponibles en parallèle.
    Les piliers nécessitant une clé API non configurée retournent available=False
    sans bloquer les autres.
    """
    tasks = {}

    # Pilier 1 — Identité légale
    if body.entity_name or body.siren:
        tasks["legal_identity"] = check_legal_identity(
            entity_name=body.entity_name, siren=body.siren
        )

    # Pilier 2 — Partenariats (synchrone, pas de coroutine)
    partnership_result = None
    if body.text_to_analyze:
        partnership_result = check_partnership_transparency(body.text_to_analyze)

    # Pilier 3 — Discours
    if body.text_to_analyze:
        tasks["discourse"] = analyze_discourse(body.text_to_analyze)

    # Pilier 4 — YouTube
    if body.youtube_url or (body.url and "youtube" in (body.url or "").lower()):
        tasks["youtube"] = check_youtube_engagement(body.youtube_url or body.url)

    # Pilier 5 — OSINT
    if body.entity_name:
        tasks["osint"] = check_osint_reputation(body.entity_name)

    # Pilier 6 — Conformité AMF (synchrone, on l'enveloppe)
    async def _compliance():
        return check_compliance(
            url=body.url, entity_name=body.entity_name,
            sector=body.sector, siren=body.siren,
        )

    if body.entity_name or body.url:
        tasks["compliance"] = _compliance()

    # Exécution parallèle
    keys = list(tasks.keys())
    results_list = await asyncio.gather(*tasks.values(), return_exceptions=True)
    results = {k: v for k, v in zip(keys, results_list)}

    # Sérialisation
    pillars = {}
    for key, res in results.items():
        if isinstance(res, Exception):
            pillars[key] = {"error": str(res), "available": False}
        elif hasattr(res, "to_dict"):
            pillars[key] = res.to_dict()
        else:
            pillars[key] = res

    if partnership_result:
        pillars["partnerships"] = partnership_result.to_dict()

    score = _global_score(pillars)

    verdict = "fiable" if score >= 70 else "suspect" if score >= 40 else "alerte"

    return {
        "entity": {
            "name": body.entity_name,
            "siren": body.siren,
            "url": body.url,
            "sector": body.sector,
        },
        "global_score": score,
        "verdict": verdict,
        "pillars": pillars,
        "disclaimer": (
            "Cet audit est informatif et ne constitue pas un avis juridique. "
            "L'absence d'alerte ne garantit pas la fiabilité. "
            "Source : données publiques officielles."
        ),
    }
