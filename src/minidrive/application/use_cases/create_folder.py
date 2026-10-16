"""Use case pour créer un dossier (pattern Use Case / Command)."""

from minidrive.application.ports import FolderRepository, IdGenerator
from minidrive.application.users import DEFAULT_USER_ID
from minidrive.domain.entities import Folder
from minidrive.domain.errors import FolderAlreadyExistsError
from minidrive.domain.value_objects import FileName


class CreateFolder:
    """Use case : créer un nouveau dossier.

    Démontre le principe S (Single Responsibility) : une seule action métier.
    Démontre le principe D (Dependency Inversion) : dépend des abstractions (ports).
    """

    def __init__(self, folder_repository: FolderRepository, id_generator: IdGenerator) -> None:
        """Injection de dépendances par constructeur.

        Args:
            folder_repository: Port pour la persistance des dossiers
            id_generator: Port pour la génération d'identifiants
        """
        self._folder_repository = folder_repository
        self._id_generator = id_generator

    def execute(
        self, name: str, parent_id: str | None = None, owner_id: str = DEFAULT_USER_ID
    ) -> Folder:
        """Crée un nouveau dossier.

        Args:
            name: Nom du dossier (sera validé)
            parent_id: Identifiant du parent (None pour la racine)
            owner_id: Identifiant du propriétaire (créateur par défaut)

        Returns:
            Le dossier créé

        Raises:
            InvalidFileNameError: Si le nom est invalide
            FolderAlreadyExistsError: Si un dossier avec ce nom existe déjà
        """
        # Validation du nom (délégué au value object)
        folder_name = FileName(name)

        # Vérification de l'unicité
        if self._folder_repository.exists_with_name(name, parent_id):
            raise FolderAlreadyExistsError(name)

        # Création du dossier (factory method, propriétaire = créateur)
        folder_id = self._id_generator.generate()
        folder = Folder.create(
            id=folder_id, name=folder_name, parent_id=parent_id, owner_id=owner_id
        )

        # Persistance
        self._folder_repository.add(folder)

        return folder
