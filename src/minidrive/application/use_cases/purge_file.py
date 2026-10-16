"""Use case pour purger définitivement un fichier (pattern Use Case / Command)."""

from minidrive.application.ports import BlobStorage, FileRepository, ShareRepository
from minidrive.application.quota_policies import QuotaPolicy
from minidrive.application.users import DEFAULT_USER_ID
from minidrive.domain.errors import UnknownFileError


class PurgeFile:
    """Use case : supprimer définitivement un fichier (métadonnées + blob).

    Libère le quota. Irréversible, contrairement à la corbeille.
    """

    def __init__(
        self,
        file_repository: FileRepository,
        blob_storage: BlobStorage,
        quota_policy: QuotaPolicy,
        share_repository: ShareRepository,
    ) -> None:
        """Injection de dépendances par constructeur.

        Args:
            file_repository: Port pour la persistance des métadonnées
            blob_storage: Port pour le stockage du contenu binaire
            quota_policy: Politique de quota (libération au purge)
            share_repository: Port des partages (nettoyés au purge)
        """
        self._file_repository = file_repository
        self._blob_storage = blob_storage
        self._quota_policy = quota_policy
        self._share_repository = share_repository

    def execute(self, file_id: str, user_id: str = DEFAULT_USER_ID) -> None:
        """Purge un fichier.

        Args:
            file_id: Identifiant du fichier
            user_id: Identifiant de l'utilisateur (libération du quota)

        Raises:
            UnknownFileError: Si l'ID est inconnu
        """
        file = self._file_repository.get(file_id)
        if file is None:
            raise UnknownFileError(file_id)

        self._blob_storage.delete(file_id)
        self._file_repository.delete(file_id)
        self._quota_policy.record_removal(user_id, file.size.value)
        self._share_repository.delete_for_node("file", file_id)
