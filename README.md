# Plume — Correcteur de français

Outil en ligne de commande (et bientôt widget bureau) pour corriger automatiquement l'orthographe, les accents, les apostrophes et la grammaire française — conçu pour un développeur sur clavier QWERTY qui écrit du français professionnel sans accents.

Le contrat est strict : **corriger uniquement ; ne jamais changer le sens, ne jamais ajouter ni supprimer d'information.**

---

## Installation

Nécessite Python 3.11+ et [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/koukiatef6/plume.git
cd plume
uv sync
```

## Configuration initiale

```bash
uv run plume init
```

Répond aux questions interactives (URL de l'API, clé, modèle). Effectue un appel de test avant de sauvegarder. La clé est stockée dans `~/.config/plume/.env`, jamais dans le TOML.

## Utilisation

```bash
# Texte en argument
uv run plume fix "Bonjour, ca va prendre 10 min"

# Depuis stdin
echo "Salut Thomas, ca marche pas encore." | uv run plume fix --stdin

# Alias pratique (à ajouter dans ~/.bashrc)
alias fix='uv run --project ~/My\ projects/Plume plume fix --stdin'
```

## Stack

- **Transport LLM** : `httpx` → endpoint OpenAI-compatible (LiteLLM)
- **Config** : Pydantic v2 · TOML (`tomllib` / `tomli-w`) · secrets dans `.env`
- **Chemins** : `platformdirs` (pas de `~/.config` codé en dur)
- **Lint / types** : `ruff` + `mypy --strict`
- **Tests** : `pytest` + `pytest-httpx` (17 tests, tout mocké)

## Configuration

| Fichier | Contenu |
|---|---|
| `~/.config/plume/config.toml` | `api_base_url`, `model`, `hotkey`, `widget_position` |
| `~/.config/plume/.env` | `PLUME_API_KEY` uniquement |

## Phases de développement

- [x] **Phase 1** — CLI : `plume init` + `plume fix`
- [ ] **Phase 2** — Mode presse-papiers : `plume fix` sans argument
- [ ] **Phase 3** — Widget PyQt6 + icône tray + hotkey global
- [ ] **Phase 4** — Dialogue paramètres + assistant première utilisation

## Tests

```bash
uv run pytest -v
uv run ruff check plume tests
uv run mypy plume
```
