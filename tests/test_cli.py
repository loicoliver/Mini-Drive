"""Tests de l'interface CLI (argparse, cross-platform)."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from minidrive.interfaces.cli import build_parser, ensure_utf8_stdio, main


class TestCLI:
    """Tests de l'interface en ligne de commande."""

    @pytest.fixture(autouse=True)
    def _isolated_db(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Isole chaque test CLI sur un SQLite temporaire (jamais ~/.minidrive)."""
        monkeypatch.setenv("MINIDRIVE_DB", str(tmp_path / "cli-test.db"))

    def test_mkdir_command_success(self, capsys: pytest.CaptureFixture[str]) -> None:
        """La commande mkdir doit créer un dossier et afficher un message de succès."""
        main(["mkdir", "documents"])

        captured = capsys.readouterr()
        assert "Dossier 'documents' créé avec succès" in captured.out

    def test_mkdir_via_sys_argv(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Compatibilité sys.argv (appel sans argument explicite)."""
        with patch.object(sys, "argv", ["minidrive", "mkdir", "documents"]):
            main()

        captured = capsys.readouterr()
        assert "Dossier 'documents' créé avec succès" in captured.out

    def test_ls_empty_repository(self, capsys: pytest.CaptureFixture[str]) -> None:
        """ls sur un repository vide doit afficher un message et sortir en code 0."""
        main(["ls"])

        captured = capsys.readouterr()
        assert "Aucun dossier." in captured.out

    def test_ls_lists_folders_sorted(self, capsys: pytest.CaptureFixture[str]) -> None:
        """ls doit afficher les dossiers créés, triés par nom."""
        main(["mkdir", "videos"])
        main(["mkdir", "documents"])
        capsys.readouterr()  # vide le buffer des mkdir

        main(["ls"])

        captured = capsys.readouterr()
        lines = [line for line in captured.out.splitlines() if line.strip()]
        assert len(lines) == 2
        assert lines[0].startswith("documents (ID: ")
        assert lines[1].startswith("videos (ID: ")

    def test_no_command_shows_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Lancer minidrive sans commande doit afficher l'aide et sortir en code 1."""
        with pytest.raises(SystemExit) as exc_info:
            main([])

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        # argparse print_help() va sur stdout
        assert "mkdir" in captured.out

    def test_no_command_via_sys_argv_shows_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Lancer minidrive sans commande (via sys.argv) doit afficher l'aide."""
        with patch.object(sys, "argv", ["minidrive"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "mkdir" in captured.out

    def test_mkdir_without_argument_exits_2(self, capsys: pytest.CaptureFixture[str]) -> None:
        """mkdir sans nom doit sortir en code 2 (convention argparse) avec usage sur stderr."""
        with pytest.raises(SystemExit) as exc_info:
            main(["mkdir"])

        assert exc_info.value.code == 2

        captured = capsys.readouterr()
        assert "nom" in captured.err.lower() or "usage" in captured.err.lower()

    def test_unknown_command_exits_2(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Une commande inconnue doit sortir en code 2 (convention argparse)."""
        with pytest.raises(SystemExit) as exc_info:
            main(["unknown"])

        assert exc_info.value.code == 2

        captured = capsys.readouterr()
        assert "invalid choice" in captured.err.lower()

    def test_mkdir_invalid_name_shows_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        """mkdir avec un nom invalide doit afficher une erreur métier et sortir en code 1."""
        with pytest.raises(SystemExit) as exc_info:
            main(["mkdir", "dossier/invalide"])

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Erreur:" in captured.out

    def test_help_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        """-h / --help doit afficher l'aide et sortir en code 0."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "mkdir" in captured.out

    def test_ensure_utf8_stdio_never_raises(self) -> None:
        """La sécurisation UTF-8 ne doit jamais lever (Windows/macOS/Linux)."""
        ensure_utf8_stdio()

    def test_build_parser_has_mkdir(self) -> None:
        """Le parser doit exposer la sous-commande mkdir."""
        parser = build_parser()
        args = parser.parse_args(["mkdir", "docs"])
        assert args.command == "mkdir"
        assert args.nom == "docs"
