"""Interface REST : même métier, autre adaptateur d'entrée (stdlib uniquement).

Démonstration clé : les use cases sont réutilisés TELS QUELS par la CLI
et par HTTP. Seule la couche interfaces change (principe O).
"""

import argparse
import base64
import binascii
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from minidrive.application.users import DEFAULT_USER_ID
from minidrive.bootstrap import Container, create_container
from minidrive.domain.entities import File, Folder
from minidrive.domain.errors import (
    DomainError,
    FileAlreadyExistsError,
    FolderAlreadyExistsError,
    InTrashError,
    InvalidFileNameError,
    InvalidFileSizeError,
    InvalidMoveError,
    InvalidShareError,
    PermissionDeniedError,
    QuotaExceededError,
    UnknownFileError,
    UnknownFolderError,
)

# Erreurs métier -> statut HTTP (sans fuite de stack trace)
_STATUS_BY_ERROR: tuple[tuple[type[DomainError], int], ...] = (
    (InvalidFileNameError, 400),
    (InvalidFileSizeError, 400),
    (InvalidShareError, 400),
    (InvalidMoveError, 400),
    (PermissionDeniedError, 403),
    (QuotaExceededError, 403),
    (UnknownFolderError, 404),
    (UnknownFileError, 404),
    (FolderAlreadyExistsError, 409),
    (FileAlreadyExistsError, 409),
    (InTrashError, 409),
)


def error_status(error: DomainError) -> int:
    """Mappe une erreur métier vers un statut HTTP."""
    for error_type, status in _STATUS_BY_ERROR:
        if isinstance(error, error_type):
            return status
    return 400


def folder_to_json(folder: Folder) -> dict[str, str | None]:
    """Sérialise un dossier."""
    return {
        "id": folder.id,
        "name": folder.name.value,
        "parent_id": folder.parent_id,
        "owner_id": folder.owner_id,
    }


def file_to_json(file: File) -> dict[str, str | int | None]:
    """Sérialise un fichier (métadonnées, pas le contenu)."""
    return {
        "id": file.id,
        "name": file.name.value,
        "parent_id": file.parent_id,
        "size_bytes": file.size.value,
        "owner_id": file.owner_id,
    }


class DriveHandler(BaseHTTPRequestHandler):
    """Handler HTTP : routes minimales, JSON in/out, erreurs en JSON."""

    container: Container

    def log_message(self, fmt: str, *args: object) -> None:
        """Logs sobres sur stderr (format stdlib par défaut trop verbeux)."""
        sys.stderr.write(f"minidrive-server: {self.command} {self.path}\n")

    def _acting_user(self) -> str:
        """Utilisateur agissant : ?user=, sinon local."""
        query = parse_qs(urlparse(self.path).query)
        return query.get("user", [DEFAULT_USER_ID])[0]

    def _send_json(self, status: int, payload: object) -> None:
        """Envoie une réponse JSON."""
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, data: bytes, filename: str) -> None:
        """Envoie un contenu binaire (download)."""
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict[str, object]:
        """Lit un corps JSON ({} si absent)."""
        length = int(self.headers.get("Content-Length") or 0)
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        parsed: dict[str, object] = json.loads(raw.decode("utf-8"))
        return parsed

    def _route(self) -> None:
        """Dispatche la requête vers le use case adéquat."""
        parsed = urlparse(self.path)
        parts = [part for part in parsed.path.split("/") if part]
        user = self._acting_user()

        if self.command == "GET" and parts == ["api", "health"]:
            self._send_json(200, {"status": "ok"})
        elif self.command == "GET" and parts == ["api", "folders"]:
            folders = self.container.list_folders.execute(user_id=user)
            self._send_json(200, [folder_to_json(folder) for folder in folders])
        elif self.command == "POST" and parts == ["api", "folders"]:
            body = self._read_json()
            folder = self.container.create_folder.execute(
                name=str(body.get("name", "")),
                parent_id=_optional_str(body.get("parent_id")),
                owner_id=user,
            )
            self._send_json(201, folder_to_json(folder))
        elif self.command == "GET" and parts == ["api", "files"]:
            files = self.container.list_files.execute(user_id=user)
            self._send_json(200, [file_to_json(file) for file in files])
        elif self.command == "POST" and parts == ["api", "files"]:
            body = self._read_json()
            try:
                data = base64.b64decode(str(body.get("content_base64", "")), validate=True)
            except (binascii.Error, ValueError) as exc:
                raise InvalidFileSizeError(-1, f"contenu base64 invalide : {exc}") from exc
            file = self.container.upload_file.execute(
                name=str(body.get("name", "")),
                data=data,
                parent_id=_optional_str(body.get("parent_id")),
                user_id=user,
            )
            self._send_json(201, file_to_json(file))
        elif (
            self.command == "GET"
            and len(parts) == 4
            and parts[:2] == ["api", "files"]
            and parts[3] == "content"
        ):
            file, data = self.container.download_file.execute(file_id=parts[2], user_id=user)
            self._send_bytes(data, file.name.value)
        else:
            self._send_json(404, {"error": f"route inconnue : {self.command} {parsed.path}"})

    def _handle(self) -> None:
        """Point d'entrée avec mapping d'erreurs."""
        try:
            self._route()
        except DomainError as error:
            self._send_json(error_status(error), {"error": str(error)})
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "corps JSON invalide"})
        except BrokenPipeError:
            pass  # client parti : rien à envoyer
        except Exception as error:  # noqa: BLE001 - jamais de 500 avec stack trace
            self._send_json(500, {"error": f"erreur inattendue : {error}"})

    def do_GET(self) -> None:
        """Route GET."""
        self._handle()

    def do_POST(self) -> None:
        """Route POST."""
        self._handle()


def _optional_str(value: object) -> str | None:
    """Normalise un champ JSON optionnel (None ou str)."""
    if value is None:
        return None
    text = str(value)
    return text if text else None


def build_server(db_path: Path | str | None = None, port: int = 0) -> ThreadingHTTPServer:
    """Construit le serveur HTTP (port 0 = port éphémère, pour les tests).

    Args:
        db_path: Chemin SQLite (défaut : ~/.minidrive via le conteneur)
        port: Port d'écoute (0 = choisi par l'OS)

    Returns:
        Un serveur prêt à servir (serve_forever)
    """
    container = create_container(db_path=db_path)
    handler = type("BoundDriveHandler", (DriveHandler,), {"container": container})
    return ThreadingHTTPServer(("127.0.0.1", port), handler)


def build_parser() -> argparse.ArgumentParser:
    """Construit le parser de minidrive-serve (séparé pour les tests)."""
    parser = argparse.ArgumentParser(
        prog="minidrive serve",
        description="Serveur HTTP Mini-Drive (mêmes use cases que la CLI).",
    )
    parser.add_argument("--port", type=int, default=8000, help="Port d'écoute (défaut : 8000)")
    return parser


def main(argv: list[str] | None = None) -> None:
    """Démarre le serveur HTTP."""
    args = build_parser().parse_args(argv)
    server = build_server(port=args.port)
    print(f"Mini-Drive sur http://127.0.0.1:{server.server_port} (Ctrl+C pour arrêter)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
