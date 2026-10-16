"""Tests des value objects du domain."""

import pytest

from minidrive.domain.errors import InvalidFileNameError, InvalidFileSizeError
from minidrive.domain.value_objects import FileName, FileSize


class TestFileName:
    """Tests du value object FileName."""

    def test_valid_filename(self) -> None:
        """Un nom valide doit être accepté."""
        name = FileName("mon_dossier")
        assert name.value == "mon_dossier"
        assert str(name) == "mon_dossier"

    def test_empty_name_raises_error(self) -> None:
        """Un nom vide doit lever InvalidFileNameError."""
        with pytest.raises(InvalidFileNameError) as exc_info:
            FileName("")
        assert "ne peut pas être vide" in str(exc_info.value)

    def test_name_with_forward_slash_raises_error(self) -> None:
        """Un nom avec / doit lever InvalidFileNameError."""
        with pytest.raises(InvalidFileNameError) as exc_info:
            FileName("dossier/sous-dossier")
        assert "séparateurs de chemin" in str(exc_info.value)

    def test_name_with_backslash_raises_error(self) -> None:
        """Un nom avec \\ doit lever InvalidFileNameError."""
        with pytest.raises(InvalidFileNameError) as exc_info:
            FileName("dossier\\sous-dossier")
        assert "séparateurs de chemin" in str(exc_info.value)

    def test_name_too_long_raises_error(self) -> None:
        """Un nom de plus de 255 caractères doit lever InvalidFileNameError."""
        long_name = "a" * 256
        with pytest.raises(InvalidFileNameError) as exc_info:
            FileName(long_name)
        assert "255 caractères" in str(exc_info.value)

    def test_name_exactly_255_chars_is_valid(self) -> None:
        """Un nom de exactement 255 caractères doit être accepté."""
        name = FileName("a" * 255)
        assert len(name.value) == 255

    def test_filename_is_immutable(self) -> None:
        """FileName est un value object immuable (frozen dataclass)."""
        name = FileName("test")
        with pytest.raises(AttributeError):
            name.value = "nouveau"  # type: ignore[misc]

    def test_filename_equality(self) -> None:
        """Deux FileName avec la même valeur doivent être égaux."""
        name1 = FileName("test")
        name2 = FileName("test")
        assert name1 == name2
        assert hash(name1) == hash(name2)


class TestFileSize:
    """Tests du value object FileSize."""

    def test_valid_size(self) -> None:
        """Une taille positive doit être acceptée."""
        size = FileSize(1024)
        assert size.value == 1024
        assert str(size) == "1024 octets"

    def test_zero_size_is_valid(self) -> None:
        """Un fichier vide (0 octet) doit être accepté."""
        assert FileSize(0).value == 0

    def test_negative_size_raises_error(self) -> None:
        """Une taille négative doit lever InvalidFileSizeError."""
        with pytest.raises(InvalidFileSizeError) as exc_info:
            FileSize(-1)
        assert "négative" in str(exc_info.value)

    def test_filesize_is_immutable(self) -> None:
        """FileSize est un value object immuable (frozen dataclass)."""
        size = FileSize(10)
        with pytest.raises(AttributeError):
            size.value = 20  # type: ignore[misc]
