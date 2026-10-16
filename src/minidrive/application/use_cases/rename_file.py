"""Use case pour renommer un fichier (pattern Use Case / Command)."""

from minidrive.application.ports import FileRepository
from minidrive.domain.entities import File
from minidrive.domain.errors import FileAlreadyExistsError, UnknownFileError
from minidrive.domain.value_objects import FileName


class RenameFile:
    """Use case : renommer un fichier existant (métadonnées, contenu inchangé)."""

    def __init__(self, file_repository: FileRepository) -> None:
        """Injection de dépendances par constructeur.

        Args:
            file_repository: Port pour la persistance des métadonnées
        """
        self._file_repository = file_repository

    def execute(self, file_id: str, new_name: str) -> File:
        """Renomme un fichier.

        Args:
            file_id: Identifiant du fichier
            new_name: Nouveau nom (sera validé)

        Returns:
            Le fichier renommé

        Raises:
            UnknownFileError: Si l'ID est inconnu
            InvalidFileNameError: Si le nouveau nom est invalide
            FileAlreadyExistsError: Si un homonyme existe déjà dans le parent
        """
        file = self._file_repository.get(file_id)
        if file is None:
            raise UnknownFileError(file_id)

        if new_name == file.name.value:
            return file  # no-op : déjà ce nom

        validated = FileName(new_name)
        if self._file_repository.exists_with_name(new_name, file.parent_id):
            raise FileAlreadyExistsError(new_name)

        file.name = validated
        self._file_repository.save(file)
        return file
