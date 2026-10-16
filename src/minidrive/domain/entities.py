"""Entités du domain : objets avec identité et cycle de vie."""

from dataclasses import dataclass

from minidrive.domain.value_objects import FileName, FileSize


@dataclass
class Folder:
    """Dossier avec identité unique."""

    id: str
    name: FileName
    parent_id: str | None

    @staticmethod
    def create(id: str, name: FileName, parent_id: str | None = None) -> "Folder":
        """Factory method pour créer un dossier valide.

        Args:
            id: Identifiant unique du dossier
            name: Nom validé du dossier
            parent_id: Identifiant du dossier parent (None pour la racine)

        Returns:
            Une nouvelle instance de Folder
        """
        return Folder(id=id, name=name, parent_id=parent_id)


@dataclass
class File:
    """Fichier avec identité unique et taille connue."""

    id: str
    name: FileName
    parent_id: str | None
    size: FileSize

    @staticmethod
    def create(id: str, name: FileName, size: FileSize, parent_id: str | None = None) -> "File":
        """Factory method pour créer un fichier valide.

        Args:
            id: Identifiant unique du fichier
            name: Nom validé du fichier
            size: Taille validée du fichier
            parent_id: Identifiant du dossier parent (None pour la racine)

        Returns:
            Une nouvelle instance de File
        """
        return File(id=id, name=name, parent_id=parent_id, size=size)
