"""Tests des use cases RenameFolder et RenameFile."""

import pytest

from minidrive.adapters.memory.blob_storage import InMemoryBlobStorage
from minidrive.adapters.memory.file_repository import InMemoryFileRepository
from minidrive.adapters.memory.folder_repository import InMemoryFolderRepository
from minidrive.adapters.memory.id_generator import UuidIdGenerator
from minidrive.adapters.memory.share_repository import InMemoryShareRepository
from minidrive.application.quota_policies import UnlimitedQuotaPolicy
from minidrive.application.use_cases.create_folder import CreateFolder
from minidrive.application.use_cases.rename_file import RenameFile
from minidrive.application.use_cases.rename_folder import RenameFolder
from minidrive.application.use_cases.upload_file import UploadFile
from minidrive.domain.errors import (
    FileAlreadyExistsError,
    FolderAlreadyExistsError,
    InTrashError,
    InvalidFileNameError,
    UnknownFileError,
    UnknownFolderError,
)


@pytest.fixture
def folder_setup() -> tuple[RenameFolder, CreateFolder]:
    """RenameFolder câblé sur un repository mémoire vierge."""
    repository = InMemoryFolderRepository()
    return (
        RenameFolder(folder_repository=repository, share_repository=InMemoryShareRepository()),
        CreateFolder(folder_repository=repository, id_generator=UuidIdGenerator()),
    )


@pytest.fixture
def file_setup() -> tuple[RenameFile, UploadFile]:
    """RenameFile câblé sur des adapteurs mémoire vierges."""
    repository = InMemoryFileRepository()
    return (
        RenameFile(file_repository=repository, share_repository=InMemoryShareRepository()),
        UploadFile(
            file_repository=repository,
            blob_storage=InMemoryBlobStorage(),
            id_generator=UuidIdGenerator(),
            quota_policy=UnlimitedQuotaPolicy(),
            folder_repository=InMemoryFolderRepository(),
        ),
    )


class TestRenameFolder:
    """Tests du use case RenameFolder."""

    def test_rename_success(self, folder_setup: tuple[RenameFolder, CreateFolder]) -> None:
        """Renommer un dossier doit changer son nom."""
        rename_folder, create_folder = folder_setup
        folder = create_folder.execute("ancien")

        renamed = rename_folder.execute(folder_id=folder.id, new_name="nouveau")

        assert renamed.name.value == "nouveau"
        assert renamed.id == folder.id

    def test_rename_same_name_is_noop(
        self, folder_setup: tuple[RenameFolder, CreateFolder]
    ) -> None:
        """Renommer avec le même nom doit réussir sans rien changer."""
        rename_folder, create_folder = folder_setup
        folder = create_folder.execute("pareil")

        renamed = rename_folder.execute(folder_id=folder.id, new_name="pareil")

        assert renamed.name.value == "pareil"

    def test_rename_unknown_id(self, folder_setup: tuple[RenameFolder, CreateFolder]) -> None:
        """Renommer un ID inconnu doit lever UnknownFolderError."""
        rename_folder, _ = folder_setup

        with pytest.raises(UnknownFolderError):
            rename_folder.execute(folder_id="inconnu", new_name="x")

    def test_rename_invalid_name(self, folder_setup: tuple[RenameFolder, CreateFolder]) -> None:
        """Un nouveau nom invalide doit lever InvalidFileNameError."""
        rename_folder, create_folder = folder_setup
        folder = create_folder.execute("ok")

        with pytest.raises(InvalidFileNameError):
            rename_folder.execute(folder_id=folder.id, new_name="mau/vais")

    def test_rename_duplicate_name(self, folder_setup: tuple[RenameFolder, CreateFolder]) -> None:
        """Renommer vers un nom déjà pris dans le parent doit échouer."""
        rename_folder, create_folder = folder_setup
        create_folder.execute("pris")
        folder = create_folder.execute("moi")

        with pytest.raises(FolderAlreadyExistsError):
            rename_folder.execute(folder_id=folder.id, new_name="pris")

    def test_rename_trashed_refused(self, folder_setup: tuple[RenameFolder, CreateFolder]) -> None:
        """Renommer un dossier corbeillé doit lever InTrashError."""
        rename_folder, create_folder = folder_setup
        folder = create_folder.execute("vieux")
        folder.trashed = True

        with pytest.raises(InTrashError):
            rename_folder.execute(folder_id=folder.id, new_name="neuf")


class TestRenameFile:
    """Tests du use case RenameFile."""

    def test_rename_success(self, file_setup: tuple[RenameFile, UploadFile]) -> None:
        """Renommer un fichier doit changer son nom, pas son contenu."""
        rename_file, upload_file = file_setup
        file = upload_file.execute(name="a.txt", data=b"123")

        renamed = rename_file.execute(file_id=file.id, new_name="b.txt")

        assert renamed.name.value == "b.txt"
        assert renamed.size.value == 3

    def test_rename_unknown_id(self, file_setup: tuple[RenameFile, UploadFile]) -> None:
        """Renommer un ID inconnu doit lever UnknownFileError."""
        rename_file, _ = file_setup

        with pytest.raises(UnknownFileError):
            rename_file.execute(file_id="inconnu", new_name="x")

    def test_rename_duplicate_name(self, file_setup: tuple[RenameFile, UploadFile]) -> None:
        """Renommer vers un nom déjà pris dans le parent doit échouer."""
        rename_file, upload_file = file_setup
        upload_file.execute(name="pris.txt", data=b"1")
        file = upload_file.execute(name="moi.txt", data=b"2")

        with pytest.raises(FileAlreadyExistsError):
            rename_file.execute(file_id=file.id, new_name="pris.txt")
