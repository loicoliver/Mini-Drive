"""Value objects : objets immuables représentant des concepts métier validés."""

from dataclasses import dataclass

from minidrive.domain.errors import InvalidFileNameError, InvalidFileSizeError


@dataclass(frozen=True)
class FileName:
    """Nom de fichier ou dossier validé selon les règles métier."""

    value: str

    def __post_init__(self) -> None:
        """Valide le nom lors de la création."""
        if not self.value:
            raise InvalidFileNameError(self.value, "le nom ne peut pas être vide")
        if "/" in self.value or "\\" in self.value:
            raise InvalidFileNameError(
                self.value, "le nom ne peut pas contenir de séparateurs de chemin (/ ou \\)"
            )
        if len(self.value) > 255:
            raise InvalidFileNameError(self.value, "le nom ne peut pas dépasser 255 caractères")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class FileSize:
    """Taille d'un fichier en octets, validée selon les règles métier."""

    value: int

    def __post_init__(self) -> None:
        """Valide la taille lors de la création."""
        if self.value < 0:
            raise InvalidFileSizeError(self.value, "la taille ne peut pas être négative")

    def __str__(self) -> str:
        return f"{self.value} octets"
