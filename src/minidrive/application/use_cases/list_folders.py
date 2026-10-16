"""Use case pour lister les dossiers (pattern Use Case / Command)."""

from minidrive.application.ports import FolderRepository, ShareRepository
from minidrive.application.users import DEFAULT_USER_ID
from minidrive.domain.entities import Folder


class ListFolders:
    """Use case : lister les dossiers visibles par l'utilisateur.

    Seuls les dossiers possédés ou partagés sont retournés.
    Démontre le principe S (Single Responsibility) : une seule action métier.
    Démontre le principe D (Dependency Inversion) : dépend des abstractions (ports).
    """

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

    def execute(self, user_id: str = DEFAULT_USER_ID) -> list[Folder]:
        """Liste les dossiers visibles, triés par nom.

        Args:
            user_id: Utilisateur agissant (possédés + partagés)

        Returns:
            Les dossiers visibles, par nom croissant
        """
        visible: list[Folder] = []
        for folder in self._folder_repository.list_all():
            shared = self._share_repository.role_for("folder", folder.id, user_id)
            if folder.owner_id == user_id or shared is not None:
                visible.append(folder)
        return sorted(visible, key=lambda folder: folder.name.value)
