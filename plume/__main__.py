from __future__ import annotations

import argparse
import asyncio
import getpass
import sys

from plume.config import CONFIG_DIR, Config, ConfigError, load_config, save_config
from plume.fixer import FixerError, fix_text

_DEFAULT_BASE_URL = "http://148.230.93.60:4000"
_DEFAULT_MODEL = "mistral-large-3:675b-cloud"


def cmd_init(_args: argparse.Namespace) -> None:
    print("Plume — Configuration initiale")
    print()

    raw_url = input(f"API base URL [{_DEFAULT_BASE_URL}]: ").strip()
    api_base_url = raw_url or _DEFAULT_BASE_URL

    api_key = getpass.getpass("API key: ").strip()
    if not api_key:
        print("Erreur : la clé API ne peut pas être vide.", file=sys.stderr)
        sys.exit(1)

    raw_model = input(f"Model [{_DEFAULT_MODEL}]: ").strip()
    model = raw_model or _DEFAULT_MODEL

    cfg = Config(api_base_url=api_base_url, api_key=api_key, model=model)

    print("\nTest de connexion en cours…")
    try:
        result = asyncio.run(fix_text("Bonjour, ca va?", cfg))
        print(f"Réponse du modèle : {result}")
    except FixerError as exc:
        print(f"\n✗ Échec du test : {exc}", file=sys.stderr)
        print("Configuration non sauvegardée.", file=sys.stderr)
        sys.exit(1)

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    save_config(cfg)
    print("\n✓ Test call successful. Config saved.")
    print(f"  Répertoire de config : {CONFIG_DIR}")


def cmd_fix(args: argparse.Namespace) -> None:
    try:
        cfg = load_config()
    except ConfigError as exc:
        print(f"Erreur de configuration : {exc}", file=sys.stderr)
        sys.exit(1)

    if args.stdin:
        text = sys.stdin.read()
    elif args.text:
        text = args.text
    else:
        print("Erreur : fournissez du texte ou --stdin.", file=sys.stderr)
        sys.exit(1)

    try:
        result = asyncio.run(fix_text(text, cfg))
        print(result)
    except FixerError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(prog="plume", description="Correcteur de français")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Configuration interactive")

    fix_parser = sub.add_parser("fix", help="Corriger du texte")
    fix_parser.add_argument("text", nargs="?", help="Texte à corriger")
    fix_parser.add_argument("--stdin", action="store_true", help="Lire depuis stdin")

    args = parser.parse_args()
    if args.command == "init":
        cmd_init(args)
    elif args.command == "fix":
        cmd_fix(args)


if __name__ == "__main__":
    main()
