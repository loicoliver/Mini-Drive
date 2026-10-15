"""Tests des politiques de quota (pattern Strategy)."""

import pytest

from minidrive.application.quota_policies import (
    FixedQuotaPolicy,
    QuotaPolicy,
    UnlimitedQuotaPolicy,
)


class TestFixedQuotaPolicy:
    """Tests de la politique de quota fixe."""

    def test_can_upload_within_quota(self) -> None:
        """L'upload doit être autorisé si dans les limites."""
        policy = FixedQuotaPolicy(quota_bytes=1000)
        assert policy.can_upload("user1", 500) is True

    def test_cannot_upload_exceeding_quota(self) -> None:
        """L'upload doit être refusé si dépasse le quota."""
        policy = FixedQuotaPolicy(quota_bytes=1000)
        assert policy.can_upload("user1", 1500) is False

    def test_can_upload_exactly_at_quota(self) -> None:
        """L'upload doit être autorisé si exactement au quota."""
        policy = FixedQuotaPolicy(quota_bytes=1000)
        assert policy.can_upload("user1", 1000) is True

    def test_remaining_quota_calculation(self) -> None:
        """Le quota restant doit être calculé correctement."""
        policy = FixedQuotaPolicy(quota_bytes=1000)
        assert policy.get_remaining_quota("user1") == 1000

        policy.record_upload("user1", 300)
        assert policy.get_remaining_quota("user1") == 700

    def test_quota_per_user(self) -> None:
        """Chaque utilisateur a son propre quota indépendant."""
        policy = FixedQuotaPolicy(quota_bytes=1000)

        policy.record_upload("user1", 600)
        policy.record_upload("user2", 200)

        assert policy.get_remaining_quota("user1") == 400
        assert policy.get_remaining_quota("user2") == 800


class TestUnlimitedQuotaPolicy:
    """Tests de la politique de quota illimité."""

    def test_always_allows_upload(self) -> None:
        """L'upload doit toujours être autorisé."""
        policy = UnlimitedQuotaPolicy()
        assert policy.can_upload("user1", 1000000000) is True
        assert policy.can_upload("user2", 999999999999) is True

    def test_returns_unlimited_quota(self) -> None:
        """Le quota doit être indiqué comme illimité (-1)."""
        policy = UnlimitedQuotaPolicy()
        assert policy.get_remaining_quota("user1") == -1
        assert policy.get_remaining_quota("user2") == -1


class TestQuotaPolicyStrategy:
    """Tests du pattern Strategy : interchangeabilité des politiques."""

    @pytest.fixture
    def policies(self) -> list[QuotaPolicy]:
        """Fixture retournant différentes implémentations du Strategy."""
        return [
            FixedQuotaPolicy(quota_bytes=1000),
            UnlimitedQuotaPolicy(),
        ]

    def test_all_policies_implement_same_interface(self, policies: list[QuotaPolicy]) -> None:
        """Toutes les politiques doivent implémenter la même interface."""
        for policy in policies:
            # Toutes doivent avoir ces méthodes
            assert hasattr(policy, "can_upload")
            assert hasattr(policy, "get_remaining_quota")
            assert callable(policy.can_upload)
            assert callable(policy.get_remaining_quota)

    def test_policies_are_interchangeable(self) -> None:
        """On peut remplacer une politique par une autre (principe L : Liskov)."""

        def check_upload(policy: QuotaPolicy, user_id: str, size: int) -> bool:
            """Fonction qui utilise une politique (n'importe laquelle)."""
            return policy.can_upload(user_id, size)

        # Les deux politiques peuvent être utilisées de manière interchangeable
        fixed = FixedQuotaPolicy(quota_bytes=100)
        unlimited = UnlimitedQuotaPolicy()

        assert check_upload(fixed, "user1", 50) is True
        assert check_upload(unlimited, "user1", 50) is True
