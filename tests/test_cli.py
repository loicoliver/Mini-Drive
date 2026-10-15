"""Tests de l'interface CLI."""

import sys
from unittest.mock import patch

import pytest

from minidrive.interfaces.cli import main


class TestCLI:
    """Tests de l'interface en ligne de commande."""

    def test_mkdir_command_success(self, capsys: pytest.CaptureFixture[str]) -> None:
        """La commande mkdir doit créer un dossier et afficher un message de succès."""
        with patch.object(sys, "argv", ["minidrive", "mkdir", "documents"]):
            main()

        captured = capsys.readouterr()
        assert "✓ Dossier 'documents' créé avec succès" in captured.out

    def test_mkdir_without_argument_shows_usage(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """mkdir sans nom de dossier doit afficher l'usage."""
        with patch.object(sys, "argv", ["minidrive", "mkdir"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Usage: minidrive mkdir <nom>" in captured.out

    def test_unknown_command_shows_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Une commande inconnue doit afficher une erreur."""
        with patch.object(sys, "argv", ["minidrive", "unknown"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Commande inconnue: unknown" in captured.out

    def test_no_command_shows_usage(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Lancer minidrive sans commande doit afficher l'usage."""
        with patch.object(sys, "argv", ["minidrive"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Usage: minidrive <commande> [arguments]" in captured.out

    def test_mkdir_invalid_name_shows_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """mkdir avec un nom invalide doit afficher une erreur."""
        with patch.object(sys, "argv", ["minidrive", "mkdir", "dossier/invalide"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "✗ Erreur:" in captured.out
