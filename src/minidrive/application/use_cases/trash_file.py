"""Use cases pour la corbeille des fichiers (pattern Use Case / Command)."""

from minidrive.application.access import require_write
from minidrive.application.ports import FileRepository, ShareRepository
from minidrive.application.users import DEFAULT_USER_ID
from minidrive.domain.entities import File
from minidrive.domain.errors import UnknownFileError


class TrashFile:
    """Use case : mettre un fichier à la corbeille (propriétaire ou editor)."""

    def __init__(self, file_repository: FileRepository, share_repository: ShareRepository) -> None:
        """Injection de dépendances par constructeur.

        Args:
            file_repository: Port pour la persistance des métadonnées
            share_repository: Port pour la persistance des partages
        """
        self._file_repository = file_repository
        self._share_repository = share_repository

    def execute(self, file_id: str, user_id: str = DEFAULT_USER_ID) -> File:
        """Met un fichier à la corbeille (idempotent).

        Args:
            file_id: Identifiant du fichier
            user_id: Utilisateur agissant (propriétaire ou editor)

        Returns:
            Le fichier corbeillé

        Raises:
            UnknownFileError: Si l'ID est inconnu
            PermissionDeniedError: Si l'utilisateur ne peut pas écrire
        """
        file = self._file_repository.get(file_id)
        if file is None:
            raise UnknownFileError(file_id)
        role = self._share_repository.role_for("file", file_id, user_id)
        require_write(file.owner_id, role, user_id, file_id)

        if not file.trashed:
            file.trashed = True
            self._file_repository.save(file)
        return file


class RestoreFile:
    """Use case : restaurer un fichier corbeillé (propriétaire ou editor)."""

    def __init__(self, file_repository: FileRepository, share_repository: ShareRepository) -> None:
        """Injection de dépendances par constructeur.

        Args:
            file_repository: Port pour la persistance des métadonnées
            share_repository: Port pour la persistance des partages
        """
        self._file_repository = file_repository
        self._share_repository = share_repository

    def execute(self, file_id: str, user_id: str = DEFAULT_USER_ID) -> File:
        """Restaure un fichier corbeillé (idempotent).

        Args:
            file_id: Identifiant du fichier
            user_id: Utilisateur agissant (propriétaire ou editor)

        Returns:
            Le fichier restauré

        Raises:
            UnknownFileError: Si l'ID est inconnu
            PermissionDeniedError: Si l'utilisateur ne peut pas écrire
        """
        file = self._file_repository.get(file_id)
        if file is None:
            raise UnknownFileError(file_id)
        role = self._share_repository.role_for("file", file_id, user_id)
        require_write(file.owner_id, role, user_id, file_id)

        if file.trashed:
            file.trashed = False
            self._file_repository.save(file)
        return file
