"""
Endpoint FastAPI - Verification de conformite institutionnelle AMF/ACPR.

Route : POST /audit/compliance
Ce router expose la verification de la liste noire ABE Infoservice
a partir des 4 inputs standardises du protocole d'audit Unmask.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.services.amf_checker import check_compliance

router = APIRouter(prefix="/audit", tags=["Conformite AMF/ACPR"])


# ---------------------------------------------------------------------------
# Schemas de requete / reponse (Pydantic)
# ---------------------------------------------------------------------------

class ComplianceRequest(BaseModel):
    """Corps de la requete POST /audit/compliance."""

    url: Optional[str] = Field(
        default=None,
        description="INPUT_1 - URL ou nom de profil reseau social de l'entite auditee.",
        examples=["tellidex.io", "https://instagram.com/john_trader"],
    )
    entity_name: Optional[str] = Field(
        default=None,
        description="INPUT_2 - Nom public de la personne ou de la marque.",
        examples=["John Trader", "CREVALUS"],
    )
    sector: Optional[str] = Field(
        default=None,
        description="INPUT_3 - Secteur declare ou infere (finance / coaching / e-commerce / lifestyle / autre).",
        examples=["finance", "lifestyle"],
    )
    siren: Optional[str] = Field(
        default=None,
        description="INPUT_4 - Numero SIREN optionnel (non verifiable via AMF, reserve pour data.gouv.fr).",
        examples=["123456789"],
    )


class ComplianceResponse(BaseModel):
    """Reponse structuree de la verification AMF."""

    is_blacklisted: bool = Field(
        description="True si l'entite figure dans la liste noire AMF/ACPR."
    )
    matches: list[dict] = Field(
        description="Liste des entrees correspondantes avec leur source et categories."
    )
    checked: dict = Field(
        description="Recapitulatif des champs verifies (transparence de l'audit)."
    )
    warning: Optional[str] = Field(
        default=None,
        description="Avertissement si la verification est incomplete ou non pertinente."
    )


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post(
    "/compliance",
    response_model=ComplianceResponse,
    summary="Verifier une entite contre la liste noire AMF/ACPR",
    description=(
        "Verifie si l'entite fournie (URL, nom, secteur) figure dans la liste noire "
        "officielle ABE Infoservice (AMF + ACPR). "
        "Retourne les correspondances trouvees avec leur source officielle."
    ),
)
def check_entity_compliance(body: ComplianceRequest) -> ComplianceResponse:
    """
    Verification de conformite institutionnelle.

    - Recherche par URL/domaine (INPUT_1)
    - Recherche par nom de societe (INPUT_2) - ne couvre pas les personnes physiques
    - Avertissement contextuel si secteur non-financier (INPUT_3)
    - SIREN note comme a verifier via data.gouv.fr (INPUT_4)
    """
    # Validation : au moins un champ doit etre fourni
    if not body.url and not body.entity_name:
        raise HTTPException(
            status_code=422,
            detail="Fournissez au moins un champ : 'url' ou 'entity_name'.",
        )

    result = check_compliance(
        url=body.url,
        entity_name=body.entity_name,
        sector=body.sector,
        siren=body.siren,
    )

    return ComplianceResponse(**result.to_dict())
