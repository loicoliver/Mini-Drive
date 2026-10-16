"""Implémentation SQLite du ShareRepository (pattern Adapter)."""

from pathlib import Path

from minidrive.adapters.sqlite._database import connect
from minidrive.application.ports import ShareRepository
from minidrive.domain.entities import Share

_SCHEMA = """
CREATE TABLE IF NOT EXISTS shares (
    node_type TEXT NOT NULL,
    node_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    PRIMARY KEY (node_type, node_id, user_id)
);
"""


class SqliteShareRepository(ShareRepository):
    """Partages persistés dans le même .db (table shares)."""

    def __init__(self, db_path: Path | str) -> None:
        """Initialise le repository sur un fichier SQLite (créé si absent).

        Args:
            db_path: Chemin du fichier .db (dossiers parents créés si besoin)
        """
        self._db_path = Path(db_path)
        with connect(self._db_path) as connection:
            connection.executescript(_SCHEMA)

    def grant(self, share: Share) -> None:
        """Accorde (ou met à jour) un partage (upsert)."""
        with connect(self._db_path) as connection:
            connection.execute(
                "INSERT OR REPLACE INTO shares (node_type, node_id, user_id, role)"
                " VALUES (?, ?, ?, ?)",
                (share.node_type, share.node_id, share.user_id, share.role),
            )

    def revoke(self, node_type: str, node_id: str, user_id: str) -> None:
        """Retire un partage (aucune erreur si absent)."""
        with connect(self._db_path) as connection:
            connection.execute(
                "DELETE FROM shares WHERE node_type = ? AND node_id = ? AND user_id = ?",
                (node_type, node_id, user_id),
            )

    def role_for(self, node_type: str, node_id: str, user_id: str) -> str | None:
        """Retourne le rôle accordé, ou None si aucun."""
        with connect(self._db_path) as connection:
            row = connection.execute(
                "SELECT role FROM shares WHERE node_type = ? AND node_id = ? AND user_id = ?",
                (node_type, node_id, user_id),
            ).fetchone()
        if row is None:
            return None
        role: str = row[0]
        return role

    def delete_for_node(self, node_type: str, node_id: str) -> None:
        """Supprime tous les partages d'un nœud (purge)."""
        with connect(self._db_path) as connection:
            connection.execute(
                "DELETE FROM shares WHERE node_type = ? AND node_id = ?",
                (node_type, node_id),
            )
