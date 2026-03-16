import httpx

from pyshort.config import get_api_url


def shorten(url: str) -> dict:
    """
    Appelle POST /shorten et retourne le dict de réponse.
    Lève une exception httpx en cas d'erreur réseau ou HTTP.
    """
    api_url = get_api_url()
    response = httpx.post(
        f"{api_url}/shorten",
        json={"url": url},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def stats(code: str) -> dict:
    """
    Appelle GET /stats/{code} et retourne le dict de réponse.
    """
    api_url = get_api_url()
    response = httpx.get(
        f"{api_url}/stats/{code}",
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
