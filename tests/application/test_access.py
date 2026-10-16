"""Tests du contrôle d'accès (helpers purs + enforcement dans les use cases)."""

import pytest

from minidrive.adapters.memory.blob_storage import InMemoryBlobStorage
from minidrive.adapters.memory.file_repository import InMemoryFileRepository
from minidrive.adapters.memory.folder_repository import InMemoryFolderRepository
from minidrive.adapters.memory.id_generator import UuidIdGenerator
from minidrive.adapters.memory.share_repository import InMemoryShareRepository
from minidrive.application.access import require_read, require_write
from minidrive.application.quota_policies import UnlimitedQuotaPolicy
from minidrive.application.use_cases.create_folder import CreateFolder
from minidrive.application.use_cases.download_file import DownloadFile
from minidrive.application.use_cases.list_files import ListFiles
from minidrive.application.use_cases.list_folders import ListFolders
from minidrive.application.use_cases.rename_file import RenameFile
from minidrive.application.use_cases.rename_folder import RenameFolder
from minidrive.application.use_cases.share_file import ShareFile
from minidrive.application.use_cases.share_folder import ShareFolder
from minidrive.application.use_cases.trash_folder import TrashFolder
from minidrive.application.use_cases.upload_file import UploadFile
from minidrive.domain.errors import PermissionDeniedError


class TestAccessHelpers:
    """Tests purs de require_read / require_write."""

    def test_owner_can_all(self) -> None:
        """Le propriétaire passe toujours."""
        require_read("alice", None, "alice", "n1")
        require_write("alice", None, "alice", "n1")

    def test_editor_can_read_and_write(self) -> None:
        """Un editor passe les deux contrôles."""
        require_read("alice", "editor", "bob", "n1")
        require_write("alice", "editor", "bob", "n1")

    def test_reader_can_read_only(self) -> None:
        """Un reader passe la lecture mais pas l'écriture."""
        require_read("alice", "reader", "bob", "n1")

        with pytest.raises(PermissionDeniedError) as exc_info:
            require_write("alice", "reader", "bob", "n1")

        assert "bob" in str(exc_info.value)
        assert "n1" in str(exc_info.value)

    def test_stranger_denied(self) -> None:
        """Sans partage, lecture et écriture sont refusées."""
        with pytest.raises(PermissionDeniedError):
            require_read("alice", None, "mallory", "n1")
        with pytest.raises(PermissionDeniedError):
            require_write("alice", None, "mallory", "n1")


class TestEnforcement:
    """L'enforcement dans les use cases (partage réel via ShareFolder)."""

    @pytest.fixture
    def world(self) -> dict[str, object]:
        """Monde mémoire : dossier d'alice partagé reader à bob, editor à carol."""
        folder_repository = InMemoryFolderRepository()
        file_repository = InMemoryFileRepository()
        share_repository = InMemoryShareRepository()
        blob_storage = InMemoryBlobStorage()
        create_folder = CreateFolder(
            folder_repository=folder_repository, id_generator=UuidIdGenerator()
        )
        folder = create_folder.execute("docs", owner_id="alice")
        upload_file = UploadFile(
            file_repository=file_repository,
            blob_storage=blob_storage,
            id_generator=UuidIdGenerator(),
            quota_policy=UnlimitedQuotaPolicy(),
            folder_repository=folder_repository,
        )
        file = upload_file.execute(name="a.txt", data=b"1", user_id="alice")
        share_folder = ShareFolder(
            folder_repository=folder_repository, share_repository=share_repository
        )
        share_folder.execute(folder_id=folder.id, user_id="bob", role="reader", owner_id="alice")
        share_folder.execute(folder_id=folder.id, user_id="carol", role="editor", owner_id="alice")
        share_file = ShareFile(file_repository=file_repository, share_repository=share_repository)
        share_file.execute(file_id=file.id, user_id="bob", role="reader", owner_id="alice")
        return {
            "folders": folder_repository,
            "files": file_repository,
            "shares": share_repository,
            "blobs": blob_storage,
            "folder_id": folder.id,
            "file_id": file.id,
        }

    def test_reader_can_download_but_not_rename(self, world: dict[str, object]) -> None:
        """Reader : download OK, rename refusé."""
        files = world["files"]
        assert isinstance(files, InMemoryFileRepository)
        blobs = world["blobs"]
        assert isinstance(blobs, InMemoryBlobStorage)
        shares = world["shares"]
        assert isinstance(shares, InMemoryShareRepository)
        file_id = world["file_id"]
        assert isinstance(file_id, str)

        download_file = DownloadFile(
            file_repository=files, blob_storage=blobs, share_repository=shares
        )
        _, data = download_file.execute(file_id=file_id, user_id="bob")
        assert data == b"1"

        rename_file = RenameFile(file_repository=files, share_repository=shares)
        with pytest.raises(PermissionDeniedError):
            rename_file.execute(file_id=file_id, new_name="b.txt", user_id="bob")

    def test_editor_can_write(self, world: dict[str, object]) -> None:
        """Editor : rename et trash autorisés."""
        folders = world["folders"]
        assert isinstance(folders, InMemoryFolderRepository)
        shares = world["shares"]
        assert isinstance(shares, InMemoryShareRepository)
        folder_id = world["folder_id"]
        assert isinstance(folder_id, str)

        rename_folder = RenameFolder(folder_repository=folders, share_repository=shares)
        renamed = rename_folder.execute(folder_id=folder_id, new_name="docs2", user_id="carol")
        assert renamed.name.value == "docs2"

        trash_folder = TrashFolder(folder_repository=folders, share_repository=shares)
        assert trash_folder.execute(folder_id=folder_id, user_id="carol").trashed is True

    def test_stranger_sees_nothing(self, world: dict[str, object]) -> None:
        """Sans partage : ls vide et download refusé."""
        folders = world["folders"]
        assert isinstance(folders, InMemoryFolderRepository)
        files = world["files"]
        assert isinstance(files, InMemoryFileRepository)
        shares = world["shares"]
        assert isinstance(shares, InMemoryShareRepository)
        blobs = world["blobs"]
        assert isinstance(blobs, InMemoryBlobStorage)
        file_id = world["file_id"]
        assert isinstance(file_id, str)

        list_folders = ListFolders(folder_repository=folders, share_repository=shares)
        list_files = ListFiles(file_repository=files, share_repository=shares)
        assert list_folders.execute(user_id="mallory") == []
        assert list_files.execute(user_id="mallory") == []

        download_file = DownloadFile(
            file_repository=files, blob_storage=blobs, share_repository=shares
        )
        with pytest.raises(PermissionDeniedError):
            download_file.execute(file_id=file_id, user_id="mallory")

    def test_shared_visible_in_lists(self, world: dict[str, object]) -> None:
        """Les partagés apparaissent dans le ls du bénéficiaire."""
        folders = world["folders"]
        assert isinstance(folders, InMemoryFolderRepository)
        shares = world["shares"]
        assert isinstance(shares, InMemoryShareRepository)

        list_folders = ListFolders(folder_repository=folders, share_repository=shares)
        assert [f.name.value for f in list_folders.execute(user_id="bob")] == ["docs"]
