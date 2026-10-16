"""Implémentation SQLite du FileRepository (pattern Adapter)."""

from pathlib import Path

from minidrive.adapters.sqlite._database import connect, ensure_column
from minidrive.application.ports import FileRepository
from minidrive.domain.entities import File
from minidrive.domain.value_objects import FileName, FileSize

_SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    parent_id TEXT,
    size_bytes INTEGER NOT NULL,
    trashed INTEGER NOT NULL DEFAULT 0,
    owner_id TEXT NOT NULL DEFAULT 'local'
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_files_name_parent
    ON files (name, parent_id);
"""
# Même note que folders : les NULL sont distincts dans l'index UNIQUE,
# l'unicité métier reste garantie par le use case via exists_with_name.


class SqliteFileRepository(FileRepository):
    """Repository persistant des métadonnées de fichiers (même .db que les dossiers)."""

    def __init__(self, db_path: Path | str) -> None:
        """Initialise le repository sur un fichier SQLite (créé si absent).

        Args:
            db_path: Chemin du fichier .db (dossiers parents créés si besoin)
        """
        self._db_path = Path(db_path)
        with connect(self._db_path) as connection:
            connection.executescript(_SCHEMA)
        # Migrations des .db créés avant ces colonnes (colonnes absentes)
        ensure_column(self._db_path, "files", "trashed", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(self._db_path, "files", "owner_id", "TEXT NOT NULL DEFAULT 'local'")

    def add(self, file: File) -> None:
        """Ajoute un fichier au repository."""
        with connect(self._db_path) as connection:
            connection.execute(
                "INSERT INTO files (id, name, parent_id, size_bytes, trashed, owner_id)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    file.id,
                    file.name.value,
                    file.parent_id,
                    file.size.value,
                    int(file.trashed),
                    file.owner_id,
                ),
            )

    def get(self, file_id: str) -> File | None:
        """Récupère un fichier par son identifiant (corbeille incluse)."""
        with connect(self._db_path) as connection:
            row = connection.execute(
                "SELECT id, name, parent_id, size_bytes, trashed, owner_id FROM files WHERE id = ?",
                (file_id,),
            ).fetchone()
        if row is None:
            return None
        found_id: str = row[0]
        found_name: str = row[1]
        found_parent_id: str | None = row[2]
        found_size: int = row[3]
        found_trashed: bool = bool(row[4])
        found_owner: str = row[5]
        return File.create(
            id=found_id,
            name=FileName(found_name),
            size=FileSize(found_size),
            parent_id=found_parent_id,
            trashed=found_trashed,
            owner_id=found_owner,
        )

    def exists_with_name(self, name: str, parent_id: str | None) -> bool:
        """Vérifie si un fichier NON corbeillé avec ce nom existe dans le parent."""
        with connect(self._db_path) as connection:
            row = connection.execute(
                "SELECT 1 FROM files WHERE name = ? AND parent_id IS ? AND trashed = 0 LIMIT 1",
                (name, parent_id),
            ).fetchone()
        return row is not None

    def list_all(self, include_trashed: bool = False) -> list[File]:
        """Liste les fichiers NON corbeillés, triés par nom."""
        query = "SELECT id, name, parent_id, size_bytes, trashed, owner_id FROM files"
        if not include_trashed:
            query += " WHERE trashed = 0"
        query += " ORDER BY name"
        with connect(self._db_path) as connection:
            rows = connection.execute(query).fetchall()
        files: list[File] = []
        for row in rows:
            file_id: str = row[0]
            file_name: str = row[1]
            file_parent_id: str | None = row[2]
            file_size: int = row[3]
            file_trashed: bool = bool(row[4])
            file_owner: str = row[5]
            files.append(
                File.create(
                    id=file_id,
                    name=FileName(file_name),
                    size=FileSize(file_size),
                    parent_id=file_parent_id,
                    trashed=file_trashed,
                    owner_id=file_owner,
                )
            )
        return files

    def save(self, file: File) -> None:
        """Crée ou remplace un fichier (upsert par identifiant)."""
        with connect(self._db_path) as connection:
            connection.execute(
                "INSERT OR REPLACE INTO files"
                " (id, name, parent_id, size_bytes, trashed, owner_id)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    file.id,
                    file.name.value,
                    file.parent_id,
                    file.size.value,
                    int(file.trashed),
                    file.owner_id,
                ),
            )

    def delete(self, file_id: str) -> None:
        """Supprime définitivement un fichier (aucune erreur si absent)."""
        with connect(self._db_path) as connection:
            connection.execute("DELETE FROM files WHERE id = ?", (file_id,))
