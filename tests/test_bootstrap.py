"""Tests du bootstrap (composition root)."""

from pathlib import Path

import pytest

from minidrive.application.quota_policies import FixedQuotaPolicy
from minidrive.bootstrap import Container, create_container
from minidrive.domain.errors import QuotaExceededError


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

    def test_container_provides_list_folders(self, tmp_path: Path) -> None:
        """Le conteneur doit fournir le use case ListFolders, câblé sur le même repo."""
        container = create_container(db_path=tmp_path / "test.db")

        container.create_folder.execute("test-folder")
        folders = container.list_folders.execute()

        assert [folder.name.value for folder in folders] == ["test-folder"]

    def test_container_provides_upload_file(self, tmp_path: Path) -> None:
        """Le conteneur doit fournir UploadFile, blobs sous le dossier du .db."""
        container = create_container(db_path=tmp_path / "test.db")

        file = container.upload_file.execute(name="a.txt", data=b"hello")

        assert file.name.value == "a.txt"
        assert file.size.value == 5
        assert (tmp_path / "blobs" / file.id).read_bytes() == b"hello"

    def test_container_provides_list_and_download_file(self, tmp_path: Path) -> None:
        """ListFiles et DownloadFile doivent partager le même stockage."""
        container = create_container(db_path=tmp_path / "test.db")
        uploaded = container.upload_file.execute(name="a.txt", data=b"hello")

        files = container.list_files.execute()
        file, data = container.download_file.execute(file_id=uploaded.id)

        assert [item.name.value for item in files] == ["a.txt"]
        assert data == b"hello"

    def test_container_accepts_quota_policy(self, tmp_path: Path) -> None:
        """Le conteneur doit accepter une politique de quota (Strategy interchangeable)."""
        container = create_container(
            db_path=tmp_path / "test.db", quota_policy=FixedQuotaPolicy(quota_bytes=4)
        )

        container.upload_file.execute(name="ok.txt", data=b"1234")
        with pytest.raises(QuotaExceededError):
            container.upload_file.execute(name="ko.txt", data=b"12345")

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
