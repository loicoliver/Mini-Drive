"""Tests des entités du domain."""

from minidrive.domain.entities import Folder
from minidrive.domain.value_objects import FileName


class TestFolder:
    """Tests de l'entité Folder."""

    def test_create_folder_with_factory(self) -> None:
        """La factory method create doit créer un dossier valide."""
        name = FileName("documents")
        folder = Folder.create(id="123", name=name, parent_id=None)

        assert folder.id == "123"
        assert folder.name == name
        assert folder.parent_id is None

    def test_create_folder_with_parent(self) -> None:
        """Un dossier peut avoir un parent."""
        name = FileName("sous-dossier")
        folder = Folder.create(id="456", name=name, parent_id="123")

        assert folder.id == "456"
        assert folder.name.value == "sous-dossier"
        assert folder.parent_id == "123"

    def test_folder_identity(self) -> None:
        """Deux dossiers avec le même ID sont le même dossier (identité)."""
        name1 = FileName("dossier1")
        name2 = FileName("dossier2")

        folder1 = Folder.create(id="same-id", name=name1)
        folder2 = Folder.create(id="same-id", name=name2)

        # Même ID = même entité (même si les noms diffèrent)
        assert folder1.id == folder2.id
