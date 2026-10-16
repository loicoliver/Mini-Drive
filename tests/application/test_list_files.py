"""Tests du use case ListFiles."""

from minidrive.adapters.memory.blob_storage import InMemoryBlobStorage
from minidrive.adapters.memory.file_repository import InMemoryFileRepository
from minidrive.adapters.memory.folder_repository import InMemoryFolderRepository
from minidrive.adapters.memory.id_generator import UuidIdGenerator
from minidrive.adapters.memory.share_repository import InMemoryShareRepository
from minidrive.application.quota_policies import UnlimitedQuotaPolicy
from minidrive.application.use_cases.list_files import ListFiles
from minidrive.application.use_cases.upload_file import UploadFile


def make_list_files() -> tuple[ListFiles, UploadFile]:
    """Fabrique un ListFiles câblé sur un repository mémoire vierge."""
    repository = InMemoryFileRepository()
    return (
        ListFiles(file_repository=repository, share_repository=InMemoryShareRepository()),
        UploadFile(
            file_repository=repository,
            blob_storage=InMemoryBlobStorage(),
            id_generator=UuidIdGenerator(),
            quota_policy=UnlimitedQuotaPolicy(),
            folder_repository=InMemoryFolderRepository(),
        ),
    )


class TestListFiles:
    """Tests du use case ListFiles."""

    def test_list_empty_repository(self) -> None:
        """Lister un repository vide doit retourner une liste vide."""
        list_files, _ = make_list_files()

        assert list_files.execute() == []

    def test_list_returns_uploaded_files_sorted(self) -> None:
        """Lister doit retourner les fichiers uploadés, triés par nom."""
        list_files, upload_file = make_list_files()
        upload_file.execute(name="zebra.bin", data=b"z")
        upload_file.execute(name="alpha.bin", data=b"a")

        files = list_files.execute()

        assert [file.name.value for file in files] == ["alpha.bin", "zebra.bin"]
