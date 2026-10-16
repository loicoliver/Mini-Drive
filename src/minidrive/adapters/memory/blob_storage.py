"""Implémentation en mémoire du BlobStorage (pattern Adapter)."""

from minidrive.application.ports import BlobStorage


class InMemoryBlobStorage(BlobStorage):
    """Stockage binaire en mémoire pour les tests."""

    def __init__(self) -> None:
        """Initialise le stockage en mémoire."""
        self._blobs: dict[str, bytes] = {}

    def write(self, file_id: str, data: bytes) -> None:
        """Stocke le contenu d'un fichier."""
        self._blobs[file_id] = data

    def read(self, file_id: str) -> bytes | None:
        """Lit le contenu d'un fichier, ou None si absent."""
        return self._blobs.get(file_id)
