"""Tests des use cases PurgeFolder et PurgeFile."""

import pytest

from minidrive.adapters.memory.blob_storage import InMemoryBlobStorage
from minidrive.adapters.memory.file_repository import InMemoryFileRepository
from minidrive.adapters.memory.folder_repository import InMemoryFolderRepository
from minidrive.adapters.memory.id_generator import UuidIdGenerator
from minidrive.adapters.memory.share_repository import InMemoryShareRepository
from minidrive.application.quota_policies import FixedQuotaPolicy
from minidrive.application.use_cases.create_folder import CreateFolder
from minidrive.application.use_cases.purge_file import PurgeFile
from minidrive.application.use_cases.purge_folder import PurgeFolder
from minidrive.application.use_cases.trash_folder import TrashFolder
from minidrive.application.use_cases.upload_file import UploadFile
from minidrive.application.users import DEFAULT_USER_ID
from minidrive.domain.errors import UnknownFileError, UnknownFolderError


@pytest.fixture
def purge_setup() -> tuple[
    PurgeFolder,
    PurgeFile,
    CreateFolder,
    UploadFile,
    InMemoryFolderRepository,
    InMemoryFileRepository,
    InMemoryBlobStorage,
    FixedQuotaPolicy,
]:
    """Purge câblée sur des adapteurs mémoire vierges (quota fixe observable)."""
    folder_repository = InMemoryFolderRepository()
    file_repository = InMemoryFileRepository()
    blob_storage = InMemoryBlobStorage()
    share_repository = InMemoryShareRepository()
    policy = FixedQuotaPolicy(quota_bytes=1000)
    return (
        PurgeFolder(
            folder_repository=folder_repository,
            file_repository=file_repository,
            blob_storage=blob_storage,
            quota_policy=policy,
            share_repository=share_repository,
        ),
        PurgeFile(
            file_repository=file_repository,
            blob_storage=blob_storage,
            quota_policy=policy,
            share_repository=share_repository,
        ),
        CreateFolder(folder_repository=folder_repository, id_generator=UuidIdGenerator()),
        UploadFile(
            file_repository=file_repository,
            blob_storage=blob_storage,
            id_generator=UuidIdGenerator(),
            quota_policy=policy,
        ),
        folder_repository,
        file_repository,
        blob_storage,
        policy,
    )


Setup = tuple[
    PurgeFolder,
    PurgeFile,
    CreateFolder,
    UploadFile,
    InMemoryFolderRepository,
    InMemoryFileRepository,
    InMemoryBlobStorage,
    FixedQuotaPolicy,
]


class TestPurgeFile:
    """Tests de PurgeFile."""

    def test_purge_removes_all_traces(self, purge_setup: Setup) -> None:
        """Purger doit supprimer métadonnées + blob et libérer le quota."""
        _, purge_file, _, upload_file, _, file_repo, blobs, policy = purge_setup
        file = upload_file.execute(name="a.txt", data=b"12345")

        purge_file.execute(file_id=file.id)

        assert file_repo.get(file.id) is None
        assert blobs.read(file.id) is None
        assert policy.get_remaining_quota(DEFAULT_USER_ID) == 1000

    def test_purge_unknown(self, purge_setup: Setup) -> None:
        """Purger un ID inconnu doit lever UnknownFileError."""
        _, purge_file, _, _, _, _, _, _ = purge_setup

        with pytest.raises(UnknownFileError):
            purge_file.execute(file_id="inconnu")


class TestPurgeFolder:
    """Tests de PurgeFolder."""

    def test_purge_recursive(self, purge_setup: Setup) -> None:
        """Purger un dossier doit purger récursivement fichiers et sous-dossiers."""
        purge_folder, _, create_folder, upload_file, folder_repo, file_repo, blobs, _ = purge_setup
        parent = create_folder.execute("parent")
        child = create_folder.execute("enfant", parent_id=parent.id)
        file = upload_file.execute(name="a.txt", data=b"123", parent_id=child.id)

        purge_folder.execute(folder_id=parent.id)

        assert folder_repo.get(parent.id) is None
        assert folder_repo.get(child.id) is None
        assert file_repo.get(file.id) is None
        assert blobs.read(file.id) is None
        assert folder_repo.list_all() == []
        assert file_repo.list_all() == []

    def test_purge_frees_quota(self, purge_setup: Setup) -> None:
        """Le quota des fichiers purgés (même via dossier) doit être libéré."""
        purge_folder, _, create_folder, upload_file, _, _, _, policy = purge_setup
        parent = create_folder.execute("parent")
        upload_file.execute(name="a.txt", data=b"12345", parent_id=parent.id)
        assert policy.get_remaining_quota(DEFAULT_USER_ID) == 995

        purge_folder.execute(folder_id=parent.id)

        assert policy.get_remaining_quota(DEFAULT_USER_ID) == 1000

    def test_purge_unknown(self, purge_setup: Setup) -> None:
        """Purger un ID inconnu doit lever UnknownFolderError."""
        purge_folder, _, _, _, _, _, _, _ = purge_setup

        with pytest.raises(UnknownFolderError):
            purge_folder.execute(folder_id="inconnu")

    def test_purge_trashed_subtree(self, purge_setup: Setup) -> None:
        """Purger un dossier corbeillé doit tout supprimer quand même."""
        purge_folder, _, create_folder, upload_file, folder_repo, _, _, _ = purge_setup
        trash_folder = TrashFolder(folder_repository=folder_repo)
        parent = create_folder.execute("parent")
        create_folder.execute("enfant", parent_id=parent.id)
        trash_folder.execute(folder_id=parent.id)

        purge_folder.execute(folder_id=parent.id)

        assert folder_repo.list_all(include_trashed=True) == []
