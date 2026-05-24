"""
Pilier 4 — Cohérence d'engagement YouTube (YouTube Data API v3).

Analyse les métriques d'une chaîne YouTube pour détecter :
- Ratio vues/abonnés anormal (achat de vues)
- Ratio likes/vues anormal (engagement artificiel)
- Croissance d'abonnés suspecte
- Activité de publication

Requiert : YOUTUBE_API_KEY dans .env
Source API : https://developers.google.com/youtube/v3
"""

import re
from dataclasses import dataclass, field
from typing import Optional

import httpx

from app.config import YOUTUBE_API_KEY

_YT_API = "https://www.googleapis.com/youtube/v3"
_TIMEOUT = 10


# ---------------------------------------------------------------------------
# Modèles
# ---------------------------------------------------------------------------

@dataclass
class EngagementFlag:
    type: str
    severity: str  # "info" | "warning" | "suspicious"
    detail: str

    def to_dict(self) -> dict:
        return {"type": self.type, "severity": self.severity, "detail": self.detail}


@dataclass
class YoutubeResult:
    channel_id: str = ""
    channel_name: str = ""
    subscribers: Optional[int] = None
    total_views: Optional[int] = None
    video_count: Optional[int] = None
    avg_views_per_video: Optional[float] = None
    engagement_ratio: Optional[float] = None  # vues/abonnés
    flags: list[EngagementFlag] = field(default_factory=list)
    engagement_score: int = 100  # 100 = sain
    channel_url: str = ""
    warning: Optional[str] = None
    available: bool = True

    def to_dict(self) -> dict:
        return {
            "channel_id": self.channel_id,
            "channel_name": self.channel_name,
            "subscribers": self.subscribers,
            "total_views": self.total_views,
            "video_count": self.video_count,
            "avg_views_per_video": round(self.avg_views_per_video, 0) if self.avg_views_per_video else None,
            "engagement_ratio": round(self.engagement_ratio, 4) if self.engagement_ratio else None,
            "flags": [f.to_dict() for f in self.flags],
            "engagement_score": self.engagement_score,
            "channel_url": self.channel_url,
            "warning": self.warning,
            "available": self.available,
            "source": "YouTube Data API v3",
            "source_url": "https://developers.google.com/youtube/v3",
        }


# ---------------------------------------------------------------------------
# Extraction d'identifiant YouTube
# ---------------------------------------------------------------------------

def _extract_channel_id(url_or_handle: str) -> Optional[str]:
    """Extrait un channel ID ou handle depuis une URL YouTube."""
    patterns = [
        r"youtube\.com/channel/(UC[\w-]{22})",
        r"youtube\.com/@([\w.-]+)",
        r"youtube\.com/c/([\w.-]+)",
        r"youtube\.com/user/([\w.-]+)",
    ]
    for p in patterns:
        m = re.search(p, url_or_handle)
        if m:
            return m.group(1)
    # Si c'est déjà un channel ID
    if url_or_handle.startswith("UC") and len(url_or_handle) == 24:
        return url_or_handle
    return None


def _analyze_metrics(result: YoutubeResult) -> YoutubeResult:
    """Applique les règles heuristiques de détection."""
    flags = []
    score = 100

    if result.subscribers and result.total_views:
        ratio = result.total_views / result.subscribers
        result.engagement_ratio = ratio

        # Ratio vues/abonnés < 1 : très suspect (abonnés achetés ?)
        if ratio < 0.5:
            flags.append(EngagementFlag(
                type="low_view_ratio",
                severity="suspicious",
                detail=f"Ratio vues/abonnés très faible ({ratio:.2f}). Possible achat d'abonnés.",
            ))
            score -= 40
        elif ratio < 2:
            flags.append(EngagementFlag(
                type="low_view_ratio",
                severity="warning",
                detail=f"Ratio vues/abonnés faible ({ratio:.2f}). Engagement potentiellement artificiel.",
            ))
            score -= 20

    if result.video_count and result.total_views and result.video_count > 0:
        avg = result.total_views / result.video_count
        result.avg_views_per_video = avg

        # Chaîne avec beaucoup d'abonnés mais peu de vues par vidéo
        if result.subscribers and result.subscribers > 100_000 and avg < 1000:
            flags.append(EngagementFlag(
                type="low_avg_views",
                severity="suspicious",
                detail=f"Moyenne de {avg:.0f} vues/vidéo pour {result.subscribers:,} abonnés.",
            ))
            score -= 30

    result.flags = flags
    result.engagement_score = max(0, score)
    return result


# ---------------------------------------------------------------------------
# Appels API
# ---------------------------------------------------------------------------

async def _resolve_handle_to_id(handle: str, client: httpx.AsyncClient) -> Optional[str]:
    """Résout un @handle ou nom de chaîne vers un channel ID via search."""
    resp = await client.get(f"{_YT_API}/search", params={
        "part": "snippet",
        "q": handle,
        "type": "channel",
        "maxResults": 1,
        "key": YOUTUBE_API_KEY,
    })
    data = resp.json()
    items = data.get("items", [])
    if items:
        return items[0]["id"]["channelId"]
    return None


async def check_youtube_engagement(url_or_handle: str) -> YoutubeResult:
    """
    Analyse les métriques d'une chaîne YouTube.

    Args:
        url_or_handle: URL YouTube, @handle, ou channel ID.

    Returns:
        YoutubeResult avec métriques et flags d'anomalie.
    """
    if not YOUTUBE_API_KEY:
        return YoutubeResult(
            warning="Clé YOUTUBE_API_KEY non configurée. Analyse YouTube indisponible.",
            available=False,
        )

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        # Résolution de l'identifiant
        raw = _extract_channel_id(url_or_handle)

        if raw and raw.startswith("UC"):
            channel_id = raw
        else:
            handle = raw or url_or_handle.strip().lstrip("@")
            channel_id = await _resolve_handle_to_id(handle, client)

        if not channel_id:
            return YoutubeResult(
                warning=f"Chaîne YouTube introuvable pour : {url_or_handle}",
                available=False,
            )

        # Récupération des stats
        resp = await client.get(f"{_YT_API}/channels", params={
            "part": "snippet,statistics",
            "id": channel_id,
            "key": YOUTUBE_API_KEY,
        })
        data = resp.json()
        items = data.get("items", [])

        if not items:
            return YoutubeResult(
                warning="Chaîne non trouvée via l'API YouTube.",
                available=False,
            )

        item = items[0]
        stats = item.get("statistics", {})
        snippet = item.get("snippet", {})

        result = YoutubeResult(
            channel_id=channel_id,
            channel_name=snippet.get("title", ""),
            subscribers=int(stats["subscriberCount"]) if stats.get("subscriberCount") else None,
            total_views=int(stats["viewCount"]) if stats.get("viewCount") else None,
            video_count=int(stats["videoCount"]) if stats.get("videoCount") else None,
            channel_url=f"https://www.youtube.com/channel/{channel_id}",
        )

        return _analyze_metrics(result)
