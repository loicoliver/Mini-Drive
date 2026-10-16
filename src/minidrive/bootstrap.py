"""Bootstrap : composition root, seul endroit qui connaît toutes les couches.

Ce fichier assemble les dépendances et câble les adapteurs aux ports.
Démontre le principe D (Dependency Inversion) : l'injection se fait ici.
"""

import os
from pathlib import Path

from minidrive.adapters.filesystem.blob_storage import FilesystemBlobStorage
from minidrive.adapters.memory.id_generator import UuidIdGenerator
from minidrive.adapters.sqlite.file_repository import SqliteFileRepository
from minidrive.adapters.sqlite.folder_repository import SqliteFolderRepository
from minidrive.application.quota_policies import QuotaPolicy, UnlimitedQuotaPolicy
from minidrive.application.use_cases.create_folder import CreateFolder
from minidrive.application.use_cases.download_file import DownloadFile
from minidrive.application.use_cases.list_files import ListFiles
from minidrive.application.use_cases.list_folders import ListFolders
from minidrive.application.use_cases.move_file import MoveFile
from minidrive.application.use_cases.move_folder import MoveFolder
from minidrive.application.use_cases.rename_file import RenameFile
from minidrive.application.use_cases.rename_folder import RenameFolder
from minidrive.application.use_cases.upload_file import UploadFile

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

    def __init__(
        self,
        db_path: Path | str | None = None,
        quota_policy: QuotaPolicy | None = None,
    ) -> None:
        """Initialise les adapteurs et use cases.

        Args:
            db_path: Chemin SQLite explicite (tests). Si None, resolve_db_path().
            quota_policy: Politique de quota (UnlimitedQuotaPolicy par défaut).
        """
        self._db_path = Path(db_path) if db_path is not None else resolve_db_path()
        # Adapteurs (implémentations concrètes)
        self._folder_repository = SqliteFolderRepository(self._db_path)
        self._file_repository = SqliteFileRepository(self._db_path)
        self._blob_storage = FilesystemBlobStorage(self._db_path.parent / "blobs")
        self._id_generator = UuidIdGenerator()
        self._quota_policy = quota_policy or UnlimitedQuotaPolicy()

        # Use cases (injection par constructeur)
        self._create_folder_use_case = CreateFolder(
            folder_repository=self._folder_repository,
            id_generator=self._id_generator,
        )
        self._list_folders_use_case = ListFolders(
            folder_repository=self._folder_repository,
        )
        self._upload_file_use_case = UploadFile(
            file_repository=self._file_repository,
            blob_storage=self._blob_storage,
            id_generator=self._id_generator,
            quota_policy=self._quota_policy,
        )
        self._list_files_use_case = ListFiles(
            file_repository=self._file_repository,
        )
        self._download_file_use_case = DownloadFile(
            file_repository=self._file_repository,
            blob_storage=self._blob_storage,
        )
        self._rename_folder_use_case = RenameFolder(
            folder_repository=self._folder_repository,
        )
        self._rename_file_use_case = RenameFile(
            file_repository=self._file_repository,
        )
        self._move_folder_use_case = MoveFolder(
            folder_repository=self._folder_repository,
        )
        self._move_file_use_case = MoveFile(
            file_repository=self._file_repository,
            folder_repository=self._folder_repository,
        )

    @property
    def db_path(self) -> Path:
        """Chemin du fichier SQLite utilisé."""
        return self._db_path

    @property
    def create_folder(self) -> CreateFolder:
        """Accès au use case CreateFolder."""
        return self._create_folder_use_case

    @property
    def list_folders(self) -> ListFolders:
        """Accès au use case ListFolders."""
        return self._list_folders_use_case

    @property
    def upload_file(self) -> UploadFile:
        """Accès au use case UploadFile."""
        return self._upload_file_use_case

    @property
    def list_files(self) -> ListFiles:
        """Accès au use case ListFiles."""
        return self._list_files_use_case

    @property
    def download_file(self) -> DownloadFile:
        """Accès au use case DownloadFile."""
        return self._download_file_use_case

    @property
    def rename_folder(self) -> RenameFolder:
        """Accès au use case RenameFolder."""
        return self._rename_folder_use_case

    @property
    def rename_file(self) -> RenameFile:
        """Accès au use case RenameFile."""
        return self._rename_file_use_case

    @property
    def move_folder(self) -> MoveFolder:
        """Accès au use case MoveFolder."""
        return self._move_folder_use_case

    @property
    def move_file(self) -> MoveFile:
        """Accès au use case MoveFile."""
        return self._move_file_use_case


def create_container(
    db_path: Path | str | None = None,
    quota_policy: QuotaPolicy | None = None,
) -> Container:
    """Factory pour créer le conteneur d'injection.

    Args:
        db_path: Chemin SQLite explicite (tests). Si None, resolve_db_path().
        quota_policy: Politique de quota (UnlimitedQuotaPolicy par défaut).

    Returns:
        Un conteneur configuré avec toutes les dépendances
    """
    return Container(db_path=db_path, quota_policy=quota_policy)
