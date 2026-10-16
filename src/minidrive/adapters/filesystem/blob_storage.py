"""Implémentation filesystem du BlobStorage (pattern Adapter).

Chaque contenu est stocké dans un fichier nommé d'après l'ID, sous le
dossier racine (pathlib : séparateurs gérés par l'OS).
"""

from pathlib import Path

from minidrive.application.ports import BlobStorage


class FilesystemBlobStorage(BlobStorage):
    """Stockage binaire sur disque, un fichier par ID."""

    def __init__(self, root_dir: Path | str) -> None:
        """Initialise le stockage sur un dossier (créé si absent).

        Args:
            root_dir: Dossier racine des blobs
        """
        self._root_dir = Path(root_dir)
        self._root_dir.mkdir(parents=True, exist_ok=True)

    def _blob_path(self, file_id: str) -> Path:
        """Résout le chemin du blob pour un ID (pas de sous-dossiers)."""
        return self._root_dir / file_id

    def write(self, file_id: str, data: bytes) -> None:
        """Stocke le contenu d'un fichier (écrase si existant)."""
        self._blob_path(file_id).write_bytes(data)

    def read(self, file_id: str) -> bytes | None:
        """Lit le contenu d'un fichier, ou None si absent."""
        blob_path = self._blob_path(file_id)
        if not blob_path.is_file():
            return None
        return blob_path.read_bytes()

    def delete(self, file_id: str) -> None:
        """Supprime le contenu d'un fichier (aucune erreur si absent)."""
        self._blob_path(file_id).unlink(missing_ok=True)
