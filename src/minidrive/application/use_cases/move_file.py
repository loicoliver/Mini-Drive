"""Use case pour déplacer un fichier (pattern Use Case / Command)."""

from minidrive.application.access import require_write
from minidrive.application.ports import FileRepository, FolderRepository, ShareRepository
from minidrive.application.users import DEFAULT_USER_ID
from minidrive.domain.entities import File
from minidrive.domain.errors import (
    FileAlreadyExistsError,
    InTrashError,
    InvalidMoveError,
    UnknownFileError,
    UnknownFolderError,
)


class MoveFile:
    """Use case : déplacer un fichier vers un dossier (propriétaire ou editor)."""

    def __init__(
        self,
        file_repository: FileRepository,
        folder_repository: FolderRepository,
        share_repository: ShareRepository,
    ) -> None:
        """Injection de dépendances par constructeur.

        Args:
            file_repository: Port pour la persistance des métadonnées
            folder_repository: Port pour vérifier le dossier de destination
            share_repository: Port pour la persistance des partages
        """
        self._file_repository = file_repository
        self._folder_repository = folder_repository
        self._share_repository = share_repository

    def execute(
        self, file_id: str, new_parent_id: str | None, user_id: str = DEFAULT_USER_ID
    ) -> File:
        """Déplace un fichier.

        Args:
            file_id: Identifiant du fichier à déplacer
            new_parent_id: Nouveau dossier parent (None pour la racine)
            user_id: Utilisateur agissant (propriétaire ou editor)

        Returns:
            Le fichier déplacé

        Raises:
            UnknownFileError: Si l'ID est inconnu
            PermissionDeniedError: Si l'utilisateur ne peut pas écrire
            UnknownFolderError: Si le dossier de destination est inconnu
            FileAlreadyExistsError: Si un homonyme existe déjà à destination
        """
        file = self._file_repository.get(file_id)
        if file is None:
            raise UnknownFileError(file_id)
        if file.trashed:
            raise InTrashError(file_id)
        role = self._share_repository.role_for("file", file_id, user_id)
        require_write(file.owner_id, role, user_id, file_id)

        if new_parent_id == file.parent_id:
            return file  # no-op : déjà à cet endroit

        if new_parent_id is not None:
            parent = self._folder_repository.get(new_parent_id)
            if parent is None:
                raise UnknownFolderError(new_parent_id)
            if parent.trashed:
                raise InvalidMoveError(new_parent_id, "destination dans la corbeille")

        if self._file_repository.exists_with_name(file.name.value, new_parent_id):
            raise FileAlreadyExistsError(file.name.value)

        file.parent_id = new_parent_id
        self._file_repository.save(file)
        return file
