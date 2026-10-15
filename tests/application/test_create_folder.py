"""Tests du use case CreateFolder."""

import pytest

from minidrive.adapters.memory.folder_repository import InMemoryFolderRepository
from minidrive.adapters.memory.id_generator import UuidIdGenerator
from minidrive.application.use_cases.create_folder import CreateFolder
from minidrive.domain.errors import FolderAlreadyExistsError, InvalidFileNameError


class TestCreateFolder:
    """Tests du use case CreateFolder avec adapteurs mémoire."""

    @pytest.fixture
    def use_case(self) -> CreateFolder:
        """Fixture pour créer un use case avec adapteurs mémoire."""
        repository = InMemoryFolderRepository()
        id_generator = UuidIdGenerator()
        return CreateFolder(folder_repository=repository, id_generator=id_generator)

    def test_create_folder_success(self, use_case: CreateFolder) -> None:
        """Créer un dossier doit réussir avec un nom valide."""
        folder = use_case.execute(name="documents")

        assert folder.name.value == "documents"
        assert folder.parent_id is None
        assert folder.id is not None
        assert len(folder.id) > 0

    def test_create_folder_with_parent(self, use_case: CreateFolder) -> None:
        """Créer un dossier avec un parent doit fonctionner."""
        folder = use_case.execute(name="sous-dossier", parent_id="parent-123")

        assert folder.name.value == "sous-dossier"
        assert folder.parent_id == "parent-123"

    def test_create_folder_invalid_name(self, use_case: CreateFolder) -> None:
        """Créer un dossier avec un nom invalide doit lever InvalidFileNameError."""
        with pytest.raises(InvalidFileNameError):
            use_case.execute(name="")

        with pytest.raises(InvalidFileNameError):
            use_case.execute(name="dossier/invalide")

    def test_create_folder_duplicate_name(self, use_case: CreateFolder) -> None:
        """Créer deux dossiers avec le même nom doit lever FolderAlreadyExistsError."""
        use_case.execute(name="documents")

        with pytest.raises(FolderAlreadyExistsError) as exc_info:
            use_case.execute(name="documents")

        assert "documents" in str(exc_info.value)

    def test_same_name_different_parent_allowed(self, use_case: CreateFolder) -> None:
        """Deux dossiers peuvent avoir le même nom s'ils ont des parents différents."""
        folder1 = use_case.execute(name="images", parent_id=None)
        folder2 = use_case.execute(name="images", parent_id="parent-123")

        assert folder1.name.value == "images"
        assert folder2.name.value == "images"
        assert folder1.id != folder2.id

    def test_generated_ids_are_unique(self, use_case: CreateFolder) -> None:
        """Chaque dossier doit avoir un ID unique."""
        folder1 = use_case.execute(name="dossier1")
        folder2 = use_case.execute(name="dossier2")

        assert folder1.id != folder2.id
