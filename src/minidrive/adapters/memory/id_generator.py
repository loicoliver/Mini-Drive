"""Implémentation de la génération d'identifiants avec UUID (pattern Adapter)."""

import uuid

from minidrive.application.ports import IdGenerator


class UuidIdGenerator(IdGenerator):
    """Générateur d'identifiants basé sur UUID4.

    Démontre le principe L (Liskov) : peut remplacer IdGenerator.
    Démontre le principe D (Dependency Inversion) : le domaine ne dépend pas de uuid.
    """

    def generate(self) -> str:
        """Génère un nouvel identifiant UUID4."""
        return str(uuid.uuid4())
