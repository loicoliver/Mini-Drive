"""Tests spécifiques à l'adapteur SQLite (au-delà du contrat)."""

import sqlite3
from pathlib import Path

from minidrive.adapters.sqlite._database import ensure_column
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

    def test_migrates_legacy_database(self, tmp_path: Path) -> None:
        """Un .db d'avant la corbeille doit être migré sans perdre ses données."""
        db_path = tmp_path / "legacy.db"
        connection = sqlite3.connect(str(db_path))
        try:
            with connection:
                connection.execute(
                    "CREATE TABLE folders (id TEXT PRIMARY KEY, name TEXT NOT NULL, parent_id TEXT)"
                )
                connection.execute(
                    "INSERT INTO folders (id, name, parent_id) VALUES ('1', 'docs', NULL)"
                )
        finally:
            connection.close()

        repository = SqliteFolderRepository(db_path)

        retrieved = repository.get("1")
        assert retrieved is not None
        assert retrieved.name.value == "docs"
        assert retrieved.trashed is False

    def test_ensure_column_is_idempotent(self, tmp_path: Path) -> None:
        """ensure_column sur une colonne existante ne doit rien changer."""
        db_path = tmp_path / "folders.db"
        SqliteFolderRepository(db_path)

        ensure_column(db_path, "folders", "trashed", "INTEGER NOT NULL DEFAULT 0")

        assert SqliteFolderRepository(db_path).get("nope") is None
