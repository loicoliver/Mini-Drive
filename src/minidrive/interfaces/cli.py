"""Interface CLI : point d'entrée utilisateur en ligne de commande."""

import argparse
import contextlib
import sys
from pathlib import Path

from minidrive.bootstrap import create_container
from minidrive.domain.errors import DomainError


def ensure_utf8_stdio() -> None:
    """Force stdout/stderr en UTF-8 quand c'est possible (Windows cp1252, etc.).

    Best-effort et cross-platform : ne lève jamais d'exception.
    À combiner avec PYTHONUTF8=1 / PYTHONIOENCODING=utf-8 dans la CI.
    """
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            with contextlib.suppress(Exception):
                reconfigure(encoding="utf-8", errors="replace")


def build_parser() -> argparse.ArgumentParser:
    """Construit le parser argparse (séparé de main pour les tests)."""
    parser = argparse.ArgumentParser(
        prog="minidrive",
        description="Clone simplifié de Google Drive (démo Clean Architecture).",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="<commande>")

    mkdir_parser = subparsers.add_parser(
        "mkdir",
        help="Créer un nouveau dossier",
        description="Créer un nouveau dossier.",
    )
    mkdir_parser.add_argument("nom", help="Nom du dossier à créer")

    subparsers.add_parser(
        "ls",
        help="Lister dossiers et fichiers",
        description="Lister tous les dossiers et fichiers, triés par nom.",
    )

    upload_parser = subparsers.add_parser(
        "upload",
        help="Uploader un fichier",
        description="Uploader un fichier local dans le drive.",
    )
    upload_parser.add_argument("chemin", help="Chemin du fichier local à uploader")

    download_parser = subparsers.add_parser(
        "download",
        help="Télécharger un fichier",
        description="Télécharger un fichier du drive vers le disque local.",
    )
    download_parser.add_argument("id", help="Identifiant du fichier à télécharger")
    download_parser.add_argument(
        "--vers",
        default=None,
        help="Chemin de destination (défaut : nom du fichier dans le dossier courant)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Point d'entrée principal du CLI.

    Args:
        argv: Arguments sans le nom du programme (sys.argv[1:] si None).
    """
    ensure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Composition root : câble les dépendances
    container = create_container()

    try:
        if args.command == "mkdir":
            folder_name: str = str(args.nom)
            folder = container.create_folder.execute(name=folder_name)
            print(f"✓ Dossier '{folder.name}' créé avec succès (ID: {folder.id})")
        elif args.command == "ls":
            folders = container.list_folders.execute()
            files = container.list_files.execute()
            if not folders and not files:
                print("Drive vide.")
                return
            if folders:
                print("Dossiers :")
                for folder in folders:
                    print(f"  {folder.name} (ID: {folder.id})")
            if files:
                print("Fichiers :")
                for file in files:
                    print(f"  {file.name} ({file.size}, ID: {file.id})")
        elif args.command == "upload":
            source = Path(str(args.chemin))
            if not source.is_file():
                print(f"✗ Erreur: fichier introuvable '{source}'")
                sys.exit(1)
            data = source.read_bytes()
            file = container.upload_file.execute(name=source.name, data=data)
            print(f"✓ Fichier '{file.name}' uploadé ({file.size}, ID: {file.id})")
        elif args.command == "download":
            file_id: str = str(args.id)
            file, content = container.download_file.execute(file_id=file_id)
            destination = Path(str(args.vers)) if args.vers is not None else Path(file.name.value)
            if destination.exists():
                print(f"✗ Erreur: la destination '{destination}' existe déjà")
                sys.exit(1)
            destination.write_bytes(content)
            print(f"✓ Fichier '{file.name}' téléchargé vers '{destination}'")
        else:  # Sécurité : argparse rejette déjà les commandes inconnues (exit 2)
            print(f"Commande inconnue: {args.command}")
            sys.exit(1)

    except DomainError as e:
        print(f"✗ Erreur: {e}")
        sys.exit(1)
    except Exception as e:  # noqa: BLE001 - on veut un message propre en CLI
        print(f"✗ Erreur inattendue: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
