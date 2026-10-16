"""Politiques de quota (pattern Strategy pour démontrer le principe O : Open/Closed)."""

from abc import ABC, abstractmethod


class QuotaPolicy(ABC):
    """Interface pour les différentes politiques de quota (pattern Strategy).

    Permet d'ajouter de nouvelles politiques sans modifier le code existant.
    Démontre le principe O (Open/Closed) : ouvert à l'extension, fermé à la modification.
    """

    @abstractmethod
    def can_upload(self, user_id: str, file_size_bytes: int) -> bool:
        """Vérifie si l'utilisateur peut uploader un fichier de cette taille.

        Args:
            user_id: Identifiant de l'utilisateur
            file_size_bytes: Taille du fichier en octets

        Returns:
            True si l'upload est autorisé
        """
        pass

    @abstractmethod
    def get_remaining_quota(self, user_id: str) -> int:
        """Retourne l'espace disponible pour l'utilisateur.

        Args:
            user_id: Identifiant de l'utilisateur

        Returns:
            Espace disponible en octets (-1 si illimité)
        """
        pass

    @abstractmethod
    def record_upload(self, user_id: str, file_size_bytes: int) -> None:
        """Enregistre un upload pour décompter le quota de l'utilisateur.

        Args:
            user_id: Identifiant de l'utilisateur
            file_size_bytes: Taille du fichier uploadé en octets
        """
        pass


class FixedQuotaPolicy(QuotaPolicy):
    """Politique de quota fixe : chaque utilisateur a un quota maximum.

    Première implémentation du Strategy. Ajouter une nouvelle politique
    (ex: QuotaPremiumPolicy) ne nécessite aucune modification de cette classe.
    """

    def __init__(self, quota_bytes: int) -> None:
        """Initialise la politique avec un quota fixe.

        Args:
            quota_bytes: Quota maximum en octets pour chaque utilisateur
        """
        self._quota_bytes = quota_bytes
        self._used_space: dict[str, int] = {}

    def can_upload(self, user_id: str, file_size_bytes: int) -> bool:
        """Vérifie si l'utilisateur peut uploader."""
        used = self._used_space.get(user_id, 0)
        return used + file_size_bytes <= self._quota_bytes

    def get_remaining_quota(self, user_id: str) -> int:
        """Retourne l'espace disponible."""
        used = self._used_space.get(user_id, 0)
        return self._quota_bytes - used

    def record_upload(self, user_id: str, file_size_bytes: int) -> None:
        """Enregistre l'utilisation d'espace après un upload réussi."""
        current = self._used_space.get(user_id, 0)
        self._used_space[user_id] = current + file_size_bytes


class UnlimitedQuotaPolicy(QuotaPolicy):
    """Politique de quota illimité : aucune restriction.

    Deuxième implémentation du Strategy. Démontre qu'on peut ajouter
    des comportements différents sans modifier FixedQuotaPolicy.
    """

    def can_upload(self, user_id: str, file_size_bytes: int) -> bool:
        """Autorise toujours l'upload."""
        return True

    def get_remaining_quota(self, user_id: str) -> int:
        """Retourne -1 pour indiquer un quota illimité."""
        return -1

    def record_upload(self, user_id: str, file_size_bytes: int) -> None:
        """Aucun décompte nécessaire : le quota est illimité."""
        pass
