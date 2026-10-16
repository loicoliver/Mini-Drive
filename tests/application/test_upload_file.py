"""Tests du use case UploadFile."""

import pytest

from minidrive.adapters.memory.blob_storage import InMemoryBlobStorage
from minidrive.adapters.memory.file_repository import InMemoryFileRepository
from minidrive.adapters.memory.id_generator import UuidIdGenerator
from minidrive.application.quota_policies import (
    FixedQuotaPolicy,
    QuotaPolicy,
    UnlimitedQuotaPolicy,
)
from minidrive.application.use_cases.upload_file import UploadFile
from minidrive.application.users import DEFAULT_USER_ID
from minidrive.domain.errors import (
    FileAlreadyExistsError,
    InvalidFileNameError,
    QuotaExceededError,
)


def make_upload_file(quota_policy: QuotaPolicy | None = None) -> UploadFile:
    """Fabrique un UploadFile câblé sur des adapteurs mémoire vierges."""
    return UploadFile(
        file_repository=InMemoryFileRepository(),
        blob_storage=InMemoryBlobStorage(),
        id_generator=UuidIdGenerator(),
        quota_policy=quota_policy or UnlimitedQuotaPolicy(),
    )


class TestUploadFile:
    """Tests du use case UploadFile avec adapteurs mémoire."""

    def test_upload_success(self) -> None:
        """Uploader un fichier doit persister métadonnées et contenu."""
        use_case = make_upload_file()

        file = use_case.execute(name="rapport.pdf", data=b"contenu")

        assert file.name.value == "rapport.pdf"
        assert file.size.value == 7
        assert file.parent_id is None
        assert file.id

    def test_upload_stores_blob_readable_by_id(self) -> None:
        """Le contenu doit être retrouvé via le blob storage (même ID)."""
        blob_storage = InMemoryBlobStorage()
        use_case = UploadFile(
            file_repository=InMemoryFileRepository(),
            blob_storage=blob_storage,
            id_generator=UuidIdGenerator(),
            quota_policy=UnlimitedQuotaPolicy(),
        )

        file = use_case.execute(name="a.bin", data=b"\x00\x01\x02")

        assert blob_storage.read(file.id) == b"\x00\x01\x02"

    def test_upload_empty_file(self) -> None:
        """Uploader un fichier vide doit fonctionner."""
        use_case = make_upload_file()

        file = use_case.execute(name="vide.txt", data=b"")

        assert file.size.value == 0

    def test_upload_invalid_name(self) -> None:
        """Un nom invalide doit lever InvalidFileNameError (aucun stockage)."""
        blob_storage = InMemoryBlobStorage()
        use_case = UploadFile(
            file_repository=InMemoryFileRepository(),
            blob_storage=blob_storage,
            id_generator=UuidIdGenerator(),
            quota_policy=UnlimitedQuotaPolicy(),
        )

        with pytest.raises(InvalidFileNameError):
            use_case.execute(name="mauvais/nom.txt", data=b"x")

    def test_upload_duplicate_name(self) -> None:
        """Deux fichiers même nom même parent doivent lever FileAlreadyExistsError."""
        use_case = make_upload_file()
        use_case.execute(name="doublon.txt", data=b"un")

        with pytest.raises(FileAlreadyExistsError) as exc_info:
            use_case.execute(name="doublon.txt", data=b"deux")

        assert "doublon.txt" in str(exc_info.value)

    def test_upload_same_name_different_parent_allowed(self) -> None:
        """Même nom dans des parents différents doit être autorisé."""
        use_case = make_upload_file()

        file1 = use_case.execute(name="a.txt", data=b"1", parent_id=None)
        file2 = use_case.execute(name="a.txt", data=b"2", parent_id="parent-1")

        assert file1.id != file2.id

    def test_upload_quota_exceeded(self) -> None:
        """Un upload dépassant le quota doit lever QuotaExceededError sans stocker."""
        blob_storage = InMemoryBlobStorage()
        repository = InMemoryFileRepository()
        use_case = UploadFile(
            file_repository=repository,
            blob_storage=blob_storage,
            id_generator=UuidIdGenerator(),
            quota_policy=FixedQuotaPolicy(quota_bytes=10),
        )

        with pytest.raises(QuotaExceededError):
            use_case.execute(name="gros.bin", data=b"x" * 11)

        assert repository.list_all() == []

    def test_upload_records_quota_usage(self) -> None:
        """Un upload réussi doit décompter le quota (le suivant peut échouer)."""
        policy = FixedQuotaPolicy(quota_bytes=10)
        use_case = make_upload_file(quota_policy=policy)
        use_case.execute(name="a.bin", data=b"12345678")

        assert policy.get_remaining_quota(DEFAULT_USER_ID) == 2
        with pytest.raises(QuotaExceededError):
            use_case.execute(name="b.bin", data=b"123")

    def test_upload_uses_default_local_user(self) -> None:
        """Sans user_id explicite, l'utilisateur local est utilisé pour le quota."""
        policy = FixedQuotaPolicy(quota_bytes=5)
        use_case = make_upload_file(quota_policy=policy)
        use_case.execute(name="a.bin", data=b"12345")

        assert policy.get_remaining_quota("local") == 0
