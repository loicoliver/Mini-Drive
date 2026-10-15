"""Interface CLI : point d'entrée utilisateur en ligne de commande."""

import sys

from minidrive.bootstrap import create_container
from minidrive.domain.errors import DomainError


def main() -> None:
    """Point d'entrée principal du CLI."""
    if len(sys.argv) < 2:
        print("Usage: minidrive <commande> [arguments]")
        print("Commandes disponibles:")
        print("  mkdir <nom>  - Créer un nouveau dossier")
        sys.exit(1)

    command = sys.argv[1]

    # Initialisation du conteneur (composition root)
    container = create_container()

    try:
        if command == "mkdir":
            if len(sys.argv) < 3:
                print("Usage: minidrive mkdir <nom>")
                sys.exit(1)

            folder_name = sys.argv[2]

            # Exécution du use case
            folder = container.create_folder.execute(name=folder_name)

            print(f"✓ Dossier '{folder.name}' créé avec succès (ID: {folder.id})")

        else:
            print(f"Commande inconnue: {command}")
            sys.exit(1)

    except DomainError as e:
        print(f"✗ Erreur: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Erreur inattendue: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
