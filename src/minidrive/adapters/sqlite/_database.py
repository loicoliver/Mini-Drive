"""Helper SQLite partagé : connexion courte avec transaction et fermeture garanties."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def connect(db_path: Path | str) -> Iterator[sqlite3.Connection]:
    """Ouvre une connexion courte sur un fichier SQLite.

    Crée les dossiers parents si besoin. Le `with` interne valide la
    transaction, le `finally` ferme la connexion (pas de verrou résiduel
    sur Windows, pas de ResourceWarning).
    """
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db_file))
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def ensure_column(db_path: Path | str, table: str, column: str, definition: str) -> None:
    """Ajoute une colonne si absente (migration idempotente des .db existants).

    Args:
        db_path: Chemin du fichier SQLite
        table: Table à migrer (constante interne, jamais saisie utilisateur)
        column: Colonne à ajouter si absente
        definition: Définition SQL de la colonne (ex: "INTEGER NOT NULL DEFAULT 0")
    """
    with connect(db_path) as connection:
        existing = [row[1] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()]
        if column not in existing:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
