"""Use case pour déplacer un fichier (pattern Use Case / Command)."""

from minidrive.application.ports import FileRepository, FolderRepository
from minidrive.domain.entities import File
from minidrive.domain.errors import (
    FileAlreadyExistsError,
    UnknownFileError,
    UnknownFolderError,
)


class MoveFile:
    """Use case : déplacer un fichier vers un dossier (ou la racine)."""

    def __init__(
        self, file_repository: FileRepository, folder_repository: FolderRepository
    ) -> None:
        """Injection de dépendances par constructeur.

        Args:
            file_repository: Port pour la persistance des métadonnées
            folder_repository: Port pour vérifier le dossier de destination
        """
        self._file_repository = file_repository
        self._folder_repository = folder_repository

    def execute(self, file_id: str, new_parent_id: str | None) -> File:
        """Déplace un fichier.

        Args:
            file_id: Identifiant du fichier à déplacer
            new_parent_id: Nouveau dossier parent (None pour la racine)

        Returns:
            Le fichier déplacé

        Raises:
            UnknownFileError: Si l'ID est inconnu
            UnknownFolderError: Si le dossier de destination est inconnu
            FileAlreadyExistsError: Si un homonyme existe déjà à destination
        """
        file = self._file_repository.get(file_id)
        if file is None:
            raise UnknownFileError(file_id)

        if new_parent_id == file.parent_id:
            return file  # no-op : déjà à cet endroit

        if new_parent_id is not None and self._folder_repository.get(new_parent_id) is None:
            raise UnknownFolderError(new_parent_id)

        if self._file_repository.exists_with_name(file.name.value, new_parent_id):
            raise FileAlreadyExistsError(file.name.value)

        file.parent_id = new_parent_id
        self._file_repository.save(file)
        return file
