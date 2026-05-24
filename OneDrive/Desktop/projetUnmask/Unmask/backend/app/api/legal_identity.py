"""
Endpoint FastAPI - Verification d'identite legale via data.gouv.fr.

Route : POST /audit/legal-identity
Verifie si une entite possede une existence juridique declaree en France
via l'Annuaire des Entreprises (anciennement Annuaire des Entreprises INSEE/INPI).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.services.siren_checker import check_legal_identity

router = APIRouter(prefix="/audit", tags=["Identite Legale"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class LegalIdentityRequest(BaseModel):
    """Corps de la requete POST /audit/legal-identity."""

    entity_name: Optional[str] = Field(
        default=None,
        description="INPUT_2 - Nom public de la personne ou de la marque.",
        examples=["Carrefour", "Jean Dupont Coaching"],
    )
    siren: Optional[str] = Field(
        default=None,
        description="INPUT_4 - Numero SIREN a 9 chiffres (prioritaire sur entity_name).",
        examples=["503932568"],
    )


class LegalIdentityResponse(BaseModel):
    """Reponse de la verification d'identite legale."""

    found: bool = Field(description="True si l'entite existe dans le registre officiel.")
    identity: Optional[dict] = Field(default=None, description="Donnees legales si trouvee.")
    query_used: str = Field(description="Parametre utilise pour la recherche.")
    warning: Optional[str] = Field(default=None, description="Avertissement contextuel.")


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post(
    "/legal-identity",
    response_model=LegalIdentityResponse,
    summary="Verifier l'existence legale d'une entite (SIREN / data.gouv.fr)",
    description=(
        "Interroge l'Annuaire des Entreprises (data.gouv.fr) pour verifier "
        "si une entite est juridiquement declaree et active en France. "
        "Fournir un SIREN donne un resultat plus precis qu'une recherche par nom."
    ),
)
async def verify_legal_identity(body: LegalIdentityRequest) -> LegalIdentityResponse:
    """
    Verification d'identite legale.

    - Recherche par SIREN (INPUT_4) si fourni - plus precis
    - Recherche par nom d'entite (INPUT_2) sinon
    """
    if not body.entity_name and not body.siren:
        raise HTTPException(
            status_code=422,
            detail="Fournissez au moins un champ : 'entity_name' ou 'siren'.",
        )

    result = await check_legal_identity(
        entity_name=body.entity_name,
        siren=body.siren,
    )

    return LegalIdentityResponse(**result.to_dict())
