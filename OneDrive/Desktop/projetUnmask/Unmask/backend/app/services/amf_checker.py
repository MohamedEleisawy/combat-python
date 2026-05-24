"""
Verification AMF/ACPR - Liste noire ABE Infoservice.

Ce module verifie si une entite (influenceur, marque, site) apparait
dans la liste noire officielle AMF/ACPR.

LIMITE CONNUE : La liste AMF recense des domaines, emails et noms de societes.
Elle ne contient PAS les noms/prenoms de personnes physiques. Un influenceur
agissant en nom propre (sans societe declaree) n'y sera donc generalement pas.

Source : https://www.abe-infoservice.fr/liste-noire
"""

import csv
import unicodedata
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Optional

_CSV_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "abeis-liste-noire.csv"


# ---------------------------------------------------------------------------
# Modele de donnees
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AmfMatch:
    """Une correspondance trouvee dans la liste noire AMF."""
    matched_on: str          # Ce qui a declenche le match : "url" ou "denomination"
    matched_value: str       # La valeur exacte trouvee dans le CSV
    categories: list[str]    # Ex. ["Forex"], ["Crypto-actifs"], ["Usurpation Autorites"]
    date_added: Optional[date]

    def to_dict(self) -> dict:
        return {
            "matched_on": self.matched_on,
            "matched_value": self.matched_value,
            "categories": self.categories,
            "date_added": self.date_added.isoformat() if self.date_added else None,
            "source": "ABE Infoservice (AMF/ACPR)",
            "source_url": "https://www.abe-infoservice.fr/liste-noire",
        }


@dataclass
class ComplianceResult:
    """Resultat complet de la verification AMF pour une entite."""
    is_blacklisted: bool
    matches: list[AmfMatch]
    checked: dict           # Ce qui a ete verifie (pour la transparence)
    warning: Optional[str]  # Avertissement si la verification est incomplete

    def to_dict(self) -> dict:
        return {
            "is_blacklisted": self.is_blacklisted,
            "matches": [m.to_dict() for m in self.matches],
            "checked": self.checked,
            "warning": self.warning,
        }


# ---------------------------------------------------------------------------
# Chargement du CSV
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Minuscules + suppression accents + suppression du prefixe www."""
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.removeprefix("www.")


def _extract_hostname(url_or_email: str) -> str:
    """
    Extrait le hostname depuis une URL ou un email.
    Exemples :
      "sites.google.com/arnaque" -> "sites.google.com"
      "contact@fafinancesarl.com" -> "fafinancesarl.com"
    """
    text = _normalize(url_or_email)
    if "@" in text:
        text = text.split("@")[-1]
    return text.split("/")[0].split("?")[0]


def _parse_date(raw: str) -> Optional[date]:
    """Parse une date JJ/MM/AAAA. Retourne None si invalide."""
    try:
        day, month, year = raw.strip().split("/")
        return date(int(year), int(month), int(day))
    except (ValueError, AttributeError):
        return None


@lru_cache(maxsize=1)
def _load_blacklist() -> list[dict]:
    """
    Charge le CSV une seule fois en memoire (cache LRU).
    Chaque entree est un dict brut : {hostname, denomination, categories, date_added}.
    """
    if not _CSV_PATH.exists():
        raise FileNotFoundError(
            f"Fichier AMF introuvable : {_CSV_PATH}\n"
            "Telechargez-le sur https://www.abe-infoservice.fr/liste-noire"
        )

    entries = []
    with open(_CSV_PATH, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            raw_url = row.get("URL / Mails", "").strip()
            raw_cats = row.get("Catégorie(s)", "") or ""
            entries.append({
                "hostname": _extract_hostname(raw_url),
                "denomination": _normalize(row.get("Dénomination", "").strip()),
                "raw_value": raw_url,
                "categories": [c.strip() for c in raw_cats.split(",") if c.strip()],
                "date_added": _parse_date(row.get("Date d'inscription", "")),
            })
    return entries


# ---------------------------------------------------------------------------
# Fonction principale
# ---------------------------------------------------------------------------

def check_compliance(
    url: Optional[str] = None,
    entity_name: Optional[str] = None,
    sector: Optional[str] = None,
    siren: Optional[str] = None,
) -> ComplianceResult:
    """
    Verifie une entite contre la liste noire AMF/ACPR.

    Args:
        url         : INPUT_1 - URL ou profil reseau social de l'entite.
        entity_name : INPUT_2 - Nom public de la personne ou de la marque.
        sector      : INPUT_3 - Secteur declare ("finance", "coaching", etc.)
                      Si le secteur est non-financier (lifestyle, sport...),
                      un avertissement l'indique car la liste AMF est moins pertinente.
        siren       : INPUT_4 - SIREN optionnel. Non present dans le fichier AMF,
                      ce champ est reserve pour la verification data.gouv.fr (pilier 1).

    Returns:
        ComplianceResult avec tous les matches et les champs verifies.
    """
    blacklist = _load_blacklist()
    matches: list[AmfMatch] = []

    # -- Verification via URL (INPUT_1) --
    query_hostname = _extract_hostname(url) if url else None
    if query_hostname:
        for entry in blacklist:
            if entry["hostname"] == query_hostname:
                matches.append(AmfMatch(
                    matched_on="url",
                    matched_value=entry["raw_value"],
                    categories=entry["categories"],
                    date_added=entry["date_added"],
                ))

    # -- Verification via nom d'entite (INPUT_2) --
    # Fonctionne uniquement pour les societes (pas les personnes physiques)
    query_name = _normalize(entity_name) if entity_name else None
    if query_name:
        for entry in blacklist:
            if entry["denomination"] and query_name in entry["denomination"]:
                # Eviter les doublons si l'URL a deja matche la meme entree
                already_matched = any(m.matched_value == entry["raw_value"] for m in matches)
                if not already_matched:
                    matches.append(AmfMatch(
                        matched_on="denomination",
                        matched_value=entry["raw_value"],
                        categories=entry["categories"],
                        date_added=entry["date_added"],
                    ))

    # -- Avertissement contextuel selon le secteur (INPUT_3) --
    financial_sectors = {"finance", "crypto", "forex", "investissement", "trading", "placement"}
    is_financial = sector and any(s in _normalize(sector) for s in financial_sectors)

    warning = None
    if not url and not entity_name:
        warning = "Aucune donnee fournie pour la verification AMF."
    elif not is_financial and sector:
        warning = (
            f"Secteur '{sector}' non-financier : la liste noire AMF est principalement "
            "destinee aux escroqueries financieres. L'absence de resultat ne garantit pas la fiabilite."
        )
    elif entity_name and not url:
        warning = (
            "La liste AMF ne recense pas les personnes physiques par leur nom. "
            "La recherche par nom ne fonctionne que pour les societes declarees."
        )

    # SIREN note (INPUT_4 - non verifiable ici)
    checked = {
        "url_checked": query_hostname,
        "entity_name_checked": query_name,
        "sector": sector,
        "siren_note": "SIREN absent de la liste AMF - a verifier via data.gouv.fr (pilier Identite Legale)" if siren else None,
    }

    return ComplianceResult(
        is_blacklisted=len(matches) > 0,
        matches=matches,
        checked=checked,
        warning=warning,
    )
