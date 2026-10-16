"""Tests des use cases MoveFolder et MoveFile."""

import pytest

from minidrive.adapters.memory.blob_storage import InMemoryBlobStorage
from minidrive.adapters.memory.file_repository import InMemoryFileRepository
from minidrive.adapters.memory.folder_repository import InMemoryFolderRepository
from minidrive.adapters.memory.id_generator import UuidIdGenerator
from minidrive.adapters.memory.share_repository import InMemoryShareRepository
from minidrive.application.quota_policies import UnlimitedQuotaPolicy
from minidrive.application.use_cases.create_folder import CreateFolder
from minidrive.application.use_cases.move_file import MoveFile
from minidrive.application.use_cases.move_folder import MoveFolder
from minidrive.application.use_cases.upload_file import UploadFile
from minidrive.domain.errors import (
    FileAlreadyExistsError,
    FolderAlreadyExistsError,
    InTrashError,
    InvalidMoveError,
    UnknownFileError,
    UnknownFolderError,
)


@pytest.fixture
def folder_setup() -> tuple[MoveFolder, CreateFolder, InMemoryFolderRepository]:
    """MoveFolder câblé sur un repository mémoire vierge."""
    repository = InMemoryFolderRepository()
    return (
        MoveFolder(folder_repository=repository, share_repository=InMemoryShareRepository()),
        CreateFolder(folder_repository=repository, id_generator=UuidIdGenerator()),
        repository,
    )


@pytest.fixture
def file_setup() -> tuple[MoveFile, UploadFile, CreateFolder]:
    """MoveFile câblé sur des adapteurs mémoire vierges."""
    folder_repository = InMemoryFolderRepository()
    file_repository = InMemoryFileRepository()
    return (
        MoveFile(
            file_repository=file_repository,
            folder_repository=folder_repository,
            share_repository=InMemoryShareRepository(),
        ),
        UploadFile(
            file_repository=file_repository,
            blob_storage=InMemoryBlobStorage(),
            id_generator=UuidIdGenerator(),
            quota_policy=UnlimitedQuotaPolicy(),
            folder_repository=folder_repository,
        ),
        CreateFolder(folder_repository=folder_repository, id_generator=UuidIdGenerator()),
    )


