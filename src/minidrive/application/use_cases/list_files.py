"""Use case pour lister les fichiers (pattern Use Case / Command)."""

from minidrive.application.ports import FileRepository
from minidrive.domain.entities import File


class ListFiles:
    """Use case : lister tous les fichiers.

    Démontre le principe S (Single Responsibility) : une seule action métier.
    Démontre le principe D (Dependency Inversion) : dépend des abstractions (ports).
    """

    def __init__(self, file_repository: FileRepository) -> None:
        """Injection de dépendances par constructeur.

        Args:
            file_repository: Port pour la persistance des métadonnées
        """
        self._file_repository = file_repository

    def execute(self) -> list[File]:
        """Liste tous les fichiers, triés par nom.

        Returns:
            Tous les fichiers persistés, par nom croissant
        """
        return self._file_repository.list_all()
