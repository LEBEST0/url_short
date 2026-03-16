from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session

from config import settings
from database import get_db, init_db
from models import ShortenRequest, ShortenResponse, StatsResponse
from shortener import create_short_url, get_url_by_code, increment_clicks

app = FastAPI(
    title="URL Shortener API",
    description="Raccourcissez vos URLs via CLI ou extension navigateur.",
    version="1.0.0",
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    msg = errors[0].get("msg", "URL invalide") if errors else "URL invalide"
    return JSONResponse(
        status_code=422,
        content={"detail": f"URL invalide : {msg}"},
    )

# CORS : autorise l'extension navigateur et les appels locaux
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Initialise la base de données au démarrage."""
    init_db()


# ─────────────────────────────────────────────
#  POST /shorten  — Crée une URL courte
# ─────────────────────────────────────────────
@app.post("/shorten", response_model=ShortenResponse, status_code=201)
def shorten_url(payload: ShortenRequest, db: Session = Depends(get_db)):
    original = str(payload.url)
    url_entry = create_short_url(db, original)
    short = f"{settings.base_url}/{url_entry.code}"
    return ShortenResponse(
        short=short,
        code=url_entry.code,
        original=original,
    )


# ─────────────────────────────────────────────
#  GET /{code}  — Redirige vers l'URL originale
# ─────────────────────────────────────────────
@app.get("/{code}")
def redirect_to_original(code: str, db: Session = Depends(get_db)):
    url_entry = get_url_by_code(db, code)
    if not url_entry:
        raise HTTPException(status_code=404, detail=f"Code '{code}' introuvable.")
    increment_clicks(db, url_entry)
    return RedirectResponse(url=url_entry.original, status_code=301)


# ─────────────────────────────────────────────
#  GET /stats/{code}  — Statistiques d'une URL
# ─────────────────────────────────────────────
@app.get("/stats/{code}", response_model=StatsResponse)
def get_stats(code: str, db: Session = Depends(get_db)):
    url_entry = get_url_by_code(db, code)
    if not url_entry:
        raise HTTPException(status_code=404, detail=f"Code '{code}' introuvable.")
    short = f"{settings.base_url}/{url_entry.code}"
    return StatsResponse(
        code=url_entry.code,
        original=url_entry.original,
        short=short,
        clicks=url_entry.clicks,
        created_at=url_entry.created_at,
    )