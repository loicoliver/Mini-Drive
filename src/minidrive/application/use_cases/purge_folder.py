"""Use case pour purger définitivement un dossier (pattern Use Case / Command)."""

from minidrive.application.folder_tree import descendant_ids
from minidrive.application.ports import (
    BlobStorage,
    FileRepository,
    FolderRepository,
    ShareRepository,
)
from minidrive.application.quota_policies import QuotaPolicy
from minidrive.application.users import DEFAULT_USER_ID
from minidrive.domain.errors import UnknownFolderError


class PurgeFolder:
    """Use case : supprimer définitivement un dossier et tout son contenu.

    Récursif : fichiers (métadonnées + blobs + quota libéré) et sous-dossiers.
    Irréversible, contrairement à la corbeille.
    """

    def __init__(
        self,
        folder_repository: FolderRepository,
        file_repository: FileRepository,
        blob_storage: BlobStorage,
        quota_policy: QuotaPolicy,
        share_repository: ShareRepository,
    ) -> None:
        """Injection de dépendances par constructeur.

        Args:
            folder_repository: Port pour la persistance des dossiers
            file_repository: Port pour la persistance des métadonnées
            blob_storage: Port pour le stockage du contenu binaire
            quota_policy: Politique de quota (libération au purge)
            share_repository: Port des partages (nettoyés au purge)
        """
        self._folder_repository = folder_repository
        self._file_repository = file_repository
        self._blob_storage = blob_storage
        self._quota_policy = quota_policy
        self._share_repository = share_repository

    def execute(self, folder_id: str, user_id: str = DEFAULT_USER_ID) -> None:
        """Purge un dossier, ses sous-dossiers et leurs fichiers.

        Args:
            folder_id: Identifiant du dossier
            user_id: Identifiant de l'utilisateur (libération du quota)

        Raises:
            UnknownFolderError: Si l'ID est inconnu
        """
        all_folders = self._folder_repository.list_all(include_trashed=True)
        if all(folder.id != folder_id for folder in all_folders):
            raise UnknownFolderError(folder_id)

        doomed_folders = descendant_ids(all_folders, folder_id)
        doomed_folders.add(folder_id)

        for file in self._file_repository.list_all(include_trashed=True):
            if file.parent_id in doomed_folders:
                self._blob_storage.delete(file.id)
                self._file_repository.delete(file.id)
                self._quota_policy.record_removal(user_id, file.size.value)
                self._share_repository.delete_for_node("file", file.id)

        for doomed_id in doomed_folders:
            self._folder_repository.delete(doomed_id)
            self._share_repository.delete_for_node("folder", doomed_id)
