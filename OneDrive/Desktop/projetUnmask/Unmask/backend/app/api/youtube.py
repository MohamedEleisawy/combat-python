"""Route POST /audit/youtube — Pilier 4."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.youtube_checker import check_youtube_engagement

router = APIRouter(prefix="/audit", tags=["Engagement YouTube"])


class YoutubeRequest(BaseModel):
    url: str = Field(description="URL YouTube, @handle ou channel ID.", examples=["https://www.youtube.com/@MrBeast"])


@router.post("/youtube", summary="Analyser la cohérence d'engagement d'une chaîne YouTube")
async def youtube_audit(body: YoutubeRequest):
    if not body.url or not body.url.strip():
        raise HTTPException(status_code=422, detail="Le champ 'url' est requis.")
    result = await check_youtube_engagement(body.url.strip())
    return result.to_dict()
