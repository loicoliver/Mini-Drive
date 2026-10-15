"""Tests du bootstrap (composition root)."""

from minidrive.bootstrap import Container, create_container


class TestBootstrap:
    """Tests de la composition root."""

    def test_create_container(self) -> None:
        """create_container doit retourner un conteneur configuré."""
        container = create_container()
        assert isinstance(container, Container)

    def test_container_provides_create_folder(self) -> None:
        """Le conteneur doit fournir le use case CreateFolder."""
        container = create_container()
        use_case = container.create_folder

        assert use_case is not None
        assert hasattr(use_case, "execute")
        assert callable(use_case.execute)

    def test_create_folder_is_wired_correctly(self) -> None:
        """Le use case CreateFolder doit être câblé avec les dépendances."""
        container = create_container()

        # Tester que le use case fonctionne de bout en bout
        folder = container.create_folder.execute("test-folder")

        assert folder.name.value == "test-folder"
        assert folder.id is not None
