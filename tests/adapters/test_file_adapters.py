"""Tests spécifiques aux adapteurs fichiers/blobs (au-delà des contrats)."""

from pathlib import Path

from minidrive.adapters.filesystem.blob_storage import FilesystemBlobStorage
from minidrive.adapters.memory.blob_storage import InMemoryBlobStorage
from minidrive.adapters.memory.file_repository import InMemoryFileRepository
from minidrive.adapters.sqlite.file_repository import SqliteFileRepository
from minidrive.adapters.sqlite.folder_repository import SqliteFolderRepository
from minidrive.domain.entities import File, Folder
from minidrive.domain.value_objects import FileName, FileSize


class TestSqliteFileAndFolderCoexistence:
    """Les tables files et folders doivent coexister dans le même .db."""

    def test_folders_and_files_share_database(self, tmp_path: Path) -> None:
        """Les deux repositories sur le même fichier ne se marchent pas dessus."""
        db_path = tmp_path / "shared.db"
        folder_repo = SqliteFolderRepository(db_path)
        file_repo = SqliteFileRepository(db_path)

        folder_repo.add(Folder.create(id="d1", name=FileName("docs")))
        file_repo.add(
            File.create(id="f1", name=FileName("a.txt"), size=FileSize(3), parent_id="d1")
        )

        assert folder_repo.get("d1") is not None
        assert folder_repo.get("f1") is None
        assert file_repo.get("f1") is not None
        assert file_repo.get("d1") is None


class TestFilesystemBlobStorageSpecifics:
    """Tests spécifiques au stockage filesystem."""

    def test_creates_root_directory(self, tmp_path: Path) -> None:
        """Le dossier racine des blobs doit être créé si absent."""
        root = tmp_path / "nested" / "blobs"

        storage = FilesystemBlobStorage(root)
        storage.write("f1", b"data")

        assert (root / "f1").exists()

    def test_blobs_are_files_on_disk(self, tmp_path: Path) -> None:
        """Chaque blob doit être un fichier nommé d'après l'ID."""
        storage = FilesystemBlobStorage(tmp_path / "blobs")
        storage.write("abc", b"xyz")

        assert (tmp_path / "blobs" / "abc").read_bytes() == b"xyz"


class TestInMemoryFileSpecifics:
    """Tests spécifiques aux implémentations mémoire."""

    def test_repositories_are_isolated(self) -> None:
        """Deux instances ne doivent pas partager leurs données."""
        repo1 = InMemoryFileRepository()
        repo2 = InMemoryFileRepository()
        repo1.add(File.create(id="1", name=FileName("a"), size=FileSize(1)))

        assert repo1.get("1") is not None
        assert repo2.get("1") is None

    def test_blob_storage_starts_empty(self) -> None:
        """Un nouveau blob storage doit être vide."""
        storage = InMemoryBlobStorage()

        assert storage.read("any") is None
