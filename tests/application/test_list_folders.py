"""Tests du use case ListFolders."""

from minidrive.adapters.memory.folder_repository import InMemoryFolderRepository
from minidrive.adapters.memory.id_generator import UuidIdGenerator
from minidrive.adapters.memory.share_repository import InMemoryShareRepository
from minidrive.application.use_cases.create_folder import CreateFolder
from minidrive.application.use_cases.list_folders import ListFolders


def make_list_folders() -> tuple[ListFolders, CreateFolder]:
    """Fabrique un ListFolders câblé sur un repository mémoire vierge."""
    repository = InMemoryFolderRepository()
    return (
        ListFolders(folder_repository=repository, share_repository=InMemoryShareRepository()),
        CreateFolder(folder_repository=repository, id_generator=UuidIdGenerator()),
    )


class TestListFolders:
    """Tests du use case ListFolders."""

    def test_list_empty_repository(self) -> None:
        """Lister un repository vide doit retourner une liste vide."""
        list_folders, _ = make_list_folders()

        assert list_folders.execute() == []

    def test_list_returns_created_folders(self) -> None:
        """Lister doit retourner les dossiers créés."""
        list_folders, create_folder = make_list_folders()
        create_folder.execute("documents")
        create_folder.execute("images")

        folders = list_folders.execute()

        assert [folder.name.value for folder in folders] == ["documents", "images"]

    def test_list_is_sorted_by_name(self) -> None:
        """La liste doit être triée par nom, quel que soit l'ordre de création."""
        list_folders, create_folder = make_list_folders()
        create_folder.execute("videos")
        create_folder.execute("documents")
        create_folder.execute("images")

        folders = list_folders.execute()

        assert [folder.name.value for folder in folders] == [
            "documents",
            "images",
            "videos",
        ]

    def test_list_trashed_only(self) -> None:
        """trashed_only=True ne retourne que la corbeille."""
        list_folders, create_folder = make_list_folders()
        create_folder.execute("visible")
        trashed = create_folder.execute("poubelle")
        trashed.trashed = True

        assert [f.name.value for f in list_folders.execute()] == ["visible"]
        assert [f.name.value for f in list_folders.execute(trashed_only=True)] == ["poubelle"]
