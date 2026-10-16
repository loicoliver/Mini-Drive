"""Implémentation SQLite du FolderRepository (pattern Adapter).

Persistance locale cross-platform : sqlite3 fait partie de la stdlib,
aucune dépendance externe. Une connexion courte est ouverte puis fermée
par opération (pas de handle persistant, pas de verrou résiduel sur Windows).
"""

from pathlib import Path

from minidrive.adapters.sqlite._database import connect
from minidrive.application.ports import FolderRepository
from minidrive.domain.entities import Folder
from minidrive.domain.value_objects import FileName

_SCHEMA = """
CREATE TABLE IF NOT EXISTS folders (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    parent_id TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_folders_name_parent
    ON folders (name, parent_id);
"""
# Note : en SQLite les NULL sont distincts dans un index UNIQUE, donc
# l'index ci-dessus est une protection best-effort pour les parents non-nuls.
# L'unicité métier (nom + parent, racine incluse) est garantie par le use case
# via exists_with_name avant add.


class SqliteFolderRepository(FolderRepository):
    """Repository persistant basé sur un fichier SQLite.

    Démontre le principe L (Liskov) : substituable à FolderRepository,
    vérifié par les contract tests partagés.
    Démontre le principe O (Open/Closed) : nouvelle implémentation ajoutée
    sans modifier le port ni les use cases.
    """

    def __init__(self, db_path: Path | str) -> None:
        """Initialise le repository sur un fichier SQLite (créé si absent).

        Args:
            db_path: Chemin du fichier .db (dossiers parents créés si besoin)
        """
        self._db_path = Path(db_path)
        with connect(self._db_path) as connection:
            connection.executescript(_SCHEMA)

    def add(self, folder: Folder) -> None:
        """Ajoute un dossier au repository."""
        with connect(self._db_path) as connection:
            connection.execute(
                "INSERT INTO folders (id, name, parent_id) VALUES (?, ?, ?)",
                (folder.id, folder.name.value, folder.parent_id),
            )

    def get(self, folder_id: str) -> Folder | None:
        """Récupère un dossier par son identifiant."""
        with connect(self._db_path) as connection:
            row = connection.execute(
                "SELECT id, name, parent_id FROM folders WHERE id = ?",
                (folder_id,),
            ).fetchone()
        if row is None:
            return None
        found_id: str = row[0]
        found_name: str = row[1]
        found_parent_id: str | None = row[2]
        return Folder.create(id=found_id, name=FileName(found_name), parent_id=found_parent_id)

    def exists_with_name(self, name: str, parent_id: str | None) -> bool:
        """Vérifie si un dossier avec ce nom existe déjà dans le même parent."""
        with connect(self._db_path) as connection:
            row = connection.execute(
                "SELECT 1 FROM folders WHERE name = ? AND parent_id IS ? LIMIT 1",
                (name, parent_id),
            ).fetchone()
        return row is not None

    def list_all(self) -> list[Folder]:
        """Liste tous les dossiers, triés par nom."""
        with connect(self._db_path) as connection:
            rows = connection.execute(
                "SELECT id, name, parent_id FROM folders ORDER BY name"
            ).fetchall()
        folders: list[Folder] = []
        for row in rows:
            folder_id: str = row[0]
            folder_name: str = row[1]
            folder_parent_id: str | None = row[2]
            folders.append(
                Folder.create(id=folder_id, name=FileName(folder_name), parent_id=folder_parent_id)
            )
        return folders
