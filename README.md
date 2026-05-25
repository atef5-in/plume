# Plume — Correcteur et traducteur de texte

Outil bureau pour Linux et Windows qui corrige et traduit du texte dans n'importe quelle application via un raccourci clavier global et un bouton flottant toujours visible.

Le contrat est strict : **corriger uniquement ; ne jamais changer le sens, ne jamais ajouter ni supprimer d'information.**

---

## Installation

### Windows (recommandé)

Télécharger `PlumeSetup.exe` depuis la page [Releases](https://github.com/atef5-in/Plume/releases), double-cliquer et suivre l'assistant. Plume démarre automatiquement à chaque connexion.

### Linux (depuis les sources)

```bash
# Prérequis
sudo apt install xclip python3-tk

git clone https://github.com/atef5-in/Plume.git
cd Plume
uv sync
uv run plume run
```

Pour démarrer automatiquement au login : ajouter `uv run plume run` aux Applications au démarrage de GNOME.

---

## Configuration initiale

Au premier lancement, un assistant de configuration s'ouvre automatiquement : URL de l'API, clé, modèle. La clé est stockée dans le répertoire de config utilisateur, jamais en clair dans le TOML.

Pour modifier la configuration : clic droit sur le bouton flottant → **Paramètres**. Les changements (y compris le raccourci clavier) prennent effet immédiatement. Pour quitter l'application : clic droit → **Fermer ✕**.

---

## Utilisation

1. Sélectionner du texte dans n'importe quelle application
2. Appuyer sur `Ctrl+Alt+F` (ou cliquer le bouton flottant)
3. Le texte est automatiquement copié, traité et collé en place

---

## Les 5 modes

Clic droit sur le bouton pour changer de mode. Le mode est mémorisé entre les sessions.

| Mode | Étiquette | Couleur |
|---|---|---|
| Corriger le français | FR | Indigo |
| Corriger l'anglais | EN | Bleu |
| Traduire FR → EN | F›E | Ambré |
| Traduire EN → FR | E›F | Violet |
| Réécrire dans un ton personnalisé | T~ | Sarcelle |

### Réécrire dans un ton

Définissez vos propres tons (nom + description en texte libre) dans **Paramètres → Tons personnalisés**. Chaque ton décrit comment le texte doit être réécrit (ex. *concis*, *diplomatique*, *formel*). Sélectionnez ensuite un ton via le sous-menu **Réécrire en…** du clic droit.

Le moteur respecte un contrat strict (pas d'ajout/suppression d'information, dates et chiffres préservés à l'identique, registre tu/vous conservé). Les tons transformatifs (commercial, marketing) peuvent néanmoins introduire des inexactitudes avec les petits modèles — relisez avant de coller.

---

## Modes CLI

```bash
uv run plume fix "Bonjour, ca va prendre 10 min"
echo "Salut Thomas, ca marche pas encore." | uv run plume fix --stdin
uv run plume fix   # lit le presse-papiers
```

---

## Stack

- Transport LLM : `httpx` → endpoint OpenAI-compatible (LiteLLM)
- Config : Pydantic v2 · TOML · secrets dans `.env`
- GUI : `tkinter` (cercle via X11 Shape sur Linux, `-transparentcolor` sur Windows)
- Hotkey global : `pynput`
- Presse-papiers : `pyperclip`
- Notifications : `notify-send` (Linux) · `plyer` (Windows)
- Chemins : `platformdirs`
- Lint / types : `ruff` + `mypy --strict`
- Tests : `pytest` + `pytest-httpx` (32 tests)
- Installeur Windows : PyInstaller + Inno Setup + GitHub Actions

---

## Publier une nouvelle version

```bash
git tag v0.x.0
git push origin v0.x.0
```

GitHub Actions construit automatiquement `PlumeSetup.exe` et le publie dans les Releases.

---

## Configuration

| Fichier | Contenu |
|---|---|
| Linux : `~/.config/plume/config.toml` | `api_base_url`, `model`, `hotkey`, `mode`, `widget_position`, `tones`, `active_tone` |
| Windows : `%LOCALAPPDATA%\plume\plume\config.toml` | idem |
| `.env` (même dossier) | `PLUME_API_KEY` uniquement |

---

## Phases de développement

- [x] Phase 1 — CLI : `plume init` + `plume fix`
- [x] Phase 2 — Mode presse-papiers : `plume fix` sans argument
- [x] Phase 3 — Widget flottant + hotkey global + notifications
- [x] Phase 4 — Dialogue paramètres + assistant première utilisation
- [x] Phase 4b — 4 modes (corriger FR/EN, traduire FR↔EN)
- [x] Phase 5 — Support multiplateforme (Linux + Windows) + installeur Windows
- [x] Phase 6 — 5ᵉ mode : réécriture dans un ton personnalisé (liste éditable de tons)

---

## Tests

```bash
uv run pytest -v
uv run ruff check plume tests
uv run mypy plume
```

> ⚠️ Note Ubuntu 20.04 : cette version utilise `tkinter` au lieu de PyQt6 (glibc 2.31 insuffisant). La migration vers PyQt6 est prévue lors du passage à Ubuntu 22.04+.
