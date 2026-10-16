"""Use cases pour la corbeille des dossiers (pattern Use Case / Command)."""

from minidrive.application.folder_tree import descendant_ids
from minidrive.application.ports import FolderRepository
from minidrive.domain.entities import Folder
from minidrive.domain.errors import UnknownFolderError


class TrashFolder:
    """Use case : mettre un dossier à la corbeille (avec tout son contenu)."""

    def __init__(self, folder_repository: FolderRepository) -> None:
        """Injection de dépendances par constructeur.

        Args:
            folder_repository: Port pour la persistance des dossiers
        """
        self._folder_repository = folder_repository

    def execute(self, folder_id: str) -> Folder:
        """Met un dossier et ses descendants à la corbeille (idempotent).

        Args:
            folder_id: Identifiant du dossier

        Returns:
            Le dossier corbeillé

        Raises:
            UnknownFolderError: Si l'ID est inconnu
        """
        all_folders = self._folder_repository.list_all(include_trashed=True)
        matches = [folder for folder in all_folders if folder.id == folder_id]
        if not matches:
            raise UnknownFolderError(folder_id)

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
    """Use case : restaurer un dossier corbeillé (avec tout son contenu)."""

    def __init__(self, folder_repository: FolderRepository) -> None:
        """Injection de dépendances par constructeur.

        Args:
            folder_repository: Port pour la persistance des dossiers
        """
        self._folder_repository = folder_repository

    def execute(self, folder_id: str) -> Folder:
        """Restaure un dossier et ses descendants (idempotent).

        Args:
            folder_id: Identifiant du dossier

        Returns:
            Le dossier restauré

        Raises:
            UnknownFolderError: Si l'ID est inconnu
        """
        all_folders = self._folder_repository.list_all(include_trashed=True)
        matches = [folder for folder in all_folders if folder.id == folder_id]
        if not matches:
            raise UnknownFolderError(folder_id)

        to_restore = descendant_ids(all_folders, folder_id)
        to_restore.add(folder_id)
        for candidate in all_folders:
            if candidate.id in to_restore and candidate.trashed:
                candidate.trashed = False
                self._folder_repository.save(candidate)

        restored = self._folder_repository.get(folder_id)
        assert restored is not None  # garanti : existe juste au-dessus
        return restored
