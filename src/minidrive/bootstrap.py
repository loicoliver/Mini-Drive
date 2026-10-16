"""Bootstrap : composition root, seul endroit qui connaît toutes les couches.

Ce fichier assemble les dépendances et câble les adapteurs aux ports.
Démontre le principe D (Dependency Inversion) : l'injection se fait ici.
"""

import os
from pathlib import Path

from minidrive.adapters.memory.id_generator import UuidIdGenerator
from minidrive.adapters.sqlite.folder_repository import SqliteFolderRepository
from minidrive.application.use_cases.create_folder import CreateFolder

DEFAULT_DB_PATH = Path.home() / ".minidrive" / "minidrive.db"


def resolve_db_path() -> Path:
    """Résout le chemin du fichier SQLite (cross-platform).

    Priorité : variable d'environnement MINIDRIVE_DB (tests, debug),
    sinon ~/.minidrive/minidrive.db (dossier home de l'OS).
    """
    override = os.environ.get("MINIDRIVE_DB")
    if override:
        return Path(override)
    return DEFAULT_DB_PATH


class Container:
    """Conteneur d'injection de dépendances simplifié."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        """Initialise les adapteurs et use cases.

        Args:
            db_path: Chemin SQLite explicite (tests). Si None, resolve_db_path().
        """
        self._db_path = Path(db_path) if db_path is not None else resolve_db_path()
        # Adapteurs (implémentations concrètes)
        self._folder_repository = SqliteFolderRepository(self._db_path)
        self._id_generator = UuidIdGenerator()

        # Use cases (injection par constructeur)
        self._create_folder_use_case = CreateFolder(
            folder_repository=self._folder_repository,
            id_generator=self._id_generator,
        )

    @property
    def db_path(self) -> Path:
        """Chemin du fichier SQLite utilisé."""
        return self._db_path

    @property
    def create_folder(self) -> CreateFolder:
        """Accès au use case CreateFolder."""
        return self._create_folder_use_case


def create_container(db_path: Path | str | None = None) -> Container:
    """Factory pour créer le conteneur d'injection.

    Args:
        db_path: Chemin SQLite explicite (tests). Si None, resolve_db_path().

    Returns:
        Un conteneur configuré avec toutes les dépendances
    """
    return Container(db_path=db_path)
