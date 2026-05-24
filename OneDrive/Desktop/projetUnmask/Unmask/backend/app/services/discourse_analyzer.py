"""
Pilier 3 — Analyse du discours par LLM (Claude API).

Détecte les signaux de manipulation rhétorique, FOMO, fausses promesses,
et langage de secte dans les contenus textuels.

Requiert : ANTHROPIC_API_KEY dans .env
"""

import json
from dataclasses import dataclass, field
from typing import Optional

from app.config import ANTHROPIC_API_KEY

_MODEL = "claude-haiku-4-5-20251001"

_SYSTEM_PROMPT = """Tu es un expert en détection de manipulation rhétorique et de désinformation.
Analyse le texte fourni et retourne UNIQUEMENT un JSON valide avec cette structure exacte :
{
  "manipulation_score": <0-100>,
  "signals": [
    {"type": "<type>", "quote": "<extrait exact>", "explanation": "<explication courte>"}
  ],
  "summary": "<résumé en 1-2 phrases>",
  "verdict": "safe" | "suspicious" | "manipulative"
}

Types de signaux à détecter :
- "fomo" : Urgence artificielle, rareté fabriquée ("dernière chance", "offre limitée")
- "false_promise" : Promesses de revenus garantis, résultats irréalistes
- "social_proof_fake" : Faux témoignages, statistiques invérifiables
- "authority_claim" : Fausses expertises, certifications non vérifiables
- "cult_language" : Langage sectaire, communauté fermée, "les autres ne comprennent pas"
- "fear" : Exploitation de la peur (perdre de l'argent, rater sa vie)
- "price_anchor" : Manipulation par ancrage de prix
- "forbidden_sector" : Promotion de secteurs réglementés sans agrément

Sois factuel et précis. Si le texte est banal et sans signal, retourne manipulation_score: 0 et signals: [].
"""


@dataclass
class DiscourseSignal:
    type: str
    quote: str
    explanation: str

    def to_dict(self) -> dict:
        return {"type": self.type, "quote": self.quote, "explanation": self.explanation}


@dataclass
class DiscourseResult:
    manipulation_score: int
    signals: list[DiscourseSignal] = field(default_factory=list)
    summary: str = ""
    verdict: str = "safe"
    warning: Optional[str] = None
    available: bool = True

    def to_dict(self) -> dict:
        return {
            "manipulation_score": self.manipulation_score,
            "signals": [s.to_dict() for s in self.signals],
            "summary": self.summary,
            "verdict": self.verdict,
            "warning": self.warning,
            "available": self.available,
        }


async def analyze_discourse(text: str) -> DiscourseResult:
    """
    Analyse un texte via Claude pour détecter les signaux de manipulation.

    Args:
        text: Contenu textuel à analyser (max ~4000 mots).

    Returns:
        DiscourseResult avec score, signaux et verdict.
    """
    if not ANTHROPIC_API_KEY:
        return DiscourseResult(
            manipulation_score=0,
            summary="",
            verdict="safe",
            warning="Clé ANTHROPIC_API_KEY non configurée. Analyse du discours indisponible.",
            available=False,
        )

    if not text or not text.strip():
        return DiscourseResult(
            manipulation_score=0,
            summary="Aucun texte fourni.",
            verdict="safe",
        )

    # Tronquer à ~3000 mots pour rester dans les limites raisonnables
    words = text.split()
    if len(words) > 3000:
        text = " ".join(words[:3000]) + "\n[...texte tronqué]"

    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        message = await client.messages.create(
            model=_MODEL,
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Analyse ce texte :\n\n{text}"}],
        )

        raw = message.content[0].text.strip()
        # Extraire le JSON même si le modèle ajoute du texte autour
        start = raw.find("{")
        end = raw.rfind("}") + 1
        data = json.loads(raw[start:end])

        signals = [
            DiscourseSignal(
                type=s.get("type", ""),
                quote=s.get("quote", ""),
                explanation=s.get("explanation", ""),
            )
            for s in data.get("signals", [])
        ]

        return DiscourseResult(
            manipulation_score=int(data.get("manipulation_score", 0)),
            signals=signals,
            summary=data.get("summary", ""),
            verdict=data.get("verdict", "safe"),
        )

    except Exception as e:
        return DiscourseResult(
            manipulation_score=0,
            summary="",
            verdict="safe",
            warning=f"Erreur lors de l'analyse : {type(e).__name__}",
            available=False,
        )
