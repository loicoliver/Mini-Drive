"""Interface CLI : point d'entrée utilisateur en ligne de commande."""

import argparse
import contextlib
import os
import sys
from pathlib import Path

from minidrive.application.users import DEFAULT_USER_ID
from minidrive.bootstrap import Container, create_container
from minidrive.domain.errors import DomainError


def _current_user(args: argparse.Namespace) -> str:
    """Utilisateur agissant : --utilisateur, sinon MINIDRIVE_USER, sinon local."""
    if getattr(args, "acting_user", None):
        return str(args.acting_user)
    return os.environ.get("MINIDRIVE_USER", DEFAULT_USER_ID)


def _resolve_node_kind(container: Container, node_id: str) -> str:
    """Détermine si un ID désigne un dossier ou un fichier (exit 1 si inconnu).

    Passe par get() (corbeille incluse), pas par ls (qui la masque) :
    trash/restore/rm doivent résoudre les IDs corbeillés.
    """
    if container.folder_repository.get(node_id) is not None:
        return "folder"
    if container.file_repository.get(node_id) is not None:
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
    parser.add_argument(
        "--utilisateur",
        dest="acting_user",
        default=None,
        help="Utilisateur agissant (défaut : $MINIDRIVE_USER ou 'local')",
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

    trash_parser = subparsers.add_parser(
        "trash",
        help="Mettre à la corbeille",
        description="Mettre un dossier (et son contenu) ou un fichier à la corbeille.",
    )
    trash_parser.add_argument("id", help="Identifiant du dossier ou fichier")

    restore_parser = subparsers.add_parser(
        "restore",
        help="Restaurer depuis la corbeille",
        description="Restaurer un dossier (et son contenu) ou un fichier corbeillé.",
    )
    restore_parser.add_argument("id", help="Identifiant du dossier ou fichier")

    rm_parser = subparsers.add_parser(
        "rm",
        help="Supprimer définitivement",
        description="Supprimer définitivement un dossier (récursif) ou un fichier.",
    )
    rm_parser.add_argument("id", help="Identifiant du dossier ou fichier")

    share_parser = subparsers.add_parser(
        "share",
        help="Partager avec un utilisateur",
        description="Partager un dossier ou un fichier (rôle reader ou editor).",
    )
    share_parser.add_argument("id", help="Identifiant du dossier ou fichier")
    share_parser.add_argument("utilisateur", help="Utilisateur bénéficiaire")
    share_parser.add_argument("role", help="Rôle : reader ou editor")

    unshare_parser = subparsers.add_parser(
        "unshare",
        help="Retirer un partage",
        description="Retirer un utilisateur d'un dossier ou fichier partagé.",
    )
    unshare_parser.add_argument("id", help="Identifiant du dossier ou fichier")
    unshare_parser.add_argument("utilisateur", help="Utilisateur à retirer")

    serve_parser = subparsers.add_parser(
        "serve",
        help="Démarrer le serveur HTTP",
        description="Démarrer le serveur HTTP (mêmes use cases que la CLI).",
    )
    serve_parser.add_argument(
        "--port", type=int, default=8000, help="Port d'écoute (défaut : 8000)"
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
        acting_user = _current_user(args)
        if args.command == "mkdir":
            folder_name: str = str(args.nom)
            folder = container.create_folder.execute(name=folder_name, owner_id=acting_user)
            print(f"✓ Dossier '{folder.name}' créé avec succès (ID: {folder.id})")
        elif args.command == "ls":
            folders = container.list_folders.execute(user_id=acting_user)
            files = container.list_files.execute(user_id=acting_user)
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
            file = container.upload_file.execute(name=source.name, data=data, user_id=acting_user)
            print(f"✓ Fichier '{file.name}' uploadé ({file.size}, ID: {file.id})")
        elif args.command == "download":
            file_id: str = str(args.id)
            file, content = container.download_file.execute(file_id=file_id, user_id=acting_user)
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
                    folder_id=node_id, new_name=new_name, user_id=acting_user
                )
                print(f"✓ Renommé en '{renamed_folder.name}' (ID: {renamed_folder.id})")
            else:
                renamed_file = container.rename_file.execute(
                    file_id=node_id, new_name=new_name, user_id=acting_user
                )
                print(f"✓ Renommé en '{renamed_file.name}' (ID: {renamed_file.id})")
        elif args.command == "move":
            node_id = str(args.id)
            new_parent: str | None = str(args.vers) if args.vers is not None else None
            if _resolve_node_kind(container, node_id) == "folder":
                moved_folder = container.move_folder.execute(
                    folder_id=node_id, new_parent_id=new_parent, user_id=acting_user
                )
                where = f"vers '{new_parent}'" if new_parent is not None else "vers la racine"
                print(f"✓ '{moved_folder.name}' déplacé {where} (ID: {moved_folder.id})")
            else:
                moved_file = container.move_file.execute(
                    file_id=node_id, new_parent_id=new_parent, user_id=acting_user
                )
                where = f"vers '{new_parent}'" if new_parent is not None else "vers la racine"
                print(f"✓ '{moved_file.name}' déplacé {where} (ID: {moved_file.id})")
        elif args.command == "trash":
            node_id = str(args.id)
            if _resolve_node_kind(container, node_id) == "folder":
                trashed_folder = container.trash_folder.execute(
                    folder_id=node_id, user_id=acting_user
                )
                print(f"✓ '{trashed_folder.name}' mis à la corbeille (ID: {trashed_folder.id})")
            else:
                trashed_file = container.trash_file.execute(file_id=node_id, user_id=acting_user)
                print(f"✓ '{trashed_file.name}' mis à la corbeille (ID: {trashed_file.id})")
        elif args.command == "restore":
            node_id = str(args.id)
            if _resolve_node_kind(container, node_id) == "folder":
                restored_folder = container.restore_folder.execute(
                    folder_id=node_id, user_id=acting_user
                )
                print(f"✓ '{restored_folder.name}' restauré (ID: {restored_folder.id})")
            else:
                restored_file = container.restore_file.execute(file_id=node_id, user_id=acting_user)
                print(f"✓ '{restored_file.name}' restauré (ID: {restored_file.id})")
        elif args.command == "rm":
            node_id = str(args.id)
            if _resolve_node_kind(container, node_id) == "folder":
                container.purge_folder.execute(folder_id=node_id, user_id=acting_user)
            else:
                container.purge_file.execute(file_id=node_id, user_id=acting_user)
            print(f"✓ '{node_id}' supprimé définitivement")
        elif args.command == "share":
            node_id = str(args.id)
            target_user: str = str(args.utilisateur)
            role: str = str(args.role)
            if _resolve_node_kind(container, node_id) == "folder":
                container.share_folder.execute(
                    folder_id=node_id, user_id=target_user, role=role, owner_id=acting_user
                )
            else:
                container.share_file.execute(
                    file_id=node_id, user_id=target_user, role=role, owner_id=acting_user
                )
            print(f"✓ Partagé avec '{target_user}' ({role})")
        elif args.command == "unshare":
            node_id = str(args.id)
            target_user = str(args.utilisateur)
            if _resolve_node_kind(container, node_id) == "folder":
                container.unshare_folder.execute(
                    folder_id=node_id, user_id=target_user, owner_id=acting_user
                )
            else:
                container.unshare_file.execute(
                    file_id=node_id, user_id=target_user, owner_id=acting_user
                )
            print(f"✓ Partage retiré pour '{target_user}'")
        elif args.command == "serve":
            from minidrive.interfaces.rest_api import build_server

            server = build_server(port=int(args.port))
            print(f"Mini-Drive sur http://127.0.0.1:{server.server_port} (Ctrl+C pour arrêter)")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                server.server_close()
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
