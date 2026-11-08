"""GcsSource against a stub client that raises Google's real exception types."""
from types import SimpleNamespace

import pytest
from google.api_core import exceptions as gexc

import parsers
from main import FileDenied, FileMissing, GcsSource, SourceUnavailable


class StubBlob:
    def __init__(self, size=2, data=b"hi", generation=7, download_error=None):
        self.size, self.data, self.generation = size, data, generation
        self.download_error = download_error
        self.downloads = []

    def download_as_bytes(self, **kwargs):
        self.downloads.append(kwargs)
        if self.download_error:
            raise self.download_error
        return self.data


def source_with(blob=None, error=None):
    def get_blob(name, **kwargs):
        if error:
            raise error
        return blob

    client = SimpleNamespace(bucket=lambda _: SimpleNamespace(get_blob=get_blob))
    return GcsSource("bucket", client=client)


def test_returns_content_and_generation():
    result = source_with(StubBlob()).read("message.txt")
    assert (result.data, result.generation) == (b"hi", 7)


def test_download_is_pinned_to_the_generation_it_reported():
    blob = StubBlob()
    source_with(blob).read("message.txt")
    assert blob.downloads[0]["if_generation_match"] == 7


def test_missing_blob_is_file_missing():
    with pytest.raises(FileMissing):
        source_with(blob=None).read("message.txt")


def test_blob_deleted_mid_read_is_file_missing():
    with pytest.raises(FileMissing):
        source_with(StubBlob(download_error=gexc.NotFound("gone"))).read("message.txt")


def test_forbidden_is_denied():
    with pytest.raises(FileDenied):
        source_with(error=gexc.Forbidden("no")).read("message.txt")


@pytest.mark.parametrize(
    "error",
    [gexc.ServiceUnavailable("x"), gexc.TooManyRequests("x"), gexc.RetryError("x", None)],
)
def test_transient_google_errors_are_unavailable(error):
    with pytest.raises(SourceUnavailable):
        source_with(error=error).read("message.txt")


def test_file_replaced_mid_read_is_unavailable():
    blob = StubBlob(download_error=gexc.PreconditionFailed("changed"))
    with pytest.raises(SourceUnavailable):
        source_with(blob).read("message.txt")


def test_oversized_blob_is_not_downloaded():
    blob = StubBlob(size=parsers.MAX_BYTES + 1)
    with pytest.raises(parsers.FileTooLarge):
        source_with(blob).read("message.txt")
    assert blob.downloads == []
