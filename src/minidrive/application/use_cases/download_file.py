"""Use case pour télécharger un fichier (pattern Use Case / Command)."""

from minidrive.application.ports import BlobStorage, FileRepository
from minidrive.domain.entities import File
from minidrive.domain.errors import UnknownFileError


class DownloadFile:
    """Use case : télécharger un fichier par son identifiant.

    Retourne métadonnées + contenu : l'écriture sur disque est une
    préoccupation d'interface (CLI), pas d'application.
    Démontre le principe S (Single Responsibility) : une seule action métier.
    """

    def __init__(
        self,
        file_repository: FileRepository,
        blob_storage: BlobStorage,
    ) -> None:
        """Injection de dépendances par constructeur.

        Args:
            file_repository: Port pour la persistance des métadonnées
            blob_storage: Port pour le stockage du contenu binaire
        """
        self._file_repository = file_repository
        self._blob_storage = blob_storage

    def execute(self, file_id: str) -> tuple[File, bytes]:
        """Télécharge un fichier.

        Args:
            file_id: Identifiant unique du fichier

        Returns:
            Le couple (métadonnées, contenu binaire)

        Raises:
            UnknownFileError: Si l'ID est inconnu ou le contenu absent
        """
        file = self._file_repository.get(file_id)
        if file is None:
            raise UnknownFileError(file_id)

        data = self._blob_storage.read(file_id)
        if data is None:
            raise UnknownFileError(file_id)

        return file, data
