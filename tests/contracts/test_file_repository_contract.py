"""Contract tests pour FileRepository : vérifie le principe de Liskov.

Toute implémentation de FileRepository doit passer ces tests.
"""

from abc import ABC, abstractmethod
from pathlib import Path

import pytest

from minidrive.application.ports import FileRepository
from minidrive.domain.entities import File
from minidrive.domain.value_objects import FileName, FileSize


def make_file(
    file_id: str = "123", name: str = "rapport.pdf", parent_id: str | None = None
) -> File:
    """Fabrique un fichier de test."""
    return File.create(id=file_id, name=FileName(name), size=FileSize(1024), parent_id=parent_id)


class FileRepositoryContract(ABC):
    """Classe de base abstraite pour tester toute implémentation de FileRepository."""

    @pytest.fixture
    @abstractmethod
    def repository(self) -> FileRepository:
        """Fixture abstraite : doit retourner une implémentation de FileRepository."""
        pass

    def test_add_and_get_file(self, repository: FileRepository) -> None:
        """Ajouter puis récupérer un fichier doit fonctionner, taille incluse."""
        repository.add(make_file())

        retrieved = repository.get("123")
        assert retrieved is not None
        assert retrieved.id == "123"
        assert retrieved.name.value == "rapport.pdf"
        assert retrieved.size.value == 1024

    def test_get_nonexistent_file_returns_none(self, repository: FileRepository) -> None:
        """Récupérer un fichier inexistant doit retourner None."""
        assert repository.get("inexistant") is None

    def test_exists_with_name(self, repository: FileRepository) -> None:
        """exists_with_name doit tenir compte du parent."""
        repository.add(make_file(file_id="1", name="a.txt", parent_id=None))
        repository.add(make_file(file_id="2", name="a.txt", parent_id="parent-1"))

        assert repository.exists_with_name("a.txt", None) is True
        assert repository.exists_with_name("a.txt", "parent-1") is True
        assert repository.exists_with_name("a.txt", "autre-parent") is False
        assert repository.exists_with_name("b.txt", None) is False

    def test_list_all_sorted_by_name(self, repository: FileRepository) -> None:
        """list_all doit retourner tous les fichiers triés par nom."""
        repository.add(make_file(file_id="2", name="zebra.bin"))
        repository.add(make_file(file_id="1", name="alpha.bin"))

        files = repository.list_all()

        assert [file.name.value for file in files] == ["alpha.bin", "zebra.bin"]

    def test_list_all_empty(self, repository: FileRepository) -> None:
        """list_all sur un repository vide doit retourner une liste vide."""
        assert repository.list_all() == []

    def test_save_updates_existing_file(self, repository: FileRepository) -> None:
        """save doit remplacer le fichier de même ID (rename/move)."""
        repository.add(make_file(file_id="1", name="ancien.txt"))

        updated = make_file(file_id="1", name="nouveau.txt", parent_id="p1")
        repository.save(updated)

        retrieved = repository.get("1")
        assert retrieved is not None
        assert retrieved.name.value == "nouveau.txt"
        assert retrieved.parent_id == "p1"
        assert retrieved.size.value == 1024

    def test_save_creates_missing_file(self, repository: FileRepository) -> None:
        """save sur un ID inconnu doit créer (sémantique upsert)."""
        repository.save(make_file(file_id="9", name="cree.txt"))

        assert repository.get("9") is not None

    def test_trashed_file_hidden_but_retrievable(self, repository: FileRepository) -> None:
        """Un fichier corbeillé : exclu de list/exists, mais get le retourne."""
        trashed = make_file(file_id="1", name="vieux.txt")
        trashed.trashed = True
        repository.add(trashed)

        retrieved = repository.get("1")
        assert retrieved is not None
        assert retrieved.trashed is True
        assert repository.list_all() == []
        assert repository.exists_with_name("vieux.txt", None) is False

    def test_delete_removes_file(self, repository: FileRepository) -> None:
        """delete doit supprimer définitivement, sans erreur si absent."""
        repository.add(make_file(file_id="1", name="ephemere.txt"))

        repository.delete("1")
        repository.delete("inexistant")  # no-op

        assert repository.get("1") is None
        assert repository.list_all() == []

    def test_list_all_include_trashed(self, repository: FileRepository) -> None:
        """list_all(include_trashed=True) doit tout retourner (traversées internes)."""
        repository.add(make_file(file_id="1", name="visible.txt"))
        trashed = make_file(file_id="2", name="cache.txt")
        trashed.trashed = True
        repository.add(trashed)

        assert [file.name.value for file in repository.list_all()] == ["visible.txt"]
        all_names = sorted(file.name.value for file in repository.list_all(include_trashed=True))
        assert all_names == ["cache.txt", "visible.txt"]


class TestInMemoryFileRepository(FileRepositoryContract):
    """Tests concrets pour InMemoryFileRepository."""

    @pytest.fixture
    def repository(self) -> FileRepository:
        """Retourne une instance d'InMemoryFileRepository."""
        from minidrive.adapters.memory.file_repository import InMemoryFileRepository

        return InMemoryFileRepository()


class TestSqliteFileRepository(FileRepositoryContract):
    """Tests concrets pour SqliteFileRepository."""

    @pytest.fixture
    def repository(self, tmp_path: Path) -> FileRepository:
        """Retourne une instance de SqliteFileRepository sur un fichier isolé."""
        from minidrive.adapters.sqlite.file_repository import SqliteFileRepository

        return SqliteFileRepository(tmp_path / "files-contract.db")
