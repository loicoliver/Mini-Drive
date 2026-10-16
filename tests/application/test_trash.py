"""Tests des use cases TrashFolder/RestoreFolder et TrashFile/RestoreFile."""

import pytest

from minidrive.adapters.memory.blob_storage import InMemoryBlobStorage
from minidrive.adapters.memory.file_repository import InMemoryFileRepository
from minidrive.adapters.memory.folder_repository import InMemoryFolderRepository
from minidrive.adapters.memory.id_generator import UuidIdGenerator
from minidrive.adapters.memory.share_repository import InMemoryShareRepository
from minidrive.application.quota_policies import UnlimitedQuotaPolicy
from minidrive.application.use_cases.create_folder import CreateFolder
from minidrive.application.use_cases.trash_file import RestoreFile, TrashFile
from minidrive.application.use_cases.trash_folder import RestoreFolder, TrashFolder
from minidrive.application.use_cases.upload_file import UploadFile
from minidrive.domain.errors import UnknownFileError, UnknownFolderError


@pytest.fixture
def folder_setup() -> tuple[TrashFolder, RestoreFolder, CreateFolder, InMemoryFolderRepository]:
    """Corbeille dossiers câblée sur un repository mémoire vierge."""
    repository = InMemoryFolderRepository()
    return (
        TrashFolder(folder_repository=repository, share_repository=InMemoryShareRepository()),
        RestoreFolder(folder_repository=repository, share_repository=InMemoryShareRepository()),
        CreateFolder(folder_repository=repository, id_generator=UuidIdGenerator()),
        repository,
    )


@pytest.fixture
def file_setup() -> tuple[TrashFile, RestoreFile, UploadFile, InMemoryFileRepository]:
    """Corbeille fichiers câblée sur des adapteurs mémoire vierges."""
    repository = InMemoryFileRepository()
    return (
        TrashFile(file_repository=repository, share_repository=InMemoryShareRepository()),
        RestoreFile(file_repository=repository, share_repository=InMemoryShareRepository()),
        UploadFile(
            file_repository=repository,
            blob_storage=InMemoryBlobStorage(),
            id_generator=UuidIdGenerator(),
            quota_policy=UnlimitedQuotaPolicy(),
            folder_repository=InMemoryFolderRepository(),
        ),
        repository,
    )


class TestTrashFolder:
    """Tests de TrashFolder."""

    def test_trash_hides_folder(
        self,
        folder_setup: tuple[TrashFolder, RestoreFolder, CreateFolder, InMemoryFolderRepository],
    ) -> None:
        """Un dossier corbeillé disparaît de list_all mais reste récupérable."""
        trash_folder, _, create_folder, repository = folder_setup
        folder = create_folder.execute("vieux")

        trashed = trash_folder.execute(folder_id=folder.id)

        assert trashed.trashed is True
        assert repository.list_all() == []
        assert repository.get(folder.id) is not None

    def test_trash_cascades_to_descendants(
        self,
        folder_setup: tuple[TrashFolder, RestoreFolder, CreateFolder, InMemoryFolderRepository],
    ) -> None:
        """Corbeiller un parent doit corbeiller toute sa descendance."""
        trash_folder, _, create_folder, repository = folder_setup
        parent = create_folder.execute("parent")
        child = create_folder.execute("enfant", parent_id=parent.id)
        create_folder.execute("petit", parent_id=child.id)

        trash_folder.execute(folder_id=parent.id)

        assert repository.list_all() == []
        retrieved = repository.get(parent.id)
        assert retrieved is not None
        assert retrieved.trashed is True

    def test_trash_frees_name(
        self,
        folder_setup: tuple[TrashFolder, RestoreFolder, CreateFolder, InMemoryFolderRepository],
    ) -> None:
        """Un nom corbeillé redevient disponible (la corbeille ne bloque pas)."""
        trash_folder, _, create_folder, repository = folder_setup
        folder = create_folder.execute("nom")

        trash_folder.execute(folder_id=folder.id)

        assert repository.exists_with_name("nom", None) is False
        recreated = create_folder.execute("nom")
        assert recreated.id != folder.id

    def test_trash_idempotent_and_unknown(
        self,
        folder_setup: tuple[TrashFolder, RestoreFolder, CreateFolder, InMemoryFolderRepository],
    ) -> None:
        """Re-corbeiller est sans effet ; un ID inconnu lève UnknownFolderError."""
        trash_folder, _, create_folder, _ = folder_setup
        folder = create_folder.execute("x")
        trash_folder.execute(folder_id=folder.id)

        again = trash_folder.execute(folder_id=folder.id)

        assert again.trashed is True
        with pytest.raises(UnknownFolderError):
            trash_folder.execute(folder_id="inconnu")


class TestRestoreFolder:
    """Tests de RestoreFolder."""

    def test_restore_brings_back_subtree(
        self,
        folder_setup: tuple[TrashFolder, RestoreFolder, CreateFolder, InMemoryFolderRepository],
    ) -> None:
        """Restaurer un parent doit restaurer toute sa descendance."""
        trash_folder, restore_folder, create_folder, repository = folder_setup
        parent = create_folder.execute("parent")
        create_folder.execute("enfant", parent_id=parent.id)
        trash_folder.execute(folder_id=parent.id)

        restored = restore_folder.execute(folder_id=parent.id)

        assert restored.trashed is False
        assert len(repository.list_all()) == 2

    def test_restore_unknown(
        self,
        folder_setup: tuple[TrashFolder, RestoreFolder, CreateFolder, InMemoryFolderRepository],
    ) -> None:
        """Restaurer un ID inconnu doit lever UnknownFolderError."""
        _, restore_folder, _, _ = folder_setup

        with pytest.raises(UnknownFolderError):
            restore_folder.execute(folder_id="inconnu")


class TestTrashRestoreFile:
    """Tests de TrashFile et RestoreFile."""

    def test_trash_and_restore(
        self, file_setup: tuple[TrashFile, RestoreFile, UploadFile, InMemoryFileRepository]
    ) -> None:
        """Corbeiller cache le fichier ; restaurer le fait réapparaître."""
        trash_file, restore_file, upload_file, repository = file_setup
        file = upload_file.execute(name="a.txt", data=b"1")

        assert trash_file.execute(file_id=file.id).trashed is True
        assert repository.list_all() == []

        assert restore_file.execute(file_id=file.id).trashed is False
        assert len(repository.list_all()) == 1

    def test_trash_unknown(
        self, file_setup: tuple[TrashFile, RestoreFile, UploadFile, InMemoryFileRepository]
    ) -> None:
        """Un ID inconnu doit lever UnknownFileError (trash comme restore)."""
        trash_file, restore_file, _, _ = file_setup

        with pytest.raises(UnknownFileError):
            trash_file.execute(file_id="inconnu")
        with pytest.raises(UnknownFileError):
            restore_file.execute(file_id="inconnu")
