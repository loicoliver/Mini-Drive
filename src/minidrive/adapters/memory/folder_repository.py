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
        """Récupère un dossier par son identifiant (corbeille incluse)."""
        return self._folders.get(folder_id)

    def exists_with_name(self, name: str, parent_id: str | None) -> bool:
        """Vérifie si un dossier NON corbeillé avec ce nom existe dans le parent."""
        return any(
            folder.name.value == name and folder.parent_id == parent_id and not folder.trashed
            for folder in self._folders.values()
        )

    def list_all(self, include_trashed: bool = False) -> list[Folder]:
        """Liste les dossiers NON corbeillés, triés par nom."""
        folders = list(self._folders.values())
        if not include_trashed:
            folders = [folder for folder in folders if not folder.trashed]
        return sorted(folders, key=lambda folder: folder.name.value)

    def save(self, folder: Folder) -> None:
        """Crée ou remplace un dossier (upsert par identifiant)."""
        self._folders[folder.id] = folder

    def delete(self, folder_id: str) -> None:
        """Supprime définitivement un dossier (aucune erreur si absent)."""
        self._folders.pop(folder_id, None)
