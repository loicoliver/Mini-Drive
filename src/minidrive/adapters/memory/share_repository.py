"""Implémentation en mémoire du ShareRepository (pattern Adapter)."""

from minidrive.application.ports import ShareRepository
from minidrive.domain.entities import Share


class InMemoryShareRepository(ShareRepository):
    """Partages en mémoire pour les tests (clé : type + nœud + utilisateur)."""

    def __init__(self) -> None:
        """Initialise le stockage en mémoire."""
        self._shares: dict[tuple[str, str, str], Share] = {}

    @staticmethod
    def _key(node_type: str, node_id: str, user_id: str) -> tuple[str, str, str]:
        """Clé unique d'un partage."""
        return (node_type, node_id, user_id)

    def grant(self, share: Share) -> None:
        """Accorde (ou met à jour) un partage (upsert)."""
        self._shares[self._key(share.node_type, share.node_id, share.user_id)] = share

    def revoke(self, node_type: str, node_id: str, user_id: str) -> None:
        """Retire un partage (aucune erreur si absent)."""
        self._shares.pop(self._key(node_type, node_id, user_id), None)

    def role_for(self, node_type: str, node_id: str, user_id: str) -> str | None:
        """Retourne le rôle accordé, ou None si aucun."""
        share = self._shares.get(self._key(node_type, node_id, user_id))
        return share.role if share is not None else None

    def delete_for_node(self, node_type: str, node_id: str) -> None:
        """Supprime tous les partages d'un nœud (purge)."""
        doomed = [key for key in self._shares if key[0] == node_type and key[1] == node_id]
        for key in doomed:
            del self._shares[key]
