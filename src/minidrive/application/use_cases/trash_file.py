"""Use cases pour la corbeille des fichiers (pattern Use Case / Command)."""

from minidrive.application.ports import FileRepository
from minidrive.domain.entities import File
from minidrive.domain.errors import UnknownFileError


class TrashFile:
    """Use case : mettre un fichier à la corbeille (contenu conservé)."""

    def __init__(self, file_repository: FileRepository) -> None:
        """Injection de dépendances par constructeur.

        Args:
            file_repository: Port pour la persistance des métadonnées
        """
        self._file_repository = file_repository

    def execute(self, file_id: str) -> File:
        """Met un fichier à la corbeille (idempotent).

        Args:
            file_id: Identifiant du fichier

        Returns:
            Le fichier corbeillé

        Raises:
            UnknownFileError: Si l'ID est inconnu
        """
        file = self._file_repository.get(file_id)
        if file is None:
            raise UnknownFileError(file_id)

        if not file.trashed:
            file.trashed = True
            self._file_repository.save(file)
        return file


class RestoreFile:
    """Use case : restaurer un fichier corbeillé."""

    def __init__(self, file_repository: FileRepository) -> None:
        """Injection de dépendances par constructeur.

        Args:
            file_repository: Port pour la persistance des métadonnées
        """
        self._file_repository = file_repository

    def execute(self, file_id: str) -> File:
        """Restaure un fichier corbeillé (idempotent).

        Args:
            file_id: Identifiant du fichier

        Returns:
            Le fichier restauré

        Raises:
            UnknownFileError: Si l'ID est inconnu
        """
        file = self._file_repository.get(file_id)
        if file is None:
            raise UnknownFileError(file_id)

        if file.trashed:
            file.trashed = False
            self._file_repository.save(file)
        return file
