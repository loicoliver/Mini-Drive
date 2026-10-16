"""Use cases pour partager des dossiers (pattern Use Case / Command)."""

from minidrive.application.ports import FolderRepository, ShareRepository
from minidrive.application.sharing import ROLES
from minidrive.application.users import DEFAULT_USER_ID
from minidrive.domain.entities import Share
from minidrive.domain.errors import InvalidShareError, UnknownFolderError


class ShareFolder:
    """Use case : partager un dossier avec un utilisateur (seul le owner peut)."""

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

    def execute(
        self, folder_id: str, user_id: str, role: str, owner_id: str = DEFAULT_USER_ID
    ) -> Share:
        """Partage un dossier.

        Args:
            folder_id: Identifiant du dossier
            user_id: Utilisateur bénéficiaire
            role: "reader" ou "editor"
            owner_id: Utilisateur agissant (doit être le propriétaire)

        Returns:
            Le partage accordé

        Raises:
            UnknownFolderError: Si l'ID est inconnu
            InvalidShareError: Si rôle inconnu ou acteur non propriétaire
        """
        folder = self._folder_repository.get(folder_id)
        if folder is None:
            raise UnknownFolderError(folder_id)
        if folder.owner_id != owner_id:
            raise InvalidShareError("seul le propriétaire peut partager")
        if role not in ROLES:
            raise InvalidShareError(f"rôle inconnu '{role}' (attendu : reader|editor)")

        share = Share(node_type="folder", node_id=folder_id, user_id=user_id, role=role)
        self._share_repository.grant(share)
        return share


class UnshareFolder:
    """Use case : retirer un partage de dossier (seul le owner peut)."""

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

    def execute(self, folder_id: str, user_id: str, owner_id: str = DEFAULT_USER_ID) -> None:
        """Retire un partage (idempotent).

        Args:
            folder_id: Identifiant du dossier
            user_id: Utilisateur à retirer
            owner_id: Utilisateur agissant (doit être le propriétaire)

        Raises:
            UnknownFolderError: Si l'ID est inconnu
            InvalidShareError: Si l'acteur n'est pas propriétaire
        """
        folder = self._folder_repository.get(folder_id)
        if folder is None:
            raise UnknownFolderError(folder_id)
        if folder.owner_id != owner_id:
            raise InvalidShareError("seul le propriétaire peut retirer un partage")

        self._share_repository.revoke("folder", folder_id, user_id)
