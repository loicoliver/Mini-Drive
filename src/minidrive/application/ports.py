"""Ports (interfaces) : contrats abstraits que les adapteurs doivent implémenter."""

from abc import ABC, abstractmethod

from minidrive.domain.entities import Folder


class FolderRepository(ABC):
    """Port pour la persistance des dossiers (pattern Repository)."""

    @abstractmethod
    def add(self, folder: Folder) -> None:
        """Ajoute un dossier au repository.

        Args:
            folder: Le dossier à persister
        """
        pass

    @abstractmethod
    def get(self, folder_id: str) -> Folder | None:
        """Récupère un dossier par son identifiant.

        Args:
            folder_id: Identifiant unique du dossier

        Returns:
            Le dossier trouvé ou None
        """
        pass

    @abstractmethod
    def exists_with_name(self, name: str, parent_id: str | None) -> bool:
        """Vérifie si un dossier avec ce nom existe déjà dans le même parent.

        Args:
            name: Nom du dossier à vérifier
            parent_id: Identifiant du parent (None pour la racine)

        Returns:
            True si un dossier avec ce nom existe déjà
        """
        pass

    @abstractmethod
    def list_all(self) -> list[Folder]:
        """Liste tous les dossiers, triés par nom.

        Returns:
            Tous les dossiers persistés, par nom croissant
        """
        pass


class IdGenerator(ABC):
    """Port pour la génération d'identifiants uniques (pattern Factory)."""

    @abstractmethod
    def generate(self) -> str:
        """Génère un nouvel identifiant unique.

        Returns:
            Un identifiant unique sous forme de chaîne
        """
        pass
