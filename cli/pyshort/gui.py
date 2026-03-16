import threading
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox

from pyshort.api import shorten as api_shorten
from pyshort.api import stats as api_stats
from pyshort.config import get_api_url, save_api_url

# ── Couleurs ──────────────────────────────────────────────────────────────────
BG        = "#0f172a"
CARD      = "#1e293b"
BORDER    = "#334155"
BLUE      = "#0ea5e9"
BLUE_H    = "#38bdf8"
TEXT      = "#e2e8f0"
MUTED     = "#64748b"
GREEN     = "#22c55e"
RED_BG    = "#450a0a"
RED_FG    = "#fca5a5"


class PyShortGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PyShort — Raccourcisseur d'URLs")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        # Centrer la fenêtre
        w, h = 420, 520
        self.root.geometry(f"{w}x{h}")
        self.root.eval("tk::PlaceWindow . center")

        self._build_ui()

    # ── Construction de l'interface ───────────────────────────────────────────
    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────────
        header = tk.Frame(self.root, bg=CARD, pady=12)
        header.pack(fill="x")

        tk.Label(header, text="🔗 PyShort", bg=CARD, fg=BLUE,
                 font=("Segoe UI", 16, "bold")).pack(side="left", padx=16)
        tk.Label(header, text="Raccourcisseur d'URLs", bg=CARD, fg=MUTED,
                 font=("Segoe UI", 10)).pack(side="left")

        # ── Corps ─────────────────────────────────────────────────────────────
        body = tk.Frame(self.root, bg=BG, padx=20, pady=20)
        body.pack(fill="both", expand=True)

        # Label URL
        tk.Label(body, text="Collez ou tapez votre URL :", bg=BG, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 6))

        # Champ URL
        url_frame = tk.Frame(body, bg=BORDER, padx=1, pady=1)
        url_frame.pack(fill="x", pady=(0, 8))

        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(
            url_frame, textvariable=self.url_var,
            bg=CARD, fg=TEXT, insertbackground=TEXT,
            font=("Segoe UI", 11), relief="flat",
            bd=0,
        )
        self.url_entry.pack(fill="x", padx=10, pady=10)
        self.url_entry.bind("<Return>", lambda e: self._shorten())
        self.url_entry.focus()

        # Bouton coller
        self._btn_paste = self._make_button(
            body, "📋  Coller depuis le presse-papier",
            self._paste, bg=CARD, fg=MUTED, hover_bg=BORDER
        )
        self._btn_paste.pack(fill="x", pady=(0, 10))

        # Bouton raccourcir
        self._btn_shorten = self._make_button(
            body, "🔗  Raccourcir l'URL",
            self._shorten, bg=BLUE, fg="white", hover_bg=BLUE_H,
            font_size=12, bold=True
        )
        self._btn_shorten.pack(fill="x", pady=(0, 16))

        # Séparateur
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(0, 16))

        # Zone résultat
        tk.Label(body, text="URL raccourcie :", bg=BG, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 6))

        result_frame = tk.Frame(body, bg=BORDER, padx=1, pady=1)
        result_frame.pack(fill="x", pady=(0, 8))

        self.result_var = tk.StringVar(value="")
        result_inner = tk.Frame(result_frame, bg=CARD)
        result_inner.pack(fill="x")

        self.result_entry = tk.Entry(
            result_inner, textvariable=self.result_var,
            bg=CARD, fg=BLUE, font=("Segoe UI", 11),
            relief="flat", bd=0, state="readonly",
            readonlybackground=CARD, cursor="hand2",
        )
        self.result_entry.pack(fill="x", padx=10, pady=10)

        # Bouton copier
        self._btn_copy = self._make_button(
            body, "📋  Copier dans le presse-papier",
            self._copy, bg=CARD, fg=MUTED, hover_bg=BORDER
        )
        self._btn_copy.pack(fill="x", pady=(0, 8))

        # Stats
        self.stats_var = tk.StringVar(value="")
        tk.Label(body, textvariable=self.stats_var, bg=BG, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w")

        # Message status (erreur ou succès)
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(
            body, textvariable=self.status_var,
            bg=BG, fg=RED_FG, font=("Segoe UI", 9),
            wraplength=380, justify="left"
        )
        self.status_label.pack(anchor="w", pady=(8, 0))

        # ── Footer ────────────────────────────────────────────────────────────
        footer = tk.Frame(self.root, bg=CARD, pady=8)
        footer.pack(fill="x", side="bottom")

      
       
    # ── Actions ───────────────────────────────────────────────────────────────
    def _paste(self):
        try:
            text = self.root.clipboard_get()
            self.url_var.set(text.strip())
            self.url_entry.focus()
        except tk.TclError:
            self._set_status("Presse-papier vide ou inaccessible.", error=True)

    def _shorten(self):
        url = self.url_var.get().strip()
        if not url:
            self._set_status("Veuillez entrer une URL.", error=True)
            return

        # Ajoute https:// si manquant
        if not url.startswith("http"):
            url = "https://" + url
            self.url_var.set(url)

        self._btn_shorten.config(text="⏳  Raccourcissement…", state="disabled")
        self._set_status("")
        self.result_var.set("")
        self.stats_var.set("")

        # Appel API dans un thread séparé pour ne pas bloquer l'UI
        threading.Thread(target=self._do_shorten, args=(url,), daemon=True).start()

    def _do_shorten(self, url):
        try:
            import httpx
            data = api_shorten(url)
            self.root.after(0, self._on_shorten_success, data)
        except httpx.RequestError:
            api = get_api_url()
            self.root.after(0, self._set_status,
                f"Impossible de joindre l'API ({api}).\nVérifiez que le serveur est lancé.", True)
        except httpx.HTTPStatusError as e:
            self.root.after(0, self._set_status,
                f"Erreur {e.response.status_code} : URL invalide.", True)
        except Exception as e:
            self.root.after(0, self._set_status, str(e), True)
        finally:
            self.root.after(0, self._btn_shorten.config,
                {"text": "🔗  Raccourcir l'URL", "state": "normal"})

    def _on_shorten_success(self, data):
        self.result_var.set(data["short"])
        self._set_status("✅ URL raccourcie avec succès !", error=False)
        self.status_label.config(fg=GREEN)

        # Charger les stats
        threading.Thread(target=self._load_stats, args=(data["code"],), daemon=True).start()

    def _load_stats(self, code):
        try:
            data = api_stats(code)
            clicks = data["clicks"]
            date = data["created_at"][:10]
            self.root.after(0, self.stats_var.set,
                f"👆 {clicks} clic{'s' if clicks != 1 else ''}  •  📅 Créé le {date}")
        except Exception:
            pass

    def _copy(self):
        url = self.result_var.get()
        if not url:
            self._set_status("Aucune URL à copier.", error=True)
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        self._btn_copy.config(text="✅  Copié !", fg=GREEN)
        self.root.after(2000, lambda: self._btn_copy.config(
            text="📋  Copier dans le presse-papier", fg=MUTED))

    def _set_status(self, msg, error=False):
        self.status_var.set(msg)
        self.status_label.config(fg=RED_FG if error else GREEN)

    def _open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Paramètres")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.geometry("360x180")
        win.grab_set()

        tk.Label(win, text="URL de l'API backend :", bg=BG, fg=MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(20, 6))

        api_var = tk.StringVar(value=get_api_url())
        entry = tk.Entry(win, textvariable=api_var, bg=CARD, fg=TEXT,
                         insertbackground=TEXT, font=("Segoe UI", 11),
                         relief="flat", bd=0)
        frame = tk.Frame(win, bg=BORDER, padx=1, pady=1)
        frame.pack(fill="x", padx=20, pady=(0, 16))
        entry.pack(fill="x", padx=10, pady=8, in_=frame)

        def save():
            url = api_var.get().strip().rstrip("/")
            if url:
                save_api_url(url)
                self.api_label_var.set(f"API : {url}")
                win.destroy()

        self._make_button(win, "💾  Enregistrer", save,
                          bg=BLUE, fg="white", hover_bg=BLUE_H,
                          font_size=11, bold=True).pack(fill="x", padx=20)

    # ── Helper bouton ─────────────────────────────────────────────────────────
    def _make_button(self, parent, text, command,
                     bg=CARD, fg=TEXT, hover_bg=BORDER,
                     font_size=10, bold=False):
        btn = tk.Button(
            parent, text=text, command=command,
            bg=bg, fg=fg, activebackground=hover_bg, activeforeground=fg,
            font=("Segoe UI", font_size, "bold" if bold else "normal"),
            relief="flat", bd=0, cursor="hand2", pady=10,
        )
        btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        return btn

    def run(self):
        self.root.mainloop()


def launch_gui():
    app = PyShortGUI()
    app.run()


if __name__ == "__main__":
    launch_gui()