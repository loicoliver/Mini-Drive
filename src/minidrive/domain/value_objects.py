"""Value objects : objets immuables représentant des concepts métier validés."""

from dataclasses import dataclass

from minidrive.domain.errors import InvalidFileNameError


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
