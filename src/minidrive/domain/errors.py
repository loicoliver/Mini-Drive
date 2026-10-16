"""Exceptions métier du domain : aucune dépendance externe."""


class DomainError(Exception):
    """Erreur métier de base."""

    pass


class InvalidFileNameError(DomainError):
    """Nom de fichier invalide selon les règles métier."""

    def __init__(self, name: str, reason: str) -> None:
        self.name = name
        self.reason = reason
        super().__init__(f"Nom de fichier invalide '{name}': {reason}")


class InvalidFileSizeError(DomainError):
    """Taille de fichier invalide selon les règles métier."""

    def __init__(self, size_bytes: int, reason: str) -> None:
        self.size_bytes = size_bytes
        self.reason = reason
        super().__init__(f"Taille de fichier invalide ({size_bytes} octets): {reason}")


class FolderAlreadyExistsError(DomainError):
    """Un dossier avec ce nom existe déjà."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Le dossier '{name}' existe déjà")


class FileAlreadyExistsError(DomainError):
    """Un fichier avec ce nom existe déjà."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Le fichier '{name}' existe déjà")


class QuotaExceededError(DomainError):
    """L'upload dépasse le quota disponible de l'utilisateur."""

    def __init__(self, user_id: str, size_bytes: int) -> None:
        self.user_id = user_id
        self.size_bytes = size_bytes
        super().__init__(f"Quota dépassé pour '{user_id}': {size_bytes} octets demandés")


class UnknownFileError(DomainError):
    """Aucun fichier connu sous cet identifiant (métadonnées ou contenu absent)."""

    def __init__(self, file_id: str) -> None:
        self.file_id = file_id
        super().__init__(f"Fichier inconnu : '{file_id}'")


class UnknownFolderError(DomainError):
    """Aucun dossier connu sous cet identifiant."""

    def __init__(self, folder_id: str) -> None:
        self.folder_id = folder_id
        super().__init__(f"Dossier inconnu : '{folder_id}'")


class InTrashError(DomainError):
    """Opération impossible : l'élément est dans la corbeille (restaurer d'abord)."""

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        super().__init__(f"Opération impossible : '{node_id}' est dans la corbeille")


class InvalidShareError(DomainError):
    """Partage invalide (rôle inconnu ou opération interdite)."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Partage invalide : {reason}")


class PermissionDeniedError(DomainError):
    """L'utilisateur n'a pas la permission pour cette opération."""

    def __init__(self, user_id: str, node_id: str) -> None:
        self.user_id = user_id
        self.node_id = node_id
        super().__init__(f"Permission refusée pour '{user_id}' sur '{node_id}'")


class InvalidMoveError(DomainError):
    """Déplacement impossible (sur soi-même ou dans un descendant)."""

    def __init__(self, node_id: str, reason: str) -> None:
        self.node_id = node_id
        self.reason = reason
        super().__init__(f"Déplacement impossible pour '{node_id}': {reason}")
