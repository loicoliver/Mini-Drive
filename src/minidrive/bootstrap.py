"""Bootstrap : composition root, seul endroit qui connaît toutes les couches.

Ce fichier assemble les dépendances et câble les adapteurs aux ports.
Démontre le principe D (Dependency Inversion) : l'injection se fait ici.
"""

from minidrive.adapters.memory.folder_repository import InMemoryFolderRepository
from minidrive.adapters.memory.id_generator import UuidIdGenerator
from minidrive.application.use_cases.create_folder import CreateFolder


class Container:
    """Conteneur d'injection de dépendances simplifié."""

    def __init__(self) -> None:
        """Initialise les adapteurs et use cases."""
        # Adapteurs (implémentations concrètes)
        self._folder_repository = InMemoryFolderRepository()
        self._id_generator = UuidIdGenerator()

        # Use cases (injection par constructeur)
        self._create_folder_use_case = CreateFolder(
            folder_repository=self._folder_repository,
            id_generator=self._id_generator,
        )

    @property
    def create_folder(self) -> CreateFolder:
        """Accès au use case CreateFolder."""
        return self._create_folder_use_case


def create_container() -> Container:
    """Factory pour créer le conteneur d'injection.

    Returns:
        Un conteneur configuré avec toutes les dépendances
    """
    return Container()
