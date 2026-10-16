"""Use case pour télécharger un fichier (pattern Use Case / Command)."""

from minidrive.application.access import require_read
from minidrive.application.ports import BlobStorage, FileRepository, ShareRepository
from minidrive.application.users import DEFAULT_USER_ID
from minidrive.domain.entities import File
from minidrive.domain.errors import InTrashError, UnknownFileError


class DownloadFile:
    """Use case : télécharger un fichier par son identifiant (lecture autorisée).

    Retourne métadonnées + contenu : l'écriture sur disque est une
    préoccupation d'interface (CLI), pas d'application.
    Démontre le principe S (Single Responsibility) : une seule action métier.
    """

    def __init__(
        self,
        file_repository: FileRepository,
        blob_storage: BlobStorage,
        share_repository: ShareRepository,
    ) -> None:
        """Injection de dépendances par constructeur.

        Args:
            file_repository: Port pour la persistance des métadonnées
            blob_storage: Port pour le stockage du contenu binaire
            share_repository: Port pour la persistance des partages
        """
        self._file_repository = file_repository
        self._blob_storage = blob_storage
        self._share_repository = share_repository

    def execute(self, file_id: str, user_id: str = DEFAULT_USER_ID) -> tuple[File, bytes]:
        """Télécharge un fichier.

        Args:
            file_id: Identifiant unique du fichier
            user_id: Utilisateur agissant (propriétaire, reader ou editor)

        Returns:
            Le couple (métadonnées, contenu binaire)

        Raises:
            UnknownFileError: Si l'ID est inconnu ou le contenu absent
            PermissionDeniedError: Si l'utilisateur ne peut pas lire
        """
        file = self._file_repository.get(file_id)
        if file is None:
            raise UnknownFileError(file_id)
        if file.trashed:
            raise InTrashError(file_id)
        role = self._share_repository.role_for("file", file_id, user_id)
        require_read(file.owner_id, role, user_id, file_id)

        data = self._blob_storage.read(file_id)
        if data is None:
            raise UnknownFileError(file_id)

        return file, data
