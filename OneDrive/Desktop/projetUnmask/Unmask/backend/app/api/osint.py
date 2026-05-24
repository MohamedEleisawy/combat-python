"""Route POST /audit/osint — Pilier 5."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.osint_checker import check_osint_reputation

router = APIRouter(prefix="/audit", tags=["Réputation OSINT"])


class OsintRequest(BaseModel):
    entity_name: str = Field(description="Nom public de l'entité à rechercher.", examples=["Jean Trader"])


@router.post("/osint", summary="Recherche OSINT — réputation externe et signalements")
async def osint_audit(body: OsintRequest):
    if not body.entity_name or not body.entity_name.strip():
        raise HTTPException(status_code=422, detail="Le champ 'entity_name' est requis.")
    result = await check_osint_reputation(body.entity_name.strip())
    return result.to_dict()
