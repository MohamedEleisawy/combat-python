"""
Service de verification d'identite legale via l'API data.gouv.fr.

Utilise l'API Recherche Entreprises (recherche-entreprises.api.gouv.fr)
pour verifier si une entite possede une existence legale declaree en France.

Pas de cle API requise - API publique et gratuite.
Source : https://recherche-entreprises.api.gouv.fr
"""

import httpx
from dataclasses import dataclass
from typing import Optional

_API_BASE = "https://recherche-entreprises.api.gouv.fr/search"
_TIMEOUT = 8  # secondes


# ---------------------------------------------------------------------------
# Modele de donnees
# ---------------------------------------------------------------------------

@dataclass
class LegalIdentity:
    """Informations legales d'une entite trouvee sur data.gouv.fr."""

    siren: str
    nom: str
    est_actif: bool              # True si etat_administratif == "A"
    date_creation: Optional[str]
    date_fermeture: Optional[str]
    forme_juridique: Optional[str]
    adresse: Optional[str]
    est_entrepreneur_individuel: bool
    source_url: str

    def to_dict(self) -> dict:
        return {
            "siren": self.siren,
            "nom": self.nom,
            "est_actif": self.est_actif,
            "date_creation": self.date_creation,
            "date_fermeture": self.date_fermeture,
            "forme_juridique": self.forme_juridique,
            "adresse": self.adresse,
            "est_entrepreneur_individuel": self.est_entrepreneur_individuel,
            "source": "Annuaire des Entreprises (data.gouv.fr)",
            "source_url": self.source_url,
        }


@dataclass
class LegalCheckResult:
    """Resultat complet de la verification d'identite legale."""

    found: bool                       # L'entite existe-t-elle dans le registre ?
    identity: Optional[LegalIdentity] # Donnees si trouvee
    query_used: str                    # Ce qui a ete recherche (transparence)
    warning: Optional[str]

    def to_dict(self) -> dict:
        return {
            "found": self.found,
            "identity": self.identity.to_dict() if self.identity else None,
            "query_used": self.query_used,
            "warning": self.warning,
        }


# ---------------------------------------------------------------------------
# Mapping des codes nature juridique (les plus courants)
# ---------------------------------------------------------------------------

_NATURE_JURIDIQUE = {
    "1000": "Entrepreneur individuel",
    "5499": "Societe a responsabilite limitee (SARL)",
    "5710": "Societe anonyme (SA)",
    "5720": "Societe par actions simplifiee (SAS)",
    "5800": "Societe en commandite",
    "6317": "Association loi 1901",
    "9110": "Etablissement public",
    "9220": "Commune",
}

def _libelle_nature_juridique(code: Optional[str]) -> Optional[str]:
    """Traduit un code nature juridique en libelle lisible."""
    if not code:
        return None
    return _NATURE_JURIDIQUE.get(code, f"Code {code}")


# ---------------------------------------------------------------------------
# Appel API
# ---------------------------------------------------------------------------

def _parse_result(data: dict, query: str) -> LegalIdentity:
    """Extrait les champs utiles d'un resultat brut de l'API."""
    siege = data.get("siege") or {}
    complements = data.get("complements") or {}
    siren = data.get("siren", "")

    return LegalIdentity(
        siren=siren,
        nom=data.get("nom_complet") or data.get("nom_raison_sociale", ""),
        est_actif=data.get("etat_administratif") == "A",
        date_creation=data.get("date_creation"),
        date_fermeture=data.get("date_fermeture"),
        forme_juridique=_libelle_nature_juridique(data.get("nature_juridique")),
        adresse=siege.get("adresse"),
        est_entrepreneur_individuel=complements.get("est_entrepreneur_individuel", False),
        source_url=f"https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}",
    )


async def check_legal_identity(
    entity_name: Optional[str] = None,
    siren: Optional[str] = None,
) -> LegalCheckResult:
    """
    Verifie l'identite legale d'une entite via l'API data.gouv.fr.

    Priorite : si un SIREN est fourni (INPUT_4), on cherche par SIREN.
    Sinon, on cherche par nom d'entite (INPUT_2).

    Args:
        entity_name : Nom public de la personne ou marque (INPUT_2).
        siren       : Numero SIREN a 9 chiffres (INPUT_4).

    Returns:
        LegalCheckResult indiquant si l'entite est enregistree et active.
    """
    # Choix de la requete : SIREN en priorite car plus precis
    if siren:
        query = siren.strip().replace(" ", "")
    elif entity_name:
        query = entity_name.strip()
    else:
        return LegalCheckResult(
            found=False,
            identity=None,
            query_used="",
            warning="Aucun parametre fourni (entity_name ou siren requis).",
        )

    # Appel API asynchrone
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.get(_API_BASE, params={"q": query, "per_page": 1})
        response.raise_for_status()
        data = response.json()

    results = data.get("results", [])

    # Aucun resultat
    if not results:
        warning = None
        if not siren:
            warning = (
                "Aucune societe trouvee pour ce nom. "
                "Les personnes physiques sans structure juridique ne sont pas dans ce registre."
            )
        return LegalCheckResult(found=False, identity=None, query_used=query, warning=warning)

    # On prend le premier resultat (le plus pertinent selon l'API)
    identity = _parse_result(results[0], query)

    # Avertissement si la societe est fermee
    warning = None
    if not identity.est_actif:
        warning = f"La societe '{identity.nom}' existe dans le registre mais est fermee (radiation)."

    return LegalCheckResult(found=True, identity=identity, query_used=query, warning=warning)
