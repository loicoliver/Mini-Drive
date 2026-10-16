"""Entités du domain : objets avec identité et cycle de vie."""

from dataclasses import dataclass

from minidrive.domain.value_objects import FileName, FileSize


@dataclass
class Folder:
    """Dossier avec identité unique."""

    id: str
    name: FileName
    parent_id: str | None
    trashed: bool = False

    @staticmethod
    def create(
        id: str, name: FileName, parent_id: str | None = None, trashed: bool = False
    ) -> "Folder":
        """Factory method pour créer un dossier valide.

        Args:
            id: Identifiant unique du dossier
            name: Nom validé du dossier
            parent_id: Identifiant du dossier parent (None pour la racine)
            trashed: True si le dossier est dans la corbeille

        Returns:
            Une nouvelle instance de Folder
        """
        return Folder(id=id, name=name, parent_id=parent_id, trashed=trashed)


@dataclass
class File:
    """Fichier avec identité unique et taille connue."""

    id: str
    name: FileName
    parent_id: str | None
    size: FileSize
    trashed: bool = False

    @staticmethod
    def create(
        id: str,
        name: FileName,
        size: FileSize,
        parent_id: str | None = None,
        trashed: bool = False,
    ) -> "File":
        """Factory method pour créer un fichier valide.

        Args:
            id: Identifiant unique du fichier
            name: Nom validé du fichier
            size: Taille validée du fichier
            parent_id: Identifiant du dossier parent (None pour la racine)
            trashed: True si le fichier est dans la corbeille

        Returns:
            Une nouvelle instance de File
        """
        return File(id=id, name=name, parent_id=parent_id, size=size, trashed=trashed)
