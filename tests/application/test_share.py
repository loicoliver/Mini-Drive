"""Tests des use cases Share/Unshare (dossiers et fichiers)."""

import pytest

from minidrive.adapters.memory.blob_storage import InMemoryBlobStorage
from minidrive.adapters.memory.file_repository import InMemoryFileRepository
from minidrive.adapters.memory.folder_repository import InMemoryFolderRepository
from minidrive.adapters.memory.id_generator import UuidIdGenerator
from minidrive.adapters.memory.share_repository import InMemoryShareRepository
from minidrive.application.quota_policies import UnlimitedQuotaPolicy
from minidrive.application.use_cases.create_folder import CreateFolder
from minidrive.application.use_cases.share_file import ShareFile, UnshareFile
from minidrive.application.use_cases.share_folder import ShareFolder, UnshareFolder
from minidrive.application.use_cases.upload_file import UploadFile
from minidrive.domain.errors import (
    InvalidShareError,
    UnknownFileError,
    UnknownFolderError,
)


@pytest.fixture
def folder_sharing() -> tuple[ShareFolder, UnshareFolder, CreateFolder, InMemoryShareRepository]:
    """Partage dossiers câblé sur des adapteurs mémoire vierges."""
    folder_repository = InMemoryFolderRepository()
    share_repository = InMemoryShareRepository()
    return (
        ShareFolder(folder_repository=folder_repository, share_repository=share_repository),
        UnshareFolder(folder_repository=folder_repository, share_repository=share_repository),
        CreateFolder(folder_repository=folder_repository, id_generator=UuidIdGenerator()),
        share_repository,
    )


@pytest.fixture
def file_sharing() -> tuple[ShareFile, UnshareFile, UploadFile, InMemoryShareRepository]:
    """Partage fichiers câblé sur des adapteurs mémoire vierges."""
    file_repository = InMemoryFileRepository()
    share_repository = InMemoryShareRepository()
    return (
        ShareFile(file_repository=file_repository, share_repository=share_repository),
        UnshareFile(file_repository=file_repository, share_repository=share_repository),
        UploadFile(
            file_repository=file_repository,
            blob_storage=InMemoryBlobStorage(),
            id_generator=UuidIdGenerator(),
            quota_policy=UnlimitedQuotaPolicy(),
            folder_repository=InMemoryFolderRepository(),
        ),
        share_repository,
    )


class TestShareFolder:
    """Tests de ShareFolder."""

    def test_share_grants_role(
        self,
        folder_sharing: tuple[ShareFolder, UnshareFolder, CreateFolder, InMemoryShareRepository],
    ) -> None:
        """Partager doit accorder le rôle demandé."""
        share_folder, _, create_folder, shares = folder_sharing
        folder = create_folder.execute("docs", owner_id="alice")

        share = share_folder.execute(
            folder_id=folder.id, user_id="bob", role="reader", owner_id="alice"
        )

        assert share.role == "reader"
        assert shares.role_for("folder", folder.id, "bob") == "reader"

    def test_share_unknown_folder(
        self,
        folder_sharing: tuple[ShareFolder, UnshareFolder, CreateFolder, InMemoryShareRepository],
    ) -> None:
        """Partager un ID inconnu doit lever UnknownFolderError."""
        share_folder, _, _, _ = folder_sharing

        with pytest.raises(UnknownFolderError):
            share_folder.execute(folder_id="inconnu", user_id="bob", role="reader")

    def test_share_invalid_role(
        self,
        folder_sharing: tuple[ShareFolder, UnshareFolder, CreateFolder, InMemoryShareRepository],
    ) -> None:
        """Un rôle inconnu doit lever InvalidShareError."""
        share_folder, _, create_folder, _ = folder_sharing
        folder = create_folder.execute("docs", owner_id="alice")

        with pytest.raises(InvalidShareError):
            share_folder.execute(folder_id=folder.id, user_id="bob", role="admin", owner_id="alice")

    def test_share_non_owner_refused(
        self,
        folder_sharing: tuple[ShareFolder, UnshareFolder, CreateFolder, InMemoryShareRepository],
    ) -> None:
        """Seul le propriétaire peut partager."""
        share_folder, _, create_folder, shares = folder_sharing
        folder = create_folder.execute("docs", owner_id="alice")

        with pytest.raises(InvalidShareError):
            share_folder.execute(
                folder_id=folder.id, user_id="bob", role="reader", owner_id="mallory"
            )

        assert shares.role_for("folder", folder.id, "bob") is None


class TestUnshareFolder:
    """Tests de UnshareFolder."""

    def test_unshare_revokes(
        self,
        folder_sharing: tuple[ShareFolder, UnshareFolder, CreateFolder, InMemoryShareRepository],
    ) -> None:
        """Retirer un partage doit le révoquer (idempotent)."""
        share_folder, unshare_folder, create_folder, shares = folder_sharing
        folder = create_folder.execute("docs", owner_id="alice")
        share_folder.execute(folder_id=folder.id, user_id="bob", role="reader", owner_id="alice")

        unshare_folder.execute(folder_id=folder.id, user_id="bob", owner_id="alice")
        unshare_folder.execute(folder_id=folder.id, user_id="bob", owner_id="alice")

        assert shares.role_for("folder", folder.id, "bob") is None

    def test_unshare_non_owner_refused(
        self,
        folder_sharing: tuple[ShareFolder, UnshareFolder, CreateFolder, InMemoryShareRepository],
    ) -> None:
        """Seul le propriétaire peut retirer un partage."""
        share_folder, unshare_folder, create_folder, shares = folder_sharing
        folder = create_folder.execute("docs", owner_id="alice")
        share_folder.execute(folder_id=folder.id, user_id="bob", role="reader", owner_id="alice")

        with pytest.raises(InvalidShareError):
            unshare_folder.execute(folder_id=folder.id, user_id="bob", owner_id="mallory")

        assert shares.role_for("folder", folder.id, "bob") == "reader"


class TestShareFile:
    """Tests de ShareFile et UnshareFile."""

    def test_share_and_unshare(
        self, file_sharing: tuple[ShareFile, UnshareFile, UploadFile, InMemoryShareRepository]
    ) -> None:
        """Partager puis retirer un fichier."""
        share_file, unshare_file, upload_file, shares = file_sharing
        file = upload_file.execute(name="a.txt", data=b"1", user_id="alice")

        assert file.owner_id == "alice"
        share = share_file.execute(file_id=file.id, user_id="bob", role="editor", owner_id="alice")
        assert share.role == "editor"

        unshare_file.execute(file_id=file.id, user_id="bob", owner_id="alice")
        assert shares.role_for("file", file.id, "bob") is None

    def test_share_unknown_file(
        self, file_sharing: tuple[ShareFile, UnshareFile, UploadFile, InMemoryShareRepository]
    ) -> None:
        """Partager un ID inconnu doit lever UnknownFileError."""
        share_file, _, _, _ = file_sharing

        with pytest.raises(UnknownFileError):
            share_file.execute(file_id="inconnu", user_id="bob", role="reader")
