"""Tests spécifiques aux adapteurs memory (au-delà du contrat)."""

from minidrive.adapters.memory.folder_repository import InMemoryFolderRepository
from minidrive.adapters.memory.id_generator import UuidIdGenerator
from minidrive.domain.entities import Folder
from minidrive.domain.value_objects import FileName


class TestInMemoryFolderRepository:
    """Tests spécifiques à l'implémentation InMemoryFolderRepository."""

    def test_repository_starts_empty(self) -> None:
        """Un nouveau repository doit être vide."""
        repository = InMemoryFolderRepository()
        assert repository.get("any-id") is None
        assert repository.exists_with_name("any-name", None) is False

    def test_repository_isolation(self) -> None:
        """Deux instances de repository doivent être isolées."""
        repo1 = InMemoryFolderRepository()
        repo2 = InMemoryFolderRepository()

        folder = Folder.create(id="123", name=FileName("test"))
        repo1.add(folder)

        assert repo1.get("123") is not None
        assert repo2.get("123") is None


class TestUuidIdGenerator:
    """Tests de l'implémentation UuidIdGenerator."""

    def test_generates_valid_uuid(self) -> None:
        """Le générateur doit produire des UUIDs valides."""
        generator = UuidIdGenerator()
        generated_id = generator.generate()

        assert isinstance(generated_id, str)
        assert len(generated_id) == 36  # Format UUID standard : 8-4-4-4-12
        assert generated_id.count("-") == 4

    def test_generates_unique_ids(self) -> None:
        """Chaque appel doit générer un ID unique."""
        generator = UuidIdGenerator()
        ids = [generator.generate() for _ in range(100)]

        # Tous les IDs doivent être uniques
        assert len(ids) == len(set(ids))
