"""Tests du bootstrap (composition root)."""

from pathlib import Path

import pytest

from minidrive.bootstrap import Container, create_container


class TestBootstrap:
    """Tests de la composition root."""

    def test_create_container(self, tmp_path: Path) -> None:
        """create_container doit retourner un conteneur configuré."""
        container = create_container(db_path=tmp_path / "test.db")
        assert isinstance(container, Container)

    def test_container_provides_create_folder(self, tmp_path: Path) -> None:
        """Le conteneur doit fournir le use case CreateFolder."""
        container = create_container(db_path=tmp_path / "test.db")
        use_case = container.create_folder

        assert use_case is not None
        assert hasattr(use_case, "execute")
        assert callable(use_case.execute)

    def test_create_folder_is_wired_correctly(self, tmp_path: Path) -> None:
        """Le use case CreateFolder doit être câblé avec les dépendances."""
        container = create_container(db_path=tmp_path / "test.db")

        # Tester que le use case fonctionne de bout en bout
        folder = container.create_folder.execute("test-folder")

        assert folder.name.value == "test-folder"
        assert folder.id is not None

    def test_container_uses_sqlite_by_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sans db_path explicite, le conteneur utilise MINIDRIVE_DB puis ~/.minidrive."""
        db_path = tmp_path / "env.db"
        monkeypatch.setenv("MINIDRIVE_DB", str(db_path))
        container = create_container()

        assert container.db_path == db_path
        folder = container.create_folder.execute("env-folder")
        assert folder.name.value == "env-folder"
        assert db_path.exists()
