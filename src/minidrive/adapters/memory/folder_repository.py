"""Implémentation en mémoire du FolderRepository (pattern Adapter)."""

from minidrive.application.ports import FolderRepository
from minidrive.domain.entities import Folder


class InMemoryFolderRepository(FolderRepository):
    """Repository en mémoire pour les tests et la démonstration.

    Démontre le principe L (Liskov) : peut remplacer FolderRepository.
    Démontre le principe O (Open/Closed) : ajouter une nouvelle implémentation
    sans modifier le code existant.
    """

    def __init__(self) -> None:
        """Initialise le stockage en mémoire."""
        self._folders: dict[str, Folder] = {}

    def add(self, folder: Folder) -> None:
        """Ajoute un dossier au repository."""
        self._folders[folder.id] = folder

    def get(self, folder_id: str) -> Folder | None:
        """Récupère un dossier par son identifiant."""
        return self._folders.get(folder_id)

    def exists_with_name(self, name: str, parent_id: str | None) -> bool:
        """Vérifie si un dossier avec ce nom existe déjà dans le même parent."""
        return any(
            folder.name.value == name and folder.parent_id == parent_id
            for folder in self._folders.values()
        )
