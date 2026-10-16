"""Use cases pour partager des fichiers (pattern Use Case / Command)."""

from minidrive.application.ports import FileRepository, ShareRepository
from minidrive.application.sharing import ROLES
from minidrive.application.users import DEFAULT_USER_ID
from minidrive.domain.entities import Share
from minidrive.domain.errors import InvalidShareError, UnknownFileError


class ShareFile:
    """Use case : partager un fichier avec un utilisateur (seul le owner peut)."""

    def __init__(self, file_repository: FileRepository, share_repository: ShareRepository) -> None:
        """Injection de dépendances par constructeur.

        Args:
            file_repository: Port pour la persistance des métadonnées
            share_repository: Port pour la persistance des partages
        """
        self._file_repository = file_repository
        self._share_repository = share_repository

    def execute(
        self, file_id: str, user_id: str, role: str, owner_id: str = DEFAULT_USER_ID
    ) -> Share:
        """Partage un fichier.

        Args:
            file_id: Identifiant du fichier
            user_id: Utilisateur bénéficiaire
            role: "reader" ou "editor"
            owner_id: Utilisateur agissant (doit être le propriétaire)

        Returns:
            Le partage accordé

        Raises:
            UnknownFileError: Si l'ID est inconnu
            InvalidShareError: Si rôle inconnu ou acteur non propriétaire
        """
        file = self._file_repository.get(file_id)
        if file is None:
            raise UnknownFileError(file_id)
        if file.owner_id != owner_id:
            raise InvalidShareError("seul le propriétaire peut partager")
        if role not in ROLES:
            raise InvalidShareError(f"rôle inconnu '{role}' (attendu : reader|editor)")

        share = Share(node_type="file", node_id=file_id, user_id=user_id, role=role)
        self._share_repository.grant(share)
        return share


class UnshareFile:
    """Use case : retirer un partage de fichier (seul le owner peut)."""

    def __init__(self, file_repository: FileRepository, share_repository: ShareRepository) -> None:
        """Injection de dépendances par constructeur.

        Args:
            file_repository: Port pour la persistance des métadonnées
            share_repository: Port pour la persistance des partages
        """
        self._file_repository = file_repository
        self._share_repository = share_repository

    def execute(self, file_id: str, user_id: str, owner_id: str = DEFAULT_USER_ID) -> None:
        """Retire un partage (idempotent).

        Args:
            file_id: Identifiant du fichier
            user_id: Utilisateur à retirer
            owner_id: Utilisateur agissant (doit être le propriétaire)

        Raises:
            UnknownFileError: Si l'ID est inconnu
            InvalidShareError: Si l'acteur n'est pas propriétaire
        """
        file = self._file_repository.get(file_id)
        if file is None:
            raise UnknownFileError(file_id)
        if file.owner_id != owner_id:
            raise InvalidShareError("seul le propriétaire peut retirer un partage")

        self._share_repository.revoke("file", file_id, user_id)
