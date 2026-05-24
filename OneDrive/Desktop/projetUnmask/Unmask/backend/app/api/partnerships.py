"""Route POST /audit/partnerships — Pilier 2."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.services.partnership_checker import check_partnership_transparency

router = APIRouter(prefix="/audit", tags=["Transparence Partenariats"])


class PartnershipRequest(BaseModel):
    text: str = Field(description="Texte à analyser (description, légende, bio...).", examples=["Mon code promo JEAN20 pour -20% ! 🚀"])
    entity_name: Optional[str] = Field(default=None, description="Nom de l'entité pour contextualiser.")


@router.post("/partnerships", summary="Vérifier la conformité loi influenceurs 2023")
def check_partnerships(body: PartnershipRequest):
    if not body.text or not body.text.strip():
        raise HTTPException(status_code=422, detail="Le champ 'text' est requis.")
    result = check_partnership_transparency(body.text)
    return result.to_dict()
