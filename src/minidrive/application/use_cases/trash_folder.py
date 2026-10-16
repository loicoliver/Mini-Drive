"""Use cases pour la corbeille des dossiers (pattern Use Case / Command)."""

from minidrive.application.access import require_write
from minidrive.application.folder_tree import descendant_ids
from minidrive.application.ports import FolderRepository, ShareRepository
from minidrive.application.users import DEFAULT_USER_ID
from minidrive.domain.entities import Folder
from minidrive.domain.errors import UnknownFolderError


class TrashFolder:
    """Use case : mettre un dossier à la corbeille (propriétaire ou editor)."""

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

    def execute(self, folder_id: str, user_id: str = DEFAULT_USER_ID) -> Folder:
        """Met un dossier et ses descendants à la corbeille (idempotent).

        Args:
            folder_id: Identifiant du dossier
            user_id: Utilisateur agissant (propriétaire ou editor)

        Returns:
            Le dossier corbeillé

        Raises:
            UnknownFolderError: Si l'ID est inconnu
            PermissionDeniedError: Si l'utilisateur ne peut pas écrire
        """
        all_folders = self._folder_repository.list_all(include_trashed=True)
        matches = [folder for folder in all_folders if folder.id == folder_id]
        if not matches:
            raise UnknownFolderError(folder_id)
        role = self._share_repository.role_for("folder", folder_id, user_id)
        require_write(matches[0].owner_id, role, user_id, folder_id)

        to_trash = descendant_ids(all_folders, folder_id)
        to_trash.add(folder_id)
        for candidate in all_folders:
            if candidate.id in to_trash and not candidate.trashed:
                candidate.trashed = True
                self._folder_repository.save(candidate)

        trashed = self._folder_repository.get(folder_id)
        assert trashed is not None  # garanti : existe juste au-dessus
        return trashed


class RestoreFolder:
    """Use case : restaurer un dossier corbeillé (propriétaire ou editor)."""

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

    def execute(self, folder_id: str, user_id: str = DEFAULT_USER_ID) -> Folder:
        """Restaure un dossier et ses descendants (idempotent).

        Args:
            folder_id: Identifiant du dossier
            user_id: Utilisateur agissant (propriétaire ou editor)

        Returns:
            Le dossier restauré

        Raises:
            UnknownFolderError: Si l'ID est inconnu
            PermissionDeniedError: Si l'utilisateur ne peut pas écrire
        """
        all_folders = self._folder_repository.list_all(include_trashed=True)
        matches = [folder for folder in all_folders if folder.id == folder_id]
        if not matches:
            raise UnknownFolderError(folder_id)
        role = self._share_repository.role_for("folder", folder_id, user_id)
        require_write(matches[0].owner_id, role, user_id, folder_id)

        to_restore = descendant_ids(all_folders, folder_id)
        to_restore.add(folder_id)
        for candidate in all_folders:
            if candidate.id in to_restore and candidate.trashed:
                candidate.trashed = False
                self._folder_repository.save(candidate)

        restored = self._folder_repository.get(folder_id)
        assert restored is not None  # garanti : existe juste au-dessus
        return restored
