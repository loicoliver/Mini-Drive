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
        """ls sur un drive vide doit afficher un message et sortir en code 0."""
        main(["ls"])

        captured = capsys.readouterr()
        assert "Drive vide." in captured.out

    def test_ls_lists_folders_sorted(self, capsys: pytest.CaptureFixture[str]) -> None:
        """ls doit afficher les dossiers créés, triés par nom."""
        main(["mkdir", "videos"])
        main(["mkdir", "documents"])
        capsys.readouterr()  # vide le buffer des mkdir

        main(["ls"])

        captured = capsys.readouterr()
        lines = [line for line in captured.out.splitlines() if line.strip()]
        assert lines[0] == "Dossiers :"
        assert lines[1].startswith("  documents (ID: ")
        assert lines[2].startswith("  videos (ID: ")

    def test_ls_lists_files(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """ls doit afficher les fichiers uploadés avec leur taille."""
        source = tmp_path / "note.txt"
        source.write_bytes(b"bonjour")
        main(["upload", str(source)])
        capsys.readouterr()

        main(["ls"])

        captured = capsys.readouterr()
        assert "Fichiers :" in captured.out
        assert "note.txt (7 octets, ID: " in captured.out

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

    def test_upload_success(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """upload doit copier le fichier et afficher un message de succès."""
        source = tmp_path / "note.txt"
        source.write_bytes(b"bonjour")

        main(["upload", str(source)])

        captured = capsys.readouterr()
        assert "Fichier 'note.txt' uploadé" in captured.out
        assert "7 octets" in captured.out

    def test_upload_missing_file(self, capsys: pytest.CaptureFixture[str]) -> None:
        """upload d'un fichier inexistant doit afficher une erreur et sortir en code 1."""
        with pytest.raises(SystemExit) as exc_info:
            main(["upload", "n-existe-pas.txt"])

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "introuvable" in captured.out

    def test_upload_then_ls_and_duplicate(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Un fichier uploadé persiste ; le ré-uploader doit échouer (doublon)."""
        source = tmp_path / "a.bin"
        source.write_bytes(b"123")

        main(["upload", str(source)])
        with pytest.raises(SystemExit) as exc_info:
            main(["upload", str(source)])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "existe déjà" in captured.out

    def test_download_success(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """download doit écrire le contenu à la destination demandée."""
        source = tmp_path / "origine.txt"
        source.write_bytes(b"abc")
        main(["upload", str(source)])
        capsys.readouterr()
        monkeypatch.chdir(tmp_path)

        main(["ls"])  # repère l'ID via la sortie
        out = capsys.readouterr().out
        file_id = out.split("ID: ")[1].split(")")[0]
        destination = tmp_path / "copie.txt"

        main(["download", file_id, "--vers", str(destination)])

        assert destination.read_bytes() == b"abc"
        captured = capsys.readouterr()
        assert "téléchargé vers" in captured.out

    def test_download_default_destination(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sans --vers, download écrit le nom d'origine dans le dossier courant."""
        source = tmp_path / "sub" / "doc.txt"
        source.parent.mkdir()
        source.write_bytes(b"data")
        main(["upload", str(source)])
        capsys.readouterr()
        workdir = tmp_path / "work"
        workdir.mkdir()
        monkeypatch.chdir(workdir)
        main(["ls"])
        out = capsys.readouterr().out
        file_id = out.split("ID: ")[1].split(")")[0]

        main(["download", file_id])

        assert (workdir / "doc.txt").read_bytes() == b"data"

    def test_download_unknown_id(self, capsys: pytest.CaptureFixture[str]) -> None:
        """download d'un ID inconnu doit afficher une erreur et sortir en code 1."""
        with pytest.raises(SystemExit) as exc_info:
            main(["download", "inexistant"])

        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Fichier inconnu" in captured.out

    def test_download_refuses_existing_destination(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """download ne doit jamais écraser un fichier existant."""
        source = tmp_path / "a.txt"
        source.write_bytes(b"nouveau")
        main(["upload", str(source)])
        capsys.readouterr()
        main(["ls"])
        out = capsys.readouterr().out
        file_id = out.split("ID: ")[1].split(")")[0]
        existing = tmp_path / "cible.txt"
        existing.write_bytes(b"precieux")

        with pytest.raises(SystemExit) as exc_info:
            main(["download", file_id, "--vers", str(existing)])

        assert exc_info.value.code == 1
        assert existing.read_bytes() == b"precieux"
        captured = capsys.readouterr()
        assert "existe déjà" in captured.out

    def test_help_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        """-h / --help doit afficher l'aide et sortir en code 0."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])

        assert exc_info.value.code == 0

        captured = capsys.readouterr()
        assert "mkdir" in captured.out
        assert "ls" in captured.out
        assert "upload" in captured.out

    def test_ensure_utf8_stdio_never_raises(self) -> None:
        """La sécurisation UTF-8 ne doit jamais lever (Windows/macOS/Linux)."""
        ensure_utf8_stdio()

    def test_build_parser_has_mkdir(self) -> None:
        """Le parser doit exposer la sous-commande mkdir."""
        parser = build_parser()
        args = parser.parse_args(["mkdir", "docs"])
        assert args.command == "mkdir"
        assert args.nom == "docs"
