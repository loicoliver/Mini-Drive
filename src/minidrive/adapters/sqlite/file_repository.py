"""Implémentation SQLite du FileRepository (pattern Adapter)."""

from pathlib import Path

from minidrive.adapters.sqlite._database import connect
from minidrive.application.ports import FileRepository
from minidrive.domain.entities import File
from minidrive.domain.value_objects import FileName, FileSize

_SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    parent_id TEXT,
    size_bytes INTEGER NOT NULL
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

    def add(self, file: File) -> None:
        """Ajoute un fichier au repository."""
        with connect(self._db_path) as connection:
            connection.execute(
                "INSERT INTO files (id, name, parent_id, size_bytes) VALUES (?, ?, ?, ?)",
                (file.id, file.name.value, file.parent_id, file.size.value),
            )

    def get(self, file_id: str) -> File | None:
        """Récupère un fichier par son identifiant."""
        with connect(self._db_path) as connection:
            row = connection.execute(
                "SELECT id, name, parent_id, size_bytes FROM files WHERE id = ?",
                (file_id,),
            ).fetchone()
        if row is None:
            return None
        found_id: str = row[0]
        found_name: str = row[1]
        found_parent_id: str | None = row[2]
        found_size: int = row[3]
        return File.create(
            id=found_id,
            name=FileName(found_name),
            size=FileSize(found_size),
            parent_id=found_parent_id,
        )

    def exists_with_name(self, name: str, parent_id: str | None) -> bool:
        """Vérifie si un fichier avec ce nom existe déjà dans le même parent."""
        with connect(self._db_path) as connection:
            row = connection.execute(
                "SELECT 1 FROM files WHERE name = ? AND parent_id IS ? LIMIT 1",
                (name, parent_id),
            ).fetchone()
        return row is not None

    def list_all(self) -> list[File]:
        """Liste tous les fichiers, triés par nom."""
        with connect(self._db_path) as connection:
            rows = connection.execute(
                "SELECT id, name, parent_id, size_bytes FROM files ORDER BY name"
            ).fetchall()
        files: list[File] = []
        for row in rows:
            file_id: str = row[0]
            file_name: str = row[1]
            file_parent_id: str | None = row[2]
            file_size: int = row[3]
            files.append(
                File.create(
                    id=file_id,
                    name=FileName(file_name),
                    size=FileSize(file_size),
                    parent_id=file_parent_id,
                )
            )
        return files
