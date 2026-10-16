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
