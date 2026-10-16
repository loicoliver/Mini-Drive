"""Tests du use case DownloadFile."""

import pytest

from minidrive.adapters.memory.blob_storage import InMemoryBlobStorage
from minidrive.adapters.memory.file_repository import InMemoryFileRepository
from minidrive.adapters.memory.folder_repository import InMemoryFolderRepository
from minidrive.adapters.memory.id_generator import UuidIdGenerator
from minidrive.adapters.memory.share_repository import InMemoryShareRepository
from minidrive.application.quota_policies import UnlimitedQuotaPolicy
from minidrive.application.use_cases.download_file import DownloadFile
from minidrive.application.use_cases.upload_file import UploadFile
from minidrive.domain.errors import InTrashError, UnknownFileError


def make_download_file() -> tuple[DownloadFile, UploadFile]:
    """Fabrique un DownloadFile câblé sur des adapteurs mémoire vierges."""
    repository = InMemoryFileRepository()
    blob_storage = InMemoryBlobStorage()
    return (
        DownloadFile(
            file_repository=repository,
            blob_storage=blob_storage,
            share_repository=InMemoryShareRepository(),
        ),
        UploadFile(
            file_repository=repository,
            blob_storage=blob_storage,
            id_generator=UuidIdGenerator(),
            quota_policy=UnlimitedQuotaPolicy(),
            folder_repository=InMemoryFolderRepository(),
        ),
    )


class TestDownloadFile:
    """Tests du use case DownloadFile avec adapteurs mémoire."""

    def test_download_roundtrip(self) -> None:
        """Télécharger un fichier uploadé doit restituer métadonnées + contenu."""
        download_file, upload_file = make_download_file()
        uploaded = upload_file.execute(name="rapport.pdf", data=b"contenu")

        file, data = download_file.execute(file_id=uploaded.id)

        assert file.id == uploaded.id
        assert file.name.value == "rapport.pdf"
        assert data == b"contenu"

    def test_download_unknown_id(self) -> None:
        """Télécharger un ID inconnu doit lever UnknownFileError."""
        download_file, _ = make_download_file()

        with pytest.raises(UnknownFileError) as exc_info:
            download_file.execute(file_id="inexistant")

        assert "inexistant" in str(exc_info.value)

    def test_download_trashed_refused(self) -> None:
        """Télécharger un fichier corbeillé doit lever InTrashError."""
        download_file, upload_file = make_download_file()
        uploaded = upload_file.execute(name="vieux.txt", data=b"x")
        uploaded.trashed = True

        with pytest.raises(InTrashError):
            download_file.execute(file_id=uploaded.id)

    def test_download_missing_blob(self) -> None:
        """Métadonnées sans contenu doivent lever UnknownFileError (incohérence)."""
        repository = InMemoryFileRepository()
        download_file = DownloadFile(
            file_repository=repository,
            blob_storage=InMemoryBlobStorage(),
            share_repository=InMemoryShareRepository(),
        )
        upload_file = UploadFile(
            file_repository=repository,
            blob_storage=InMemoryBlobStorage(),  # autre stockage : blob absent
            id_generator=UuidIdGenerator(),
            quota_policy=UnlimitedQuotaPolicy(),
            folder_repository=InMemoryFolderRepository(),
        )
        uploaded = upload_file.execute(name="orphelin.txt", data=b"x")

        with pytest.raises(UnknownFileError):
            download_file.execute(file_id=uploaded.id)
