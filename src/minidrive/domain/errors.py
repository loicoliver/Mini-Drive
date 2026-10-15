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


class FolderAlreadyExistsError(DomainError):
    """Un dossier avec ce nom existe déjà."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Le dossier '{name}' existe déjà")
