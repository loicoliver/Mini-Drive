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

    def test_container_quota_from_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MINIDRIVE_QUOTA_BYTES doit activer un plafond suivi par utilisateur."""
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("MINIDRIVE_DB", str(db_path))
        monkeypatch.setenv("MINIDRIVE_QUOTA_BYTES", "10")

        alice = create_container()
        alice.upload_file.execute(name="a.txt", data=b"12345678", user_id="alice")

        assert alice.quota_policy.get_remaining_quota("alice") == 2
        assert alice.quota_policy.get_remaining_quota("bob") == 10
        with pytest.raises(QuotaExceededError):
            alice.upload_file.execute(name="b.txt", data=b"123", user_id="alice")

    def test_container_invalid_quota_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MINIDRIVE_QUOTA_BYTES non entier doit échouer explicitement."""
        monkeypatch.setenv("MINIDRIVE_DB", str(tmp_path / "test.db"))
        monkeypatch.setenv("MINIDRIVE_QUOTA_BYTES", "beaucoup")

        with pytest.raises(ValueError, match="MINIDRIVE_QUOTA_BYTES invalide"):
            create_container()

    def test_container_provides_rename_and_move(self, tmp_path: Path) -> None:
        """Le conteneur doit fournir les use cases rename/move, câblés ensemble."""
        container = create_container(db_path=tmp_path / "test.db")
        folder = container.create_folder.execute("dossier")
        uploaded = container.upload_file.execute(name="a.txt", data=b"1")

        renamed = container.rename_folder.execute(folder_id=folder.id, new_name="renomme")
        moved = container.move_file.execute(file_id=uploaded.id, new_parent_id=folder.id)

        assert renamed.name.value == "renomme"
        assert moved.parent_id == folder.id
        assert container.rename_file is not None
        assert container.move_folder is not None

    def test_container_provides_trash_and_purge(self, tmp_path: Path) -> None:
        """Le conteneur doit fournir trash/restore/purge de bout en bout."""
        container = create_container(db_path=tmp_path / "test.db")
        folder = container.create_folder.execute("dossier")

        container.trash_folder.execute(folder_id=folder.id)
        assert container.list_folders.execute() == []

        container.restore_folder.execute(folder_id=folder.id)
        assert len(container.list_folders.execute()) == 1

        container.purge_folder.execute(folder_id=folder.id)
        assert container.list_folders.execute() == []
        assert container.trash_file is not None
        assert container.restore_file is not None
        assert container.purge_file is not None

    def test_container_provides_sharing(self, tmp_path: Path) -> None:
        """Le conteneur doit fournir share/unshare câblés sur les mêmes repos."""
        container = create_container(db_path=tmp_path / "test.db")
        folder = container.create_folder.execute("dossier", owner_id="alice")

        share = container.share_folder.execute(
            folder_id=folder.id, user_id="bob", role="reader", owner_id="alice"
        )
        assert share.role == "reader"

        container.unshare_folder.execute(folder_id=folder.id, user_id="bob", owner_id="alice")
        assert container.share_file is not None
        assert container.unshare_file is not None

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