class TestMoveFolder:
    """Tests du use case MoveFolder."""

    def test_move_to_folder(
        self, folder_setup: tuple[MoveFolder, CreateFolder, InMemoryFolderRepository]
    ) -> None:
        """Déplacer un dossier vers un parent doit changer son parent."""
        move_folder, create_folder, _ = folder_setup
        parent = create_folder.execute("parent")
        child = create_folder.execute("enfant")

        moved = move_folder.execute(folder_id=child.id, new_parent_id=parent.id)

        assert moved.parent_id == parent.id

    def test_move_to_root(
        self, folder_setup: tuple[MoveFolder, CreateFolder, InMemoryFolderRepository]
    ) -> None:
        """Déplacer vers None doit remonter à la racine."""
        move_folder, create_folder, _ = folder_setup
        parent = create_folder.execute("parent")
        child = create_folder.execute("enfant", parent_id=parent.id)

        moved = move_folder.execute(folder_id=child.id, new_parent_id=None)

        assert moved.parent_id is None

    def test_move_same_parent_is_noop(
        self, folder_setup: tuple[MoveFolder, CreateFolder, InMemoryFolderRepository]
    ) -> None:
        """Déplacer vers le parent actuel doit réussir sans rien changer."""
        move_folder, create_folder, _ = folder_setup
        folder = create_folder.execute("stable")

        moved = move_folder.execute(folder_id=folder.id, new_parent_id=None)

        assert moved.parent_id is None

    def test_move_unknown_id(
        self, folder_setup: tuple[MoveFolder, CreateFolder, InMemoryFolderRepository]
    ) -> None:
        """Déplacer un ID inconnu doit lever UnknownFolderError."""
        move_folder, _, _ = folder_setup

        with pytest.raises(UnknownFolderError):
            move_folder.execute(folder_id="inconnu", new_parent_id=None)

    def test_move_unknown_parent(
        self, folder_setup: tuple[MoveFolder, CreateFolder, InMemoryFolderRepository]
    ) -> None:
        """Déplacer vers un parent inconnu doit lever UnknownFolderError."""
        move_folder, create_folder, _ = folder_setup
        folder = create_folder.execute("orphelin")

        with pytest.raises(UnknownFolderError):
            move_folder.execute(folder_id=folder.id, new_parent_id="parent-fantome")

    def test_move_onto_self(
        self, folder_setup: tuple[MoveFolder, CreateFolder, InMemoryFolderRepository]
    ) -> None:
        """Un dossier ne peut pas être son propre parent."""
        move_folder, create_folder, _ = folder_setup
        folder = create_folder.execute("narcisse")

        with pytest.raises(InvalidMoveError):
            move_folder.execute(folder_id=folder.id, new_parent_id=folder.id)

    def test_move_into_descendant(
        self, folder_setup: tuple[MoveFolder, CreateFolder, InMemoryFolderRepository]
    ) -> None:
        """Un dossier ne peut pas aller dans un de ses descendants (cycle)."""
        move_folder, create_folder, _ = folder_setup
        grand_parent = create_folder.execute("gp")
        parent = create_folder.execute("p", parent_id=grand_parent.id)
        enfant = create_folder.execute("e", parent_id=parent.id)

        with pytest.raises(InvalidMoveError):
            move_folder.execute(folder_id=grand_parent.id, new_parent_id=enfant.id)

    def test_move_duplicate_name(
        self, folder_setup: tuple[MoveFolder, CreateFolder, InMemoryFolderRepository]
    ) -> None:
        """Déplacer vers un parent contenant un homonyme doit échouer."""
        move_folder, create_folder, _ = folder_setup
        parent = create_folder.execute("parent")
        create_folder.execute("doublon", parent_id=parent.id)
        folder = create_folder.execute("doublon")

        with pytest.raises(FolderAlreadyExistsError):
            move_folder.execute(folder_id=folder.id, new_parent_id=parent.id)

    def test_move_trashed_refused(
        self, folder_setup: tuple[MoveFolder, CreateFolder, InMemoryFolderRepository]
    ) -> None:
        """Déplacer un dossier corbeillé doit lever InTrashError."""
        move_folder, create_folder, _ = folder_setup
        folder = create_folder.execute("vieux")
        folder.trashed = True

        with pytest.raises(InTrashError):
            move_folder.execute(folder_id=folder.id, new_parent_id=None)

    def test_move_into_trashed_parent_refused(
        self, folder_setup: tuple[MoveFolder, CreateFolder, InMemoryFolderRepository]
    ) -> None:
        """Déplacer vers un parent corbeillé doit lever InvalidMoveError."""
        move_folder, create_folder, _ = folder_setup
        parent = create_folder.execute("parent")
        parent.trashed = True
        folder = create_folder.execute("enfant")

        with pytest.raises(InvalidMoveError):
            move_folder.execute(folder_id=folder.id, new_parent_id=parent.id)


class TestMoveFile:
    """Tests du use case MoveFile."""

    def test_move_to_folder(self, file_setup: tuple[MoveFile, UploadFile, CreateFolder]) -> None:
        """Déplacer un fichier vers un dossier doit changer son parent."""
        move_file, upload_file, create_folder = file_setup
        parent = create_folder.execute("docs")
        file = upload_file.execute(name="a.txt", data=b"1")

        moved = move_file.execute(file_id=file.id, new_parent_id=parent.id)

        assert moved.parent_id == parent.id

    def test_move_unknown_file(self, file_setup: tuple[MoveFile, UploadFile, CreateFolder]) -> None:
        """Déplacer un ID inconnu doit lever UnknownFileError."""
        move_file, _, _ = file_setup

        with pytest.raises(UnknownFileError):
            move_file.execute(file_id="inconnu", new_parent_id=None)

    def test_move_unknown_parent(
        self, file_setup: tuple[MoveFile, UploadFile, CreateFolder]
    ) -> None:
        """Déplacer vers un dossier inconnu doit lever UnknownFolderError."""
        move_file, upload_file, _ = file_setup
        file = upload_file.execute(name="a.txt", data=b"1")

        with pytest.raises(UnknownFolderError):
            move_file.execute(file_id=file.id, new_parent_id="parent-fantome")

    def test_move_duplicate_name(
        self, file_setup: tuple[MoveFile, UploadFile, CreateFolder]
    ) -> None:
        """Déplacer vers un parent contenant un homonyme doit échouer."""
        move_file, upload_file, create_folder = file_setup
        parent = create_folder.execute("docs")
        upload_file.execute(name="a.txt", data=b"1", parent_id=parent.id)
        file = upload_file.execute(name="a.txt", data=b"2")

        with pytest.raises(FileAlreadyExistsError):
            move_file.execute(file_id=file.id, new_parent_id=parent.id)
