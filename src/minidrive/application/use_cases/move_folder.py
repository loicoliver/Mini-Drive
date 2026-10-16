"""Use case pour déplacer un dossier (pattern Use Case / Command)."""

from minidrive.application.ports import FolderRepository
from minidrive.domain.entities import Folder
from minidrive.domain.errors import (
    FolderAlreadyExistsError,
    InvalidMoveError,
    UnknownFolderError,
)


class MoveFolder:
    """Use case : déplacer un dossier vers un autre parent (ou la racine)."""

    def __init__(self, folder_repository: FolderRepository) -> None:
        """Injection de dépendances par constructeur.

        Args:
            folder_repository: Port pour la persistance des dossiers
        """
        self._folder_repository = folder_repository

    def execute(self, folder_id: str, new_parent_id: str | None) -> Folder:
        """Déplace un dossier.

        Args:
            folder_id: Identifiant du dossier à déplacer
            new_parent_id: Nouveau parent (None pour la racine)

        Returns:
            Le dossier déplacé

        Raises:
            UnknownFolderError: Si l'ID ou le parent est inconnu
            InvalidMoveError: Si déplacement sur soi-même ou dans un descendant
            FolderAlreadyExistsError: Si un homonyme existe déjà à destination
        """
        folder = self._folder_repository.get(folder_id)
        if folder is None:
            raise UnknownFolderError(folder_id)

        if new_parent_id == folder.parent_id:
            return folder  # no-op : déjà à cet endroit

        if new_parent_id == folder_id:
            raise InvalidMoveError(folder_id, "un dossier ne peut pas être son propre parent")

        if new_parent_id is not None:
            parent = self._folder_repository.get(new_parent_id)
            if parent is None:
                raise UnknownFolderError(new_parent_id)
            if new_parent_id in self._descendant_ids(folder_id):
                raise InvalidMoveError(
                    folder_id, "un dossier ne peut pas aller dans un de ses descendants"
                )

        if self._folder_repository.exists_with_name(folder.name.value, new_parent_id):
            raise FolderAlreadyExistsError(folder.name.value)

        folder.parent_id = new_parent_id
        self._folder_repository.save(folder)
        return folder

    def _descendant_ids(self, folder_id: str) -> set[str]:
        """Retourne tous les descendants d'un dossier (parcours en mémoire)."""
        children: dict[str | None, list[str]] = {}
        for candidate in self._folder_repository.list_all():
            children.setdefault(candidate.parent_id, []).append(candidate.id)

        descendants: set[str] = set()
        stack = [folder_id]
        while stack:
            for child_id in children.get(stack.pop(), []):
                if child_id not in descendants:
                    descendants.add(child_id)
                    stack.append(child_id)
        return descendants
