"""Ports (interfaces) : contrats abstraits que les adapteurs doivent implémenter."""

from abc import ABC, abstractmethod

from minidrive.domain.entities import File, Folder, Share


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
    def list_all(self, include_trashed: bool = False) -> list[Folder]:
        """Liste les dossiers NON corbeillés, triés par nom.

        Args:
            include_trashed: True pour inclure aussi les corbeillés
                (traversées trash/restore/purge, jamais l'affichage)

        Returns:
            Les dossiers persistés, par nom croissant
        """
        pass

    @abstractmethod
    def save(self, folder: Folder) -> None:
        """Crée ou remplace un dossier (upsert par identifiant).

        Args:
            folder: Le dossier à persister (remplace celui de même ID)
        """
        pass

    @abstractmethod
    def delete(self, folder_id: str) -> None:
        """Supprime définitivement un dossier (aucune erreur si absent).

        Args:
            folder_id: Identifiant unique du dossier
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


class FileRepository(ABC):
    """Port pour la persistance des métadonnées de fichiers (pattern Repository)."""

    @abstractmethod
    def add(self, file: File) -> None:
        """Ajoute un fichier au repository.

        Args:
            file: Le fichier à persister
        """
        pass

    @abstractmethod
    def get(self, file_id: str) -> File | None:
        """Récupère un fichier par son identifiant.

        Args:
            file_id: Identifiant unique du fichier

        Returns:
            Le fichier trouvé ou None
        """
        pass

    @abstractmethod
    def exists_with_name(self, name: str, parent_id: str | None) -> bool:
        """Vérifie si un fichier avec ce nom existe déjà dans le même parent.

        Args:
            name: Nom du fichier à vérifier
            parent_id: Identifiant du parent (None pour la racine)

        Returns:
            True si un fichier avec ce nom existe déjà
        """
        pass

    @abstractmethod
    def list_all(self, include_trashed: bool = False) -> list[File]:
        """Liste les fichiers NON corbeillés, triés par nom.

        Args:
            include_trashed: True pour inclure aussi les corbeillés
                (traversées trash/restore/purge, jamais l'affichage)

        Returns:
            Les fichiers persistés, par nom croissant
        """
        pass

    @abstractmethod
    def save(self, file: File) -> None:
        """Crée ou remplace un fichier (upsert par identifiant).

        Args:
            file: Le fichier à persister (remplace celui de même ID)
        """
        pass

    @abstractmethod
    def delete(self, file_id: str) -> None:
        """Supprime définitivement un fichier (aucune erreur si absent).

        Args:
            file_id: Identifiant unique du fichier
        """
        pass


class BlobStorage(ABC):
    """Port pour le stockage du contenu binaire des fichiers."""

    @abstractmethod
    def write(self, file_id: str, data: bytes) -> None:
        """Stocke le contenu d'un fichier.

        Args:
            file_id: Identifiant unique du fichier
            data: Contenu binaire à stocker
        """
        pass

    @abstractmethod
    def read(self, file_id: str) -> bytes | None:
        """Lit le contenu d'un fichier.

        Args:
            file_id: Identifiant unique du fichier

        Returns:
            Le contenu binaire, ou None si absent
        """
        pass

    @abstractmethod
    def delete(self, file_id: str) -> None:
        """Supprime le contenu d'un fichier (aucune erreur si absent).

        Args:
            file_id: Identifiant unique du fichier
        """
        pass


class ShareRepository(ABC):
    """Port pour la persistance des partages (qui peut voir/éditer quoi)."""

    @abstractmethod
    def grant(self, share: Share) -> None:
        """Accorde (ou met à jour) un partage (upsert).

        Args:
            share: Le partage à persister
        """
        pass

    @abstractmethod
    def revoke(self, node_type: str, node_id: str, user_id: str) -> None:
        """Retire un partage (aucune erreur si absent).

        Args:
            node_type: "folder" ou "file"
            node_id: Identifiant du dossier ou fichier
            user_id: Identifiant de l'utilisateur
        """
        pass

    @abstractmethod
    def role_for(self, node_type: str, node_id: str, user_id: str) -> str | None:
        """Retourne le rôle accordé ("reader"/"editor"), ou None si aucun.

        Args:
            node_type: "folder" ou "file"
            node_id: Identifiant du dossier ou fichier
            user_id: Identifiant de l'utilisateur

        Returns:
            Le rôle, ou None
        """
        pass

    @abstractmethod
    def delete_for_node(self, node_type: str, node_id: str) -> None:
        """Supprime tous les partages d'un nœud (purge).

        Args:
            node_type: "folder" ou "file"
            node_id: Identifiant du dossier ou fichier
        """
        pass
