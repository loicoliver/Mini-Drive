"""Use case pour renommer un fichier (pattern Use Case / Command)."""

from minidrive.application.access import require_write
from minidrive.application.ports import FileRepository, ShareRepository
from minidrive.application.users import DEFAULT_USER_ID
from minidrive.domain.entities import File
from minidrive.domain.errors import FileAlreadyExistsError, InTrashError, UnknownFileError
from minidrive.domain.value_objects import FileName


class RenameFile:
    """Use case : renommer un fichier existant (propriétaire ou editor)."""

    def __init__(self, file_repository: FileRepository, share_repository: ShareRepository) -> None:
        """Injection de dépendances par constructeur.

        Args:
            file_repository: Port pour la persistance des métadonnées
            share_repository: Port pour la persistance des partages
        """
        self._file_repository = file_repository
        self._share_repository = share_repository

    def execute(self, file_id: str, new_name: str, user_id: str = DEFAULT_USER_ID) -> File:
        """Renomme un fichier.

        Args:
            file_id: Identifiant du fichier
            new_name: Nouveau nom (sera validé)
            user_id: Utilisateur agissant (propriétaire ou editor)

        Returns:
            Le fichier renommé

        Raises:
            UnknownFileError: Si l'ID est inconnu
            PermissionDeniedError: Si l'utilisateur ne peut pas écrire
            InvalidFileNameError: Si le nouveau nom est invalide
            FileAlreadyExistsError: Si un homonyme existe déjà dans le parent
        """
        file = self._file_repository.get(file_id)
        if file is None:
            raise UnknownFileError(file_id)
        if file.trashed:
            raise InTrashError(file_id)
        role = self._share_repository.role_for("file", file_id, user_id)
        require_write(file.owner_id, role, user_id, file_id)

        if new_name == file.name.value:
            return file  # no-op : déjà ce nom

        validated = FileName(new_name)
        if self._file_repository.exists_with_name(new_name, file.parent_id):
            raise FileAlreadyExistsError(new_name)

        file.name = validated
        self._file_repository.save(file)
        return file
