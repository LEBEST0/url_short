from datetime import datetime

from pydantic import BaseModel, HttpUrl


class ShortenRequest(BaseModel):
    """Corps de la requête POST /shorten"""
    url: HttpUrl


class ShortenResponse(BaseModel):
    """Réponse après création d'une URL courte"""
    short: str
    code: str
    original: str


class StatsResponse(BaseModel):
    """Réponse de GET /stats/{code}"""
    code: str
    original: str
    short: str
    clicks: int
    created_at: datetime
