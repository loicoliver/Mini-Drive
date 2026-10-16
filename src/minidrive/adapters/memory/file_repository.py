"""Implémentation en mémoire du FileRepository (pattern Adapter)."""

from minidrive.application.ports import FileRepository
from minidrive.domain.entities import File


class InMemoryFileRepository(FileRepository):
    """Repository en mémoire pour les tests (isolation, rapidité)."""

    def __init__(self) -> None:
        """Initialise le stockage en mémoire."""
        self._files: dict[str, File] = {}

    def add(self, file: File) -> None:
        """Ajoute un fichier au repository."""
        self._files[file.id] = file

    def get(self, file_id: str) -> File | None:
        """Récupère un fichier par son identifiant."""
        return self._files.get(file_id)

    def exists_with_name(self, name: str, parent_id: str | None) -> bool:
        """Vérifie si un fichier avec ce nom existe déjà dans le même parent."""
        return any(
            file.name.value == name and file.parent_id == parent_id for file in self._files.values()
        )

    def list_all(self) -> list[File]:
        """Liste tous les fichiers, triés par nom."""
        return sorted(self._files.values(), key=lambda file: file.name.value)

    def save(self, file: File) -> None:
        """Crée ou remplace un fichier (upsert par identifiant)."""
        self._files[file.id] = file
