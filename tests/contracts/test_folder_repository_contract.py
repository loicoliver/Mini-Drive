"""Contract tests pour FolderRepository : vérifie le principe de Liskov.

Toute implémentation de FolderRepository doit passer ces tests.
Démontre le principe L (Liskov Substitution) : toutes les implémentations
sont interchangeables et doivent respecter le même contrat.
"""

from abc import ABC, abstractmethod
from pathlib import Path

import pytest

from minidrive.application.ports import FolderRepository
from minidrive.domain.entities import Folder
from minidrive.domain.value_objects import FileName


class FolderRepositoryContract(ABC):
    """Classe de base abstraite pour tester toute implémentation de FolderRepository.

    Pour tester une nouvelle implémentation, il suffit d'hériter de cette classe
    et d'implémenter la fixture create_repository. Aucun autre code n'est nécessaire.
    """

    @pytest.fixture
    @abstractmethod
    def repository(self) -> FolderRepository:
        """Fixture abstraite : doit retourner une implémentation de FolderRepository."""
        pass

    def test_add_and_get_folder(self, repository: FolderRepository) -> None:
        """Ajouter puis récupérer un dossier doit fonctionner."""
        folder = Folder.create(id="123", name=FileName("documents"))
        repository.add(folder)

        retrieved = repository.get("123")
        assert retrieved is not None
        assert retrieved.id == "123"
        assert retrieved.name.value == "documents"

    def test_get_nonexistent_folder_returns_none(self, repository: FolderRepository) -> None:
        """Récupérer un dossier inexistant doit retourner None."""
        result = repository.get("inexistant")
        assert result is None

    def test_exists_with_name_returns_true_when_exists(self, repository: FolderRepository) -> None:
        """exists_with_name doit retourner True si le dossier existe."""
        folder = Folder.create(id="123", name=FileName("documents"))
        repository.add(folder)

        assert repository.exists_with_name("documents", None) is True

    def test_exists_with_name_returns_false_when_not_exists(
        self, repository: FolderRepository
    ) -> None:
        """exists_with_name doit retourner False si le dossier n'existe pas."""
        assert repository.exists_with_name("inexistant", None) is False

    def test_exists_with_name_checks_parent(self, repository: FolderRepository) -> None:
        """exists_with_name doit vérifier le parent également."""
        folder1 = Folder.create(id="1", name=FileName("images"), parent_id=None)
        folder2 = Folder.create(id="2", name=FileName("images"), parent_id="parent-123")

        repository.add(folder1)
        repository.add(folder2)

        assert repository.exists_with_name("images", None) is True
        assert repository.exists_with_name("images", "parent-123") is True
        assert repository.exists_with_name("images", "autre-parent") is False

    def test_add_multiple_folders(self, repository: FolderRepository) -> None:
        """Ajouter plusieurs dossiers doit fonctionner."""
        folder1 = Folder.create(id="1", name=FileName("documents"))
        folder2 = Folder.create(id="2", name=FileName("images"))

        repository.add(folder1)
        repository.add(folder2)

        assert repository.get("1") is not None
        assert repository.get("2") is not None

    def test_folder_with_parent(self, repository: FolderRepository) -> None:
        """Ajouter un dossier avec un parent doit fonctionner."""
        folder = Folder.create(id="456", name=FileName("sous-dossier"), parent_id="123")
        repository.add(folder)

        retrieved = repository.get("456")
        assert retrieved is not None
        assert retrieved.parent_id == "123"

    def test_list_all_returns_empty_when_no_folder(self, repository: FolderRepository) -> None:
        """list_all sur un repository vide doit retourner une liste vide."""
        assert repository.list_all() == []

    def test_list_all_returns_all_folders_sorted_by_name(
        self, repository: FolderRepository
    ) -> None:
        """list_all doit retourner tous les dossiers triés par nom."""
        repository.add(Folder.create(id="2", name=FileName("images")))
        repository.add(Folder.create(id="1", name=FileName("documents")))
        repository.add(Folder.create(id="3", name=FileName("videos"), parent_id="1"))

        folders = repository.list_all()

        assert [folder.name.value for folder in folders] == [
            "documents",
            "images",
            "videos",
        ]


class TestInMemoryFolderRepository(FolderRepositoryContract):
    """Tests concrets pour InMemoryFolderRepository.

    Hérite tous les tests du contrat, il suffit de fournir la fixture.
    """

    @pytest.fixture
    def repository(self) -> FolderRepository:
        """Retourne une instance d'InMemoryFolderRepository."""
        from minidrive.adapters.memory.folder_repository import InMemoryFolderRepository

        return InMemoryFolderRepository()


class TestSqliteFolderRepository(FolderRepositoryContract):
    """Tests concrets pour SqliteFolderRepository (même contrat, autre implémentation)."""

    @pytest.fixture
    def repository(self, tmp_path: Path) -> FolderRepository:
        """Retourne une instance de SqliteFolderRepository sur un fichier isolé."""
        from minidrive.adapters.sqlite.folder_repository import SqliteFolderRepository

        return SqliteFolderRepository(tmp_path / "contract.db")
