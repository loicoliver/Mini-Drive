"""Contract tests pour BlobStorage : vérifie le principe de Liskov.

Toute implémentation de BlobStorage doit passer ces tests.
"""

from abc import ABC, abstractmethod
from pathlib import Path

import pytest

from minidrive.application.ports import BlobStorage


class BlobStorageContract(ABC):
    """Classe de base abstraite pour tester toute implémentation de BlobStorage."""

    @pytest.fixture
    @abstractmethod
    def storage(self) -> BlobStorage:
        """Fixture abstraite : doit retourner une implémentation de BlobStorage."""
        pass

    def test_write_and_read_roundtrip(self, storage: BlobStorage) -> None:
        """Écrire puis lire doit restituer les octets à l'identique."""
        data = b"\x00\x01\x02 binary \xff contenu"

        storage.write("file-1", data)

        assert storage.read("file-1") == data

    def test_read_missing_returns_none(self, storage: BlobStorage) -> None:
        """Lire un blob absent doit retourner None."""
        assert storage.read("inexistant") is None

    def test_write_empty_bytes(self, storage: BlobStorage) -> None:
        """Un contenu vide doit être stocké et relu (fichier vide valide)."""
        storage.write("empty", b"")

        assert storage.read("empty") == b""

    def test_write_overwrites(self, storage: BlobStorage) -> None:
        """Réécrire le même ID doit remplacer le contenu."""
        storage.write("file-1", b"ancien")
        storage.write("file-1", b"nouveau")

        assert storage.read("file-1") == b"nouveau"

    def test_blobs_are_isolated_by_id(self, storage: BlobStorage) -> None:
        """Deux IDs différents ne doivent pas se mélanger."""
        storage.write("a", b"contenu-a")
        storage.write("b", b"contenu-b")

        assert storage.read("a") == b"contenu-a"
        assert storage.read("b") == b"contenu-b"


class TestInMemoryBlobStorage(BlobStorageContract):
    """Tests concrets pour InMemoryBlobStorage."""

    @pytest.fixture
    def storage(self) -> BlobStorage:
        """Retourne une instance d'InMemoryBlobStorage."""
        from minidrive.adapters.memory.blob_storage import InMemoryBlobStorage

        return InMemoryBlobStorage()


class TestFilesystemBlobStorage(BlobStorageContract):
    """Tests concrets pour FilesystemBlobStorage."""

    @pytest.fixture
    def storage(self, tmp_path: Path) -> BlobStorage:
        """Retourne une instance de FilesystemBlobStorage sur un dossier isolé."""
        from minidrive.adapters.filesystem.blob_storage import FilesystemBlobStorage

        return FilesystemBlobStorage(tmp_path / "blobs")
