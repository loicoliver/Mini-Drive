"""Use case pour lister les dossiers (pattern Use Case / Command)."""

from minidrive.application.ports import FolderRepository
from minidrive.domain.entities import Folder


class ListFolders:
    """Use case : lister tous les dossiers.

    Démontre le principe S (Single Responsibility) : une seule action métier.
    Démontre le principe D (Dependency Inversion) : dépend des abstractions (ports).
    """

    def __init__(self, folder_repository: FolderRepository) -> None:
        """Injection de dépendances par constructeur.

        Args:
            folder_repository: Port pour la persistance des dossiers
        """
        self._folder_repository = folder_repository

    def execute(self) -> list[Folder]:
        """Liste tous les dossiers, triés par nom.

        Returns:
            Tous les dossiers persistés, par nom croissant
        """
        return self._folder_repository.list_all()
