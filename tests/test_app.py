import pytest

import parsers
from main import (
    FileDenied,
    FileMissing,
    ReadResult,
    SourceUnavailable,
    create_app,
)


class FakeSource:
    def __init__(self, data=b"", error=None):
        self.data, self.error = data, error
        self.names = []

    def read(self, name):
        self.names.append(name)
        if self.error:
            raise self.error
        return ReadResult(self.data, 42)


def get(source, url="/"):
    return create_app(source, revision="rev-1").test_client().get(url)


def page(response):
    return response.get_data(as_text=True)


def test_shows_file_name_and_content():
    response = get(FakeSource("גרסה 1".encode()))
    assert response.status_code == 200
    assert "message.txt" in page(response)
    assert "גרסה 1" in page(response)


def test_shows_generation_and_revision_as_proof_of_freshness():
    body = page(get(FakeSource(b"x")))
    assert "42" in body
    assert "rev-1" in body


def test_response_is_never_cached():
    assert get(FakeSource(b"x")).headers["Cache-Control"] == "no-store"


def test_every_load_reads_the_source_again():
    source = FakeSource(b"x")
    client = create_app(source, revision="r").test_client()
    client.get("/")
    client.get("/")
    assert len(source.names) == 2


def test_html_in_a_text_file_is_escaped():
    assert "<script>alert" not in page(get(FakeSource(b"<script>alert(1)</script>")))


def test_csv_renders_as_table():
    body = page(get(FakeSource(b"a,b\n1,2\n"), "/?file=data.csv"))
    assert "<table" in body
    assert "<th" in body


def test_markdown_renders_as_html():
    assert "<h1>" in page(get(FakeSource(b"# hi"), "/?file=note.md"))


def test_cp1255_notice_is_visible():
    assert "cp1255" in page(get(FakeSource("שלום".encode("cp1255"))))


def test_missing_file_is_404_with_automatic_retry():
    response = get(FakeSource(error=FileMissing()))
    assert response.status_code == 404
    assert "עדיין לא הועלה" in page(response)
    assert 'data-auto-retry="15"' in page(response)


def test_denied_is_500_and_offers_no_retry():
    response = get(FakeSource(error=FileDenied()))
    assert response.status_code == 500
    assert "ניסיון חוזר לא יעזור" in page(response)
    assert "נסו שוב" not in page(response)


def test_unavailable_is_503_with_retry_after():
    response = get(FakeSource(error=SourceUnavailable()))
    assert response.status_code == 503
    assert response.headers["Retry-After"] == "15"
    assert 'data-auto-retry="15"' in page(response)


def test_empty_file_is_200_with_a_message():
    response = get(FakeSource(b"  "))
    assert response.status_code == 200
    assert page(response).count("הקובץ ריק") == 1


def test_corrupt_file_is_422_and_explains_why():
    response = get(FakeSource(b"a,b\n1\n"), "/?file=data.csv")
    assert response.status_code == 422
    assert "בשורה 2 מספר העמודות הוא 1 במקום 2" in page(response)
    assert "data-auto-retry" not in page(response)


def test_unsupported_is_415_and_lists_supported_formats():
    response = get(FakeSource(b"x"), "/?file=report.pdf")
    assert response.status_code == 415
    assert all(fmt in page(response) for fmt in parsers.SUPPORTED)


def test_too_large_from_the_source_is_413():
    response = get(FakeSource(error=parsers.FileTooLarge("גדול")))
    assert response.status_code == 413


def test_unexpected_error_is_503_without_leaking_details():
    response = get(FakeSource(error=RuntimeError("secret-path")))
    assert response.status_code == 503
    assert "secret-path" not in page(response)


@pytest.mark.parametrize("name", ["../x.txt", "a/b.txt", ".env", "%2e%2e%2fx.txt"])
def test_unsafe_file_name_is_400_and_never_reaches_the_source(name):
    source = FakeSource(b"x")
    response = get(source, f"/?file={name}")
    assert response.status_code == 400
    assert source.names == []


def test_retry_link_keeps_the_requested_file():
    body = page(get(FakeSource(error=FileMissing()), "/?file=data.csv"))
    assert "?file=data.csv" in body


def test_error_page_still_names_the_file():
    assert "message.txt" in page(get(FakeSource(error=FileMissing())))
