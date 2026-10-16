"""Use case pour renommer un dossier (pattern Use Case / Command)."""

from minidrive.application.ports import FolderRepository
from minidrive.domain.entities import Folder
from minidrive.domain.errors import FolderAlreadyExistsError, InTrashError, UnknownFolderError
from minidrive.domain.value_objects import FileName


class RenameFolder:
    """Use case : renommer un dossier existant."""

    def __init__(self, folder_repository: FolderRepository) -> None:
        """Injection de dépendances par constructeur.

        Args:
            folder_repository: Port pour la persistance des dossiers
        """
        self._folder_repository = folder_repository

    def execute(self, folder_id: str, new_name: str) -> Folder:
        """Renomme un dossier.

        Args:
            folder_id: Identifiant du dossier
            new_name: Nouveau nom (sera validé)

        Returns:
            Le dossier renommé

        Raises:
            UnknownFolderError: Si l'ID est inconnu
            InvalidFileNameError: Si le nouveau nom est invalide
            FolderAlreadyExistsError: Si un homonyme existe déjà dans le parent
        """
        folder = self._folder_repository.get(folder_id)
        if folder is None:
            raise UnknownFolderError(folder_id)
        if folder.trashed:
            raise InTrashError(folder_id)

        if new_name == folder.name.value:
            return folder  # no-op : déjà ce nom

        validated = FileName(new_name)
        if self._folder_repository.exists_with_name(new_name, folder.parent_id):
            raise FolderAlreadyExistsError(new_name)

        folder.name = validated
        self._folder_repository.save(folder)
        return folder
