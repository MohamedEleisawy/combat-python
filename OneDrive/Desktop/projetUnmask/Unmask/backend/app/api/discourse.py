"""Route POST /audit/discourse — Pilier 3."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.discourse_analyzer import analyze_discourse

router = APIRouter(prefix="/audit", tags=["Analyse du Discours"])


class DiscourseRequest(BaseModel):
    text: str = Field(description="Texte à analyser pour détecter la manipulation.", examples=["Rejoignez ma formation et gagnez 5000€/mois garanti !"])


@router.post("/discourse", summary="Analyser un texte pour détecter la manipulation (LLM)")
async def analyze_discourse_route(body: DiscourseRequest):
    if not body.text or not body.text.strip():
        raise HTTPException(status_code=422, detail="Le champ 'text' est requis.")
    result = await analyze_discourse(body.text)
    return result.to_dict()
