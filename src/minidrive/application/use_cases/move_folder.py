"""Use case pour déplacer un dossier (pattern Use Case / Command)."""

from minidrive.application.access import require_write
from minidrive.application.folder_tree import descendant_ids
from minidrive.application.ports import FolderRepository, ShareRepository
from minidrive.application.users import DEFAULT_USER_ID
from minidrive.domain.entities import Folder
from minidrive.domain.errors import (
    FolderAlreadyExistsError,
    InTrashError,
    InvalidMoveError,
    UnknownFolderError,
)


class MoveFolder:
    """Use case : déplacer un dossier vers un autre parent (propriétaire ou editor)."""

    def __init__(
        self, folder_repository: FolderRepository, share_repository: ShareRepository
    ) -> None:
        """Injection de dépendances par constructeur.

        Args:
            folder_repository: Port pour la persistance des dossiers
            share_repository: Port pour la persistance des partages
        """
        self._folder_repository = folder_repository
        self._share_repository = share_repository

    def execute(
        self, folder_id: str, new_parent_id: str | None, user_id: str = DEFAULT_USER_ID
    ) -> Folder:
        """Déplace un dossier.

        Args:
            folder_id: Identifiant du dossier à déplacer
            new_parent_id: Nouveau parent (None pour la racine)
            user_id: Utilisateur agissant (propriétaire ou editor)

        Returns:
            Le dossier déplacé

        Raises:
            UnknownFolderError: Si l'ID ou le parent est inconnu
            PermissionDeniedError: Si l'utilisateur ne peut pas écrire
            InvalidMoveError: Si déplacement sur soi-même ou dans un descendant
            FolderAlreadyExistsError: Si un homonyme existe déjà à destination
        """
        folder = self._folder_repository.get(folder_id)
        if folder is None:
            raise UnknownFolderError(folder_id)
        if folder.trashed:
            raise InTrashError(folder_id)
        role = self._share_repository.role_for("folder", folder_id, user_id)
        require_write(folder.owner_id, role, user_id, folder_id)

        if new_parent_id == folder.parent_id:
            return folder  # no-op : déjà à cet endroit

        if new_parent_id == folder_id:
            raise InvalidMoveError(folder_id, "un dossier ne peut pas être son propre parent")

        if new_parent_id is not None:
            parent = self._folder_repository.get(new_parent_id)
            if parent is None:
                raise UnknownFolderError(new_parent_id)
            if parent.trashed:
                raise InvalidMoveError(new_parent_id, "destination dans la corbeille")
            descendants = descendant_ids(self._folder_repository.list_all(), folder_id)
            if new_parent_id in descendants:
                raise InvalidMoveError(
                    folder_id, "un dossier ne peut pas aller dans un de ses descendants"
                )

        if self._folder_repository.exists_with_name(folder.name.value, new_parent_id):
            raise FolderAlreadyExistsError(folder.name.value)

        folder.parent_id = new_parent_id
        self._folder_repository.save(folder)
        return folder
