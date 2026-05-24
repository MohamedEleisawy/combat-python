"""Configuration centralisée — lit les variables d'environnement."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
GOOGLE_CSE_API_KEY: str = os.getenv("GOOGLE_CSE_API_KEY", "")
GOOGLE_CSE_ID: str = os.getenv("GOOGLE_CSE_ID", "")
SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")
