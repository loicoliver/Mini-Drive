"""Tests spécifiques à l'adapteur SQLite (au-delà du contrat)."""

from pathlib import Path

from minidrive.adapters.sqlite.folder_repository import SqliteFolderRepository
from minidrive.domain.entities import Folder
from minidrive.domain.value_objects import FileName


class TestSqliteFolderRepository:
    """Tests spécifiques à l'implémentation SqliteFolderRepository."""

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """Le repository doit créer les dossiers parents du fichier .db."""
        db_path = tmp_path / "nested" / "dirs" / "folders.db"

        SqliteFolderRepository(db_path)

        assert db_path.exists()

    def test_data_survives_reopen(self, tmp_path: Path) -> None:
        """Les données doivent persister entre deux instances (preuve de persistance)."""
        db_path = tmp_path / "folders.db"
        folder = Folder.create(id="123", name=FileName("documents"))

        SqliteFolderRepository(db_path).add(folder)

        reopened = SqliteFolderRepository(db_path)
        retrieved = reopened.get("123")

        assert retrieved is not None
        assert retrieved.id == "123"
        assert retrieved.name.value == "documents"
        assert reopened.exists_with_name("documents", None) is True

    def test_accepts_str_path(self, tmp_path: Path) -> None:
        """Le repository doit accepter un chemin str ou Path."""
        repository = SqliteFolderRepository(str(tmp_path / "folders.db"))
        repository.add(Folder.create(id="1", name=FileName("docs")))

        assert repository.get("1") is not None
