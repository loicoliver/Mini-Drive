"""Tests de l'interface REST (serveur réel sur port éphémère, client urllib stdlib)."""

import base64
import json
import threading
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

from minidrive.interfaces.rest_api import build_server


class ApiClient:
    """Mini-client HTTP stdlib pour les tests."""

    def __init__(self, base_url: str) -> None:
        """Initialise le client sur l'URL de base du serveur."""
        self._base_url = base_url

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, object] | None = None,
        user: str | None = None,
    ) -> tuple[int, object]:
        """Exécute une requête, retourne (statut, JSON ou bytes)."""
        url = self._base_url + path
        if user is not None:
            separator = "&" if "?" in url else "?"
            url += f"{separator}user={urllib.parse.quote(user)}"
        data = None
        headers = {}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers = {"Content-Type": "application/json"}
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request) as response:
                raw = response.read()
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return response.status, json.loads(raw.decode("utf-8"))
                return response.status, raw
        except urllib.error.HTTPError as error:
            raw_error = error.read()
            try:
                return error.code, json.loads(raw_error.decode("utf-8"))
            except json.JSONDecodeError:
                return error.code, {"error": raw_error.decode("utf-8", "replace")}


@pytest.fixture
def api(tmp_path: Path) -> ApiClient:
    """Démarre un serveur réel sur DB isolée, arrêté en fin de test."""
    server = build_server(db_path=tmp_path / "api.db", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield ApiClient(f"http://127.0.0.1:{server.server_port}")
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


class TestRestHealth:
    """Tests de santé et routes inconnues."""

    def test_health(self, api: ApiClient) -> None:
        """GET /api/health doit répondre 200."""
        status, body = api.request("GET", "/api/health")

        assert status == 200
        assert body == {"status": "ok"}

    def test_unknown_route(self, api: ApiClient) -> None:
        """Une route inconnue doit répondre 404 JSON."""
        status, body = api.request("GET", "/api/nope")

        assert status == 404
        assert isinstance(body, dict)
        assert "error" in body


class TestRestFolders:
    """Tests REST des dossiers."""

    def test_create_and_list_folders(self, api: ApiClient) -> None:
        """POST puis GET /api/folders."""
        status, created = api.request("POST", "/api/folders", {"name": "docs"})
        assert status == 201
        assert isinstance(created, dict)
        assert created["name"] == "docs"

        status, folders = api.request("GET", "/api/folders")
        assert status == 200
        assert isinstance(folders, list)
        assert [folder["name"] for folder in folders] == ["docs"]

    def test_create_invalid_name_returns_400(self, api: ApiClient) -> None:
        """Un nom invalide doit répondre 400."""
        status, body = api.request("POST", "/api/folders", {"name": "mau/vais"})

        assert status == 400
        assert isinstance(body, dict)

    def test_create_duplicate_returns_409(self, api: ApiClient) -> None:
        """Un doublon doit répondre 409."""
        api.request("POST", "/api/folders", {"name": "docs"})

        status, _ = api.request("POST", "/api/folders", {"name": "docs"})

        assert status == 409


class TestRestFiles:
    """Tests REST des fichiers (upload/download)."""

    def test_upload_list_download_roundtrip(self, api: ApiClient) -> None:
        """POST /api/files, GET /api/files, GET content : roundtrip complet."""
        content = base64.b64encode(b"contenu-fichier").decode("ascii")
        status, created = api.request(
            "POST", "/api/files", {"name": "a.bin", "content_base64": content}
        )
        assert status == 201
        assert isinstance(created, dict)
        assert created["size_bytes"] == len(b"contenu-fichier")
        file_id = created["id"]
        assert isinstance(file_id, str)

        status, files = api.request("GET", "/api/files")
        assert status == 200
        assert isinstance(files, list)
        assert len(files) == 1

        status, data = api.request("GET", f"/api/files/{file_id}/content")
        assert status == 200
        assert data == b"contenu-fichier"

    def test_download_unknown_returns_404(self, api: ApiClient) -> None:
        """Télécharger un ID inconnu doit répondre 404."""
        status, _ = api.request("GET", "/api/files/inconnu/content")

        assert status == 404

    def test_invalid_base64_returns_400(self, api: ApiClient) -> None:
        """Un contenu base64 invalide doit répondre 400."""
        status, _ = api.request("POST", "/api/files", {"name": "a.bin", "content_base64": "!!!"})

        assert status == 400


class TestRestPermissions:
    """La REST applique les mêmes permissions que la CLI."""

    def test_stranger_cannot_download(self, api: ApiClient) -> None:
        """Sans partage, un autre utilisateur reçoit 403."""
        _, created = api.request(
            "POST", "/api/files", {"name": "a.txt", "content_base64": ""}, user="alice"
        )
        assert isinstance(created, dict)
        file_id = created["id"]

        status, body = api.request("GET", f"/api/files/{file_id}/content", user="mallory")

        assert status == 403
        assert isinstance(body, dict)

    def test_user_isolation_in_lists(self, api: ApiClient) -> None:
        """Chaque utilisateur ne liste que ce qu'il possède."""
        api.request("POST", "/api/folders", {"name": "prive"}, user="alice")

        status, folders = api.request("GET", "/api/folders", user="mallory")

        assert status == 200
        assert folders == []


class TestRestNodeOps:
    """Tests REST rename/move/trash/restore/rm/share."""

    def test_rename_folder(self, api: ApiClient) -> None:
        """PATCH /api/folders/{id} renomme."""
        _, created = api.request("POST", "/api/folders", {"name": "ancien"})
        assert isinstance(created, dict)

        status, renamed = api.request("PATCH", f"/api/folders/{created['id']}", {"name": "nouveau"})

        assert status == 200
        assert isinstance(renamed, dict)
        assert renamed["name"] == "nouveau"

    def test_rename_wrong_kind_returns_404(self, api: ApiClient) -> None:
        """Un dossier sous /api/files/{id} doit répondre 404."""
        _, created = api.request("POST", "/api/folders", {"name": "docs"})
        assert isinstance(created, dict)

        status, _ = api.request("PATCH", f"/api/files/{created['id']}", {"name": "x"})

        assert status == 404

    def test_move_file(self, api: ApiClient) -> None:
        """POST /api/files/{id}/move déplace."""
        _, parent = api.request("POST", "/api/folders", {"name": "parent"})
        _, created = api.request("POST", "/api/files", {"name": "a.txt", "content_base64": ""})
        assert isinstance(parent, dict) and isinstance(created, dict)

        status, moved = api.request(
            "POST", f"/api/files/{created['id']}/move", {"parent_id": parent["id"]}
        )

        assert status == 200
        assert isinstance(moved, dict)
        assert moved["parent_id"] == parent["id"]

    def test_trash_restore_rm_folder(self, api: ApiClient) -> None:
        """Cycle trash/restore/rm via REST."""
        _, created = api.request("POST", "/api/folders", {"name": "ephemere"})
        assert isinstance(created, dict)
        folder_id = created["id"]

        status, _ = api.request("POST", f"/api/folders/{folder_id}/trash", {})
        assert status == 200
        status, folders = api.request("GET", "/api/folders")
        assert folders == []

        status, _ = api.request("POST", f"/api/folders/{folder_id}/restore", {})
        assert status == 200
        status, folders = api.request("GET", "/api/folders")
        assert isinstance(folders, list) and len(folders) == 1

        status, deleted = api.request("DELETE", f"/api/folders/{folder_id}")
        assert status == 200
        assert deleted == {"deleted": folder_id}

    def test_share_unshare_file(self, api: ApiClient) -> None:
        """Partage puis retrait via REST, effet visible sur le bénéficiaire."""
        _, created = api.request(
            "POST", "/api/files", {"name": "a.txt", "content_base64": ""}, user="alice"
        )
        assert isinstance(created, dict)
        file_id = created["id"]

        status, _ = api.request(
            "POST",
            f"/api/files/{file_id}/share",
            {"user": "bob", "role": "reader"},
            user="alice",
        )
        assert status == 200
        status, files = api.request("GET", "/api/files", user="bob")
        assert isinstance(files, list) and len(files) == 1

        status, _ = api.request(
            "POST", f"/api/files/{file_id}/unshare", {"user": "bob"}, user="alice"
        )
        assert status == 200
        status, files = api.request("GET", "/api/files", user="bob")
        assert files == []

    def test_share_invalid_role_returns_400(self, api: ApiClient) -> None:
        """Un rôle inconnu doit répondre 400."""
        _, created = api.request("POST", "/api/folders", {"name": "docs"})
        assert isinstance(created, dict)

        status, _ = api.request(
            "POST", f"/api/folders/{created['id']}/share", {"user": "bob", "role": "admin"}
        )

        assert status == 400


class TestWebPage:
    """La racine sert la GUI."""

    def test_root_serves_html(self, api: ApiClient) -> None:
        """GET / doit retourner la page Mini-Drive en HTML."""
        import urllib.request

        with urllib.request.urlopen(api._base_url + "/") as response:
            assert response.status == 200
            assert "text/html" in response.headers.get("Content-Type", "")
            assert "Mini-Drive" in response.read().decode("utf-8")
