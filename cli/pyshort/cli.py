from typing import Optional

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pyshort import __version__
from pyshort.api import shorten as api_shorten
from pyshort.api import stats as api_stats
from pyshort.config import get_api_url, save_api_url

app = typer.Typer(
    name="pyshort",
    help="🔗 Raccourcissez vos URLs directement depuis le terminal.",
    add_completion=False,
)

console = Console()


def _try_copy(text: str) -> bool:
    """Tente de copier le texte dans le presse-papier. Retourne True si succès."""
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────
#  pyshort shorten <url>
# ─────────────────────────────────────────────
@app.command()
def shorten(
    url: str = typer.Argument(..., help="L'URL longue à raccourcir."),
    no_copy: bool = typer.Option(False, "--no-copy", help="Ne pas copier dans le presse-papier."),
):
    """Raccourcit une URL et copie le résultat dans le presse-papier."""
    with console.status("[bold cyan]Raccourcissement en cours…[/]"):
        try:
            data = api_shorten(url)
        except httpx.HTTPStatusError as e:
            console.print(f"[bold red]Erreur HTTP {e.response.status_code}[/] : {e.response.text}")
            raise typer.Exit(1)
        except httpx.RequestError:
            api = get_api_url()
            console.print(f"[bold red]Impossible de joindre l'API[/] ({api})")
            console.print("💡 Vérifiez que le serveur tourne ou configurez l'URL avec [bold]pyshort config[/]")
            raise typer.Exit(1)

    short_url = data["short"]

    copied = False
    if not no_copy:
        copied = _try_copy(short_url)

    panel_content = f"[bold green]{short_url}[/]"
    if copied:
        panel_content += "\n[dim]✅ Copié dans le presse-papier[/]"

    console.print(Panel(panel_content, title="🔗 URL raccourcie", border_style="green"))


# ─────────────────────────────────────────────
#  pyshort stats <code>
# ─────────────────────────────────────────────
@app.command()
def stats(
    code: str = typer.Argument(..., help="Le code court (ex: abc12x) ou l'URL courte complète."),
):
    """Affiche les statistiques d'une URL raccourcie."""
    # Accepte aussi bien "abc12x" que "https://shr.ty/abc12x"
    if "/" in code:
        code = code.rstrip("/").split("/")[-1]

    with console.status("[bold cyan]Récupération des stats…[/]"):
        try:
            data = api_stats(code)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                console.print(f"[bold red]Code introuvable :[/] '{code}'")
            else:
                console.print(f"[bold red]Erreur HTTP {e.response.status_code}[/]")
            raise typer.Exit(1)
        except httpx.RequestError:
            api = get_api_url()
            console.print(f"[bold red]Impossible de joindre l'API[/] ({api})")
            raise typer.Exit(1)

    table = Table(show_header=False, border_style="cyan", min_width=50)
    table.add_column("Clé", style="bold cyan", width=14)
    table.add_column("Valeur")

    # Formater la date
    created = data["created_at"].replace("T", " ").split(".")[0]

    table.add_row("🔑 Code", data["code"])
    table.add_row("🔗 URL courte", f"[green]{data['short']}[/]")
    table.add_row("📄 Originale", data["original"])
    table.add_row("👆 Clics", str(data["clicks"]))
    table.add_row("📅 Créé le", created)

    console.print(table)


# ─────────────────────────────────────────────
#  pyshort config
# ─────────────────────────────────────────────
@app.command()
def config(
    api_url: Optional[str] = typer.Option(None, "--api-url", help="URL de l'API backend."),
    show: bool = typer.Option(False, "--show", help="Affiche la configuration actuelle."),
):
    """Configure l'URL de l'API backend (sauvegardée dans ~/.pyshortrc)."""
    if show or api_url is None:
        current = get_api_url()
        console.print(f"[bold]API URL :[/] {current}")
        return

    save_api_url(api_url)
    console.print(f"[bold green]✅ API URL mise à jour :[/] {api_url}")


# ─────────────────────────────────────────────
#  pyshort version
# ─────────────────────────────────────────────
@app.command()
def version():
    """Affiche la version de pyshort."""
    console.print(f"[bold]pyshort[/] v{__version__}")


if __name__ == "__main__":
    app()

# ─────────────────────────────────────────────
#  pyshort gui
# ─────────────────────────────────────────────
@app.command()
def gui():
    """Lance l'interface graphique (pour les utilisateurs non-développeurs)."""
    try:
        from pyshort.gui import launch_gui
        console.print("[bold cyan]Ouverture de l'interface graphique…[/]")
        launch_gui()
    except ImportError:
        console.print("[bold red]tkinter n'est pas disponible sur ce système.[/]")
        console.print("Sur Ubuntu/Debian : [bold]sudo apt install python3-tk[/]")