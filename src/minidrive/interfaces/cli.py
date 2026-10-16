"""Interface CLI : point d'entrée utilisateur en ligne de commande."""

import argparse
import contextlib
import sys
from pathlib import Path

from minidrive.bootstrap import Container, create_container
from minidrive.domain.errors import DomainError


def _resolve_node_kind(container: Container, node_id: str) -> str:
    """Détermine si un ID désigne un dossier ou un fichier (exit 1 si inconnu)."""
    for folder in container.list_folders.execute():
        if folder.id == node_id:
            return "folder"
    for file in container.list_files.execute():
        if file.id == node_id:
            return "file"
    print(f"✗ Erreur: ID inconnu '{node_id}'")
    sys.exit(1)


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

    rename_parser = subparsers.add_parser(
        "rename",
        help="Renommer un dossier ou un fichier",
        description="Renommer un dossier ou un fichier par son ID.",
    )
    rename_parser.add_argument("id", help="Identifiant du dossier ou fichier")
    rename_parser.add_argument("nom", help="Nouveau nom")

    move_parser = subparsers.add_parser(
        "move",
        help="Déplacer un dossier ou un fichier",
        description="Déplacer un dossier ou un fichier vers un dossier parent.",
    )
    move_parser.add_argument("id", help="Identifiant du dossier ou fichier")
    move_parser.add_argument(
        "--vers",
        default=None,
        help="ID du dossier de destination (défaut : racine)",
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
        elif args.command == "rename":
            node_id: str = str(args.id)
            new_name: str = str(args.nom)
            if _resolve_node_kind(container, node_id) == "folder":
                renamed_folder = container.rename_folder.execute(
                    folder_id=node_id, new_name=new_name
                )
                print(f"✓ Renommé en '{renamed_folder.name}' (ID: {renamed_folder.id})")
            else:
                renamed_file = container.rename_file.execute(file_id=node_id, new_name=new_name)
                print(f"✓ Renommé en '{renamed_file.name}' (ID: {renamed_file.id})")
        elif args.command == "move":
            node_id = str(args.id)
            new_parent: str | None = str(args.vers) if args.vers is not None else None
            if _resolve_node_kind(container, node_id) == "folder":
                moved_folder = container.move_folder.execute(
                    folder_id=node_id, new_parent_id=new_parent
                )
                where = f"vers '{new_parent}'" if new_parent is not None else "vers la racine"
                print(f"✓ '{moved_folder.name}' déplacé {where} (ID: {moved_folder.id})")
            else:
                moved_file = container.move_file.execute(file_id=node_id, new_parent_id=new_parent)
                where = f"vers '{new_parent}'" if new_parent is not None else "vers la racine"
                print(f"✓ '{moved_file.name}' déplacé {where} (ID: {moved_file.id})")
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
