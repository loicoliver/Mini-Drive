"""Use case pour uploader un fichier (pattern Use Case / Command)."""

from minidrive.application.ports import (
    BlobStorage,
    FileRepository,
    FolderRepository,
    IdGenerator,
)
from minidrive.application.quota_policies import QuotaPolicy
from minidrive.application.users import DEFAULT_USER_ID
from minidrive.domain.entities import File
from minidrive.domain.errors import (
    FileAlreadyExistsError,
    InTrashError,
    QuotaExceededError,
    UnknownFolderError,
)
from minidrive.domain.value_objects import FileName, FileSize


class UploadFile:
    """Use case : uploader un nouveau fichier.

    Le contenu arrive en bytes purs : la lecture du disque est une
    préoccupation d'interface (CLI), pas d'application. Le use case reste
    testable sans aucun fichier sur disque.
    Démontre le principe S (Single Responsibility) : une seule action métier.
    Démontre le principe D (Dependency Inversion) : dépend des abstractions (ports).
    """

    def __init__(
        self,
        file_repository: FileRepository,
        blob_storage: BlobStorage,
        id_generator: IdGenerator,
        quota_policy: QuotaPolicy,
        folder_repository: FolderRepository,
    ) -> None:
        """Injection de dépendances par constructeur.

        Args:
            file_repository: Port pour la persistance des métadonnées
            blob_storage: Port pour le stockage du contenu binaire
            id_generator: Port pour la génération d'identifiants
            quota_policy: Politique de quota applicable (pattern Strategy)
            folder_repository: Port pour vérifier le dossier parent
        """
        self._file_repository = file_repository
        self._blob_storage = blob_storage
        self._id_generator = id_generator
        self._quota_policy = quota_policy
        self._folder_repository = folder_repository

    def execute(
        self,
        name: str,
        data: bytes,
        parent_id: str | None = None,
        user_id: str = DEFAULT_USER_ID,
    ) -> File:
        """Upload un nouveau fichier.

        Args:
            name: Nom du fichier (sera validé)
            data: Contenu binaire du fichier
            parent_id: Identifiant du dossier parent (None pour la racine)
            user_id: Identifiant de l'utilisateur (mono-utilisateur local par défaut)

        Returns:
            Le fichier créé

        Raises:
            InvalidFileNameError: Si le nom est invalide
            UnknownFolderError: Si le dossier parent est inconnu
            InTrashError: Si le dossier parent est corbeillé
            FileAlreadyExistsError: Si un fichier avec ce nom existe déjà
            QuotaExceededError: Si le quota de l'utilisateur est dépassé
        """
        # Validation du nom et de la taille (déléguées aux value objects)
        file_name = FileName(name)
        file_size = FileSize(len(data))

        # Le parent doit exister et ne pas être corbeillé (pas d'orphelins)
        if parent_id is not None:
            parent = self._folder_repository.get(parent_id)
            if parent is None:
                raise UnknownFolderError(parent_id)
            if parent.trashed:
                raise InTrashError(parent_id)

        # Vérification de l'unicité
        if self._file_repository.exists_with_name(name, parent_id):
            raise FileAlreadyExistsError(name)

        # Vérification du quota AVANT tout stockage
        if not self._quota_policy.can_upload(user_id, file_size.value):
            raise QuotaExceededError(user_id, file_size.value)

        # Création du fichier (factory method, propriétaire = uploader)
        file_id = self._id_generator.generate()
        file = File.create(
            id=file_id, name=file_name, size=file_size, parent_id=parent_id, owner_id=user_id
        )

        # Persistance : contenu puis métadonnées, puis décompte du quota
        self._blob_storage.write(file_id, data)
        self._file_repository.add(file)
        self._quota_policy.record_upload(user_id, file_size.value)

        return file
