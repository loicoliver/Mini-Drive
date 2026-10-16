"""Use case pour lister les fichiers (pattern Use Case / Command)."""

from minidrive.application.ports import FileRepository, ShareRepository
from minidrive.application.users import DEFAULT_USER_ID
from minidrive.domain.entities import File


class ListFiles:
    """Use case : lister les fichiers visibles par l'utilisateur.

    Seuls les fichiers possédés ou partagés sont retournés.
    Démontre le principe S (Single Responsibility) : une seule action métier.
    Démontre le principe D (Dependency Inversion) : dépend des abstractions (ports).
    """

    def __init__(self, file_repository: FileRepository, share_repository: ShareRepository) -> None:
        """Injection de dépendances par constructeur.

        Args:
            file_repository: Port pour la persistance des métadonnées
            share_repository: Port pour la persistance des partages
        """
        self._file_repository = file_repository
        self._share_repository = share_repository

    def execute(self, user_id: str = DEFAULT_USER_ID) -> list[File]:
        """Liste les fichiers visibles, triés par nom.

        Args:
            user_id: Utilisateur agissant (possédés + partagés)

        Returns:
            Les fichiers visibles, par nom croissant
        """
        visible: list[File] = []
        for file in self._file_repository.list_all():
            shared = self._share_repository.role_for("file", file.id, user_id)
            if file.owner_id == user_id or shared is not None:
                visible.append(file)
        return sorted(visible, key=lambda file: file.name.value)
