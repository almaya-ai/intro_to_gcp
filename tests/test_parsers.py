import pytest

import parsers
from parsers import CorruptFile, EmptyFile, FileTooLarge, UnsupportedFormat, parse


def test_txt_keeps_hebrew_text():
    assert parse("message.txt", "גרסה 1".encode()).text == "גרסה 1"


def test_utf8_bom_is_removed():
    assert parse("message.txt", b"\xef\xbb\xbfhi").text == "hi"


def test_cp1255_is_decoded_with_a_visible_notice():
    result = parse("message.txt", "שלום".encode("cp1255"))
    assert result.text == "שלום"
    assert "cp1255" in result.notice


def test_utf8_file_has_no_notice():
    assert parse("message.txt", b"hi").notice is None


@pytest.mark.parametrize("data", [b"", b"  \n\t "])
def test_blank_file_is_empty(data):
    with pytest.raises(EmptyFile):
        parse("message.txt", data)


def test_image_renamed_to_txt_is_corrupt():
    with pytest.raises(CorruptFile):
        parse("message.txt", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")


def test_oversized_file_is_rejected():
    with pytest.raises(FileTooLarge):
        parse("message.txt", b"a" * (parsers.MAX_BYTES + 1))


def test_unknown_extension_is_unsupported():
    with pytest.raises(UnsupportedFormat):
        parse("report.pdf", b"%PDF-1.7")


def test_extension_is_case_insensitive():
    assert parse("NOTE.TXT", b"hi").text == "hi"


def test_markdown_renders_heading():
    assert "<h1>כותרת</h1>" in parse("a.md", "# כותרת".encode()).html


def test_markdown_escapes_raw_html():
    html = parse("a.md", b"<script>alert(1)</script>").html
    assert "<script>" not in html


def test_markdown_blocks_javascript_links():
    assert "<a " not in parse("a.md", b"[x](javascript:alert(1))").html


def test_csv_becomes_rows():
    assert parse("a.csv", "שם,גיל\nדנה,30\n".encode()).rows == [
        ["שם", "גיל"],
        ["דנה", "30"],
    ]


def test_csv_with_uneven_row_is_corrupt_and_names_the_line():
    with pytest.raises(CorruptFile, match="3"):
        parse("a.csv", b"a,b\n1,2\n3\n")


def test_csv_with_unclosed_quote_is_corrupt():
    with pytest.raises(CorruptFile):
        parse("a.csv", b'a,b\n"1,2\n')


def test_supported_lists_every_format():
    assert parsers.SUPPORTED == ("txt", "md", "csv")
