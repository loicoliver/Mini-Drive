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

    def execute(
        self,
        user_id: str = DEFAULT_USER_ID,
        trashed_only: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[File]:
        """Liste les fichiers visibles, triés par nom.

        Args:
            user_id: Utilisateur agissant (possédés + partagés)
            trashed_only: True pour ne voir que la corbeille (vue `ls --corbeille`)
            limit: Nombre max de résultats (None = tout)
            offset: Nombre de résultats à sauter

        Returns:
            Les fichiers visibles, par nom croissant
        """
        visible: list[File] = []
        for file in self._file_repository.list_all(include_trashed=trashed_only):
            if trashed_only and not file.trashed:
                continue
            shared = self._share_repository.role_for("file", file.id, user_id)
            if file.owner_id == user_id or shared is not None:
                visible.append(file)
        ordered = sorted(visible, key=lambda file: file.name.value)
        if limit is None:
            return ordered[offset:]
        return ordered[offset : offset + limit]
