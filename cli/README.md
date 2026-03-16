# pyshort — Raccourcisseur d'URLs en ligne de commande

## Installation

```bash
pip install pyshort-cli

``
## Utilisation

```bash
# Raccourcir une URL (résultat copié automatiquement)
pyshort shorten https://www.monsite.com/une/url/tres/longue
# ╭─ 🔗 URL raccourcie ─╮
# │ https://shr.ty/abc12x │
# │ ✅ Copié dans le presse-papier │
# ╰────────────────────────╯

# Sans copie automatique
pyshort shorten https://example.com --no-copy

# Voir les statistiques (code ou URL courte)
pyshort stats abc12x
pyshort stats https://shr.ty/abc12x

# Version
pyshort version
```

