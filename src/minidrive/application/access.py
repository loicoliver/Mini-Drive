"""Contrôle d'accès : qui peut faire quoi sur un nœud (pur, testable sans I/O).

Règles :
- le propriétaire peut tout faire ;
- un partage "editor" autorise lecture + écriture ;
- un partage "reader" autorise la lecture seule ;
- sans partage, tout est refusé (PermissionDeniedError).
"""

from minidrive.application.sharing import EDITOR, READER
from minidrive.domain.errors import PermissionDeniedError


def require_read(owner_id: str, role: str | None, user_id: str, node_id: str) -> None:
    """Exige un droit de lecture (propriétaire, reader ou editor).

    Args:
        owner_id: Propriétaire du nœud
        role: Rôle partagé de l'utilisateur (None si aucun)
        user_id: Utilisateur agissant
        node_id: Identifiant du nœud (message d'erreur)

    Raises:
        PermissionDeniedError: Si l'utilisateur ne peut pas lire
    """
    if user_id == owner_id or role in (READER, EDITOR):
        return
    raise PermissionDeniedError(user_id, node_id)


def require_write(owner_id: str, role: str | None, user_id: str, node_id: str) -> None:
    """Exige un droit d'écriture (propriétaire ou editor).

    Args:
        owner_id: Propriétaire du nœud
        role: Rôle partagé de l'utilisateur (None si aucun)
        user_id: Utilisateur agissant
        node_id: Identifiant du nœud (message d'erreur)

    Raises:
        PermissionDeniedError: Si l'utilisateur ne peut pas écrire
    """
    if user_id == owner_id or role == EDITOR:
        return
    raise PermissionDeniedError(user_id, node_id)
