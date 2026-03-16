# pyshort — Raccourcisseur d'URLs en ligne de commande

## Installation

```bash
pip install pyshort
# ou en local depuis ce dossier :
pip install -e .
```

## Configuration (une seule fois)

```bash
pyshort config --api-url https://mon-api.render.com
```

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

# Voir la config actuelle
pyshort config --show

# Version
pyshort version
```

## Lancer les tests

```bash
pip install pytest
pytest tests/ -v
```
