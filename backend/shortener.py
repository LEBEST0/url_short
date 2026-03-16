import random
import string

from sqlalchemy.orm import Session

from database import URL

# Alphabet base62 : chiffres + lettres minuscules + majuscules
ALPHABET = string.digits + string.ascii_letters
CODE_LENGTH = 6


def generate_code() -> str:
    """Génère un code aléatoire de 6 caractères en base62."""
    return "".join(random.choices(ALPHABET, k=CODE_LENGTH))


def get_unique_code(db: Session) -> str:
    """
    Génère un code unique en vérifiant qu'il n'existe pas déjà en base.
    En pratique, les collisions sont rarissimes (62^6 = ~56 milliards de combinaisons).
    """
    for _ in range(10):  # 10 tentatives max par sécurité
        code = generate_code()
        existing = db.query(URL).filter(URL.code == code).first()
        if not existing:
            return code
    raise RuntimeError("Impossible de générer un code unique après 10 tentatives.")


def create_short_url(db: Session, original_url: str) -> URL:
    """
    Crée et persiste une nouvelle URL courte.
    Si l'URL originale existe déjà, retourne l'entrée existante.
    """
    # Évite les doublons : si l'URL existe déjà, on retourne le même code
    existing = db.query(URL).filter(URL.original == original_url).first()
    if existing:
        return existing

    code = get_unique_code(db)
    url_entry = URL(code=code, original=original_url)
    db.add(url_entry)
    db.commit()
    db.refresh(url_entry)
    return url_entry


def get_url_by_code(db: Session, code: str) -> URL | None:
    """Récupère une entrée URL par son code court."""
    return db.query(URL).filter(URL.code == code).first()


def increment_clicks(db: Session, url_entry: URL) -> None:
    """Incrémente le compteur de clics d'une URL."""
    url_entry.clicks += 1
    db.commit()
