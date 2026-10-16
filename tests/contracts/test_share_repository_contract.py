"""Contract tests pour ShareRepository : vérifie le principe de Liskov."""

from abc import ABC, abstractmethod
from pathlib import Path

import pytest

from minidrive.application.ports import ShareRepository
from minidrive.domain.entities import Share


class ShareRepositoryContract(ABC):
    """Classe de base abstraite pour tester toute implémentation de ShareRepository."""

    @pytest.fixture
    @abstractmethod
    def repository(self) -> ShareRepository:
        """Fixture abstraite : doit retourner une implémentation de ShareRepository."""
        pass

    def test_grant_and_role_for(self, repository: ShareRepository) -> None:
        """Accorder un partage doit rendre le rôle visible."""
        repository.grant(Share(node_type="folder", node_id="d1", user_id="bob", role="reader"))

        assert repository.role_for("folder", "d1", "bob") == "reader"

    def test_role_for_unknown_returns_none(self, repository: ShareRepository) -> None:
        """Sans partage, role_for doit retourner None."""
        assert repository.role_for("folder", "d1", "bob") is None
        assert repository.role_for("file", "d1", "bob") is None

    def test_grant_updates_role(self, repository: ShareRepository) -> None:
        """Ré-accorder doit mettre à jour le rôle (upsert)."""
        repository.grant(Share(node_type="file", node_id="f1", user_id="bob", role="reader"))
        repository.grant(Share(node_type="file", node_id="f1", user_id="bob", role="editor"))

        assert repository.role_for("file", "f1", "bob") == "editor"

    def test_revoke_removes_share(self, repository: ShareRepository) -> None:
        """Révoquer doit retirer le partage, sans erreur si absent."""
        repository.grant(Share(node_type="file", node_id="f1", user_id="bob", role="reader"))

        repository.revoke("file", "f1", "bob")
        repository.revoke("file", "f1", "bob")  # no-op

        assert repository.role_for("file", "f1", "bob") is None

    def test_delete_for_node_removes_all_shares(self, repository: ShareRepository) -> None:
        """Purger un nœud doit supprimer tous ses partages, pas ceux des autres."""
        repository.grant(Share(node_type="folder", node_id="d1", user_id="bob", role="reader"))
        repository.grant(Share(node_type="folder", node_id="d1", user_id="carol", role="editor"))
        repository.grant(Share(node_type="folder", node_id="d2", user_id="bob", role="reader"))

        repository.delete_for_node("folder", "d1")

        assert repository.role_for("folder", "d1", "bob") is None
        assert repository.role_for("folder", "d1", "carol") is None
        assert repository.role_for("folder", "d2", "bob") == "reader"


class TestInMemoryShareRepository(ShareRepositoryContract):
    """Tests concrets pour InMemoryShareRepository."""

    @pytest.fixture
    def repository(self) -> ShareRepository:
        """Retourne une instance d'InMemoryShareRepository."""
        from minidrive.adapters.memory.share_repository import InMemoryShareRepository

        return InMemoryShareRepository()


class TestSqliteShareRepository(ShareRepositoryContract):
    """Tests concrets pour SqliteShareRepository."""

    @pytest.fixture
    def repository(self, tmp_path: Path) -> ShareRepository:
        """Retourne une instance de SqliteShareRepository sur un fichier isolé."""
        from minidrive.adapters.sqlite.share_repository import SqliteShareRepository

        return SqliteShareRepository(tmp_path / "shares-contract.db")
