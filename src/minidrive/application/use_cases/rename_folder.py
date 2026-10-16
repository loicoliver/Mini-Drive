"""Use case pour renommer un dossier (pattern Use Case / Command)."""

from minidrive.application.access import require_write
from minidrive.application.ports import FolderRepository, ShareRepository
from minidrive.application.users import DEFAULT_USER_ID
from minidrive.domain.entities import Folder
from minidrive.domain.errors import FolderAlreadyExistsError, InTrashError, UnknownFolderError
from minidrive.domain.value_objects import FileName


class RenameFolder:
    """Use case : renommer un dossier existant (propriétaire ou editor)."""

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

    def execute(self, folder_id: str, new_name: str, user_id: str = DEFAULT_USER_ID) -> Folder:
        """Renomme un dossier.

        Args:
            folder_id: Identifiant du dossier
            new_name: Nouveau nom (sera validé)
            user_id: Utilisateur agissant (propriétaire ou editor)

        Returns:
            Le dossier renommé

        Raises:
            UnknownFolderError: Si l'ID est inconnu
            PermissionDeniedError: Si l'utilisateur ne peut pas écrire
            InvalidFileNameError: Si le nouveau nom est invalide
            FolderAlreadyExistsError: Si un homonyme existe déjà dans le parent
        """
        folder = self._folder_repository.get(folder_id)
        if folder is None:
            raise UnknownFolderError(folder_id)
        if folder.trashed:
            raise InTrashError(folder_id)
        role = self._share_repository.role_for("folder", folder_id, user_id)
        require_write(folder.owner_id, role, user_id, folder_id)

        if new_name == folder.name.value:
            return folder  # no-op : déjà ce nom

        validated = FileName(new_name)
        if self._folder_repository.exists_with_name(new_name, folder.parent_id):
            raise FolderAlreadyExistsError(new_name)

        folder.name = validated
        self._folder_repository.save(folder)
        return folder
