# Plume — Correcteur et traducteur de texte

Outil bureau pour Ubuntu qui corrige et traduit du texte dans n'importe quelle application via un raccourci clavier global et un bouton flottant toujours visible.

Le contrat est strict : **corriger uniquement ; ne jamais changer le sens, ne jamais ajouter ni supprimer d'information.**

---

## Prérequis

- Ubuntu 20.04+ (testé sur 20.04)
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- `xclip` pour le presse-papiers : `sudo apt install xclip`
- Un endpoint LLM compatible OpenAI (ex. LiteLLM)

## Installation

```bash
git clone https://github.com/atef5-in/plume.git
cd plume
uv sync
```

## Configuration initiale

Au premier lancement, un assistant de configuration s'ouvre automatiquement et guide pas à pas : URL de l'API, clé, modèle. La clé est stockée dans `~/.config/plume/.env`, jamais dans le TOML.

Pour modifier la configuration ultérieurement : clic droit sur le bouton flottant → fenêtre Paramètres. Les changements (y compris le raccourci clavier) prennent effet immédiatement sans redémarrage.

## Utilisation

```bash
uv run plume run
```

Lance un bouton flottant circulaire toujours visible sur le bureau.

1. Sélectionner le texte dans n'importe quelle application
2. Appuyer sur `Ctrl+Alt+F`
3. Le texte est automatiquement copié, traité et collé en place

Pour démarrer automatiquement au login : ajouter `plume run` aux Applications au démarrage de GNOME.

## Les 4 modes

Le bouton change de couleur et d'étiquette selon le mode actif. Clic droit sur le bouton pour changer de mode.

| Mode | Étiquette | Couleur |
|---|---|---|
| Corriger le français | FR | Indigo |
| Corriger l'anglais | EN | Bleu |
| Traduire FR → EN | F›E | Ambré |
| Traduire EN → FR | E›F | Violet |

Le mode choisi est conservé après redémarrage.

## Modes CLI (toujours disponibles)

```bash
uv run plume fix "Bonjour, ca va prendre 10 min"
echo "Salut Thomas, ca marche pas encore." | uv run plume fix --stdin
uv run plume fix   # lit le presse-papiers
```

## Stack

- Transport LLM : `httpx` → endpoint OpenAI-compatible (LiteLLM)
- Config : Pydantic v2 · TOML (`tomllib` / `tomli-w`) · secrets dans `.env`
- GUI : `tkinter` + X11 Shape Extension (fenêtre vraiment circulaire, sans coins)
- Hotkey global : `pynput`
- Presse-papiers : `pyperclip` + `xclip`
- Notifications : `notify-send`
- Chemins : `platformdirs` (pas de `~/.config` codé en dur)
- Lint / types : `ruff` + `mypy --strict`
- Tests : `pytest` + `pytest-httpx` (26 tests)

> ⚠️ Note Ubuntu 20.04 : cette version utilise `tkinter` au lieu de PyQt6 (glibc 2.31 insuffisant). La migration vers PyQt6 est prévue lors du passage à Ubuntu 22.04+.

## Configuration

| Fichier | Contenu |
|---|---|
| `~/.config/plume/config.toml` | `api_base_url`, `model`, `hotkey`, `mode`, `widget_position` |
| `~/.config/plume/.env` | `PLUME_API_KEY` uniquement |

## Phases de développement

- [x] Phase 1 — CLI : `plume init` + `plume fix`
- [x] Phase 2 — Mode presse-papiers : `plume fix` sans argument
- [x] Phase 3 — Widget flottant + hotkey global + notifications
- [x] Phase 4 — Dialogue paramètres + assistant première utilisation
- [x] Phase 4b — 4 modes (corriger FR/EN, traduire FR↔EN)
- [ ] Phase 5 — Support multiplateforme (Linux + Windows)

## Tests

```bash
uv run pytest -v
uv run ruff check plume tests
uv run mypy plume
```
