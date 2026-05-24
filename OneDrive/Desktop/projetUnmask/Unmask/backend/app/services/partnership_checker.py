"""
Pilier 2 — Transparence des partenariats (loi influenceurs 2023).

Analyse si le contenu d'un influenceur respecte les obligations de mention
imposées par la loi n°2023-451 du 9 juin 2023 (loi influenceurs).

Règles vérifiées :
- Mention "#sponsorisé", "#partenariat", "#publicité" ou équivalent
- Absence de promotion de produits financiers non réglementés
- Absence de promotion de chirurgie esthétique
- Absence de promotion de paris sportifs sans mention légale
"""

import re
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Patterns légaux (loi 2023-451)
# ---------------------------------------------------------------------------

_DISCLOSURE_PATTERNS = [
    r"#(?:sponsoris[eé]|partenariat|collaboration|publi[- ]?r[eé]dactionnel|publicite|pub\b|ad\b|sponsored|gifted)",
    r"\b(?:en partenariat avec|offert par|sponsoris[eé] par|en collaboration avec)\b",
]

_FORBIDDEN_FINANCE = [
    r"\b(?:forex|cfd|crypto(?:monnaie)?|trading|bitcoin|investissement garanti|rendement)\b",
    r"\b(?:copy.?trading|signal.?trading|formation trading)\b",
]

_FORBIDDEN_AESTHETIC = [
    r"\b(?:chirurgie|lip\s*filler|botox|rhinoplastie|liposuccion|augmentation mammaire)\b",
]

_GAMBLING_PATTERNS = [
    r"\b(?:paris sportifs?|bet365|winamax|betclic|unibet|pmu)\b",
]

_LEGAL_GAMBLING_MENTION = [
    r"\bjouez responsable\b",
    r"\binterdits? aux mineurs?\b",
    r"\bargj?\b",
]


@dataclass
class PartnershipFlag:
    rule: str
    severity: str  # "warning" | "violation"
    detail: str
    source: str = "Loi n°2023-451 du 9 juin 2023"
    source_url: str = "https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000047663185"

    def to_dict(self) -> dict:
        return {
            "rule": self.rule,
            "severity": self.severity,
            "detail": self.detail,
            "source": self.source,
            "source_url": self.source_url,
        }


@dataclass
class PartnershipResult:
    has_disclosure: bool
    flags: list[PartnershipFlag] = field(default_factory=list)
    score: int = 0  # 0-100, 100 = parfaitement conforme
    warning: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "has_disclosure": self.has_disclosure,
            "flags": [f.to_dict() for f in self.flags],
            "compliance_score": self.score,
            "warning": self.warning,
            "source": "Analyse automatique — Loi influenceurs 2023",
        }


# ---------------------------------------------------------------------------
# Logique d'analyse
# ---------------------------------------------------------------------------

def _match_any(text: str, patterns: list[str]) -> bool:
    t = text.lower()
    return any(re.search(p, t, re.IGNORECASE) for p in patterns)


def check_partnership_transparency(text: str) -> PartnershipResult:
    """
    Analyse un texte (description, caption, bio) pour détecter les violations
    de la loi influenceurs 2023.

    Args:
        text: Contenu textuel à analyser (description YouTube, légende Instagram, etc.)

    Returns:
        PartnershipResult avec les flags et un score de conformité.
    """
    if not text or not text.strip():
        return PartnershipResult(
            has_disclosure=False,
            warning="Aucun texte fourni pour l'analyse.",
            score=50,
        )

    flags: list[PartnershipFlag] = []

    # 1. Vérification mention partenariat
    has_disclosure = _match_any(text, _DISCLOSURE_PATTERNS)

    # 2. Promotion financière interdite sans agrément
    if _match_any(text, _FORBIDDEN_FINANCE):
        flags.append(PartnershipFlag(
            rule="Promotion produit financier",
            severity="violation",
            detail="Contenu potentiellement lié à la promotion de produits financiers non réglementés (trading, crypto, forex). Interdit sans agrément AMF.",
        ))

    # 3. Chirurgie esthétique
    if _match_any(text, _FORBIDDEN_AESTHETIC):
        flags.append(PartnershipFlag(
            rule="Promotion acte chirurgical",
            severity="violation",
            detail="Mention d'actes chirurgicaux ou de médecine esthétique. Promotion interdite par la loi 2023-451.",
        ))

    # 4. Paris sportifs sans mention légale
    if _match_any(text, _GAMBLING_PATTERNS):
        if not _match_any(text, _LEGAL_GAMBLING_MENTION):
            flags.append(PartnershipFlag(
                rule="Paris sportifs sans mention légale",
                severity="warning",
                detail="Promotion de paris sportifs sans les mentions obligatoires (\"Jouez responsable\", interdiction aux mineurs).",
            ))

    # 5. Contenu commercial sans disclosure
    commercial_signals = [
        r"\b(?:code promo|réduction|lien en bio|swipe up|utilisez mon code)\b",
        r"\b(?:offert|cadeau|gifted|c/o|courtesy of)\b",
    ]
    is_commercial = _match_any(text, commercial_signals)
    if is_commercial and not has_disclosure:
        flags.append(PartnershipFlag(
            rule="Partenariat commercial non déclaré",
            severity="violation",
            detail="Contenu commercial détecté (code promo, lien, cadeau) sans mention de partenariat (#sponsorisé, #publicité, etc.).",
        ))

    # Score de conformité
    deductions = sum(20 if f.severity == "violation" else 10 for f in flags)
    bonus = 10 if has_disclosure else 0
    score = max(0, min(100, 100 - deductions + bonus))

    return PartnershipResult(
        has_disclosure=has_disclosure,
        flags=flags,
        score=score,
    )
