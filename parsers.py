"""Turn raw file bytes into something the page can show, or say why it can't."""
import csv
import io
from dataclasses import dataclass
from pathlib import PurePosixPath

from markdown_it import MarkdownIt

MAX_BYTES = 1024 * 1024
_CONTROL_BYTES = bytes(b for b in range(32) if b not in b"\t\n\r\f")
_markdown = MarkdownIt("js-default")  # Raw HTML off, unsafe links blocked.


class ParseFailure(Exception):
    """A file we read successfully but cannot show."""


class EmptyFile(ParseFailure):
    pass


class CorruptFile(ParseFailure):
    pass


class UnsupportedFormat(ParseFailure):
    pass


class FileTooLarge(ParseFailure):
    pass


@dataclass
class Parsed:
    text: str | None = None
    html: str | None = None
    rows: list[list[str]] | None = None
    notice: str | None = None


def _parse_txt(text: str) -> Parsed:
    return Parsed(text=text)


def _parse_md(text: str) -> Parsed:
    return Parsed(html=_markdown.render(text))


def _parse_csv(text: str) -> Parsed:
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        rows = [row for row in reader if row]
    except csv.Error as err:
        raise CorruptFile(f"מבנה ה-CSV שבור בשורה {reader.line_num}") from err
    for line, row in enumerate(rows, start=1):
        if len(row) != len(rows[0]):
            raise CorruptFile(f"בשורה {line} מספר העמודות הוא {len(row)} במקום {len(rows[0])}")
    return Parsed(rows=rows)


_PARSERS = {"txt": _parse_txt, "md": _parse_md, "csv": _parse_csv}
SUPPORTED = tuple(_PARSERS)


def _decode(data: bytes) -> tuple[str, str | None]:
    try:
        return data.decode("utf-8-sig"), None
    except UnicodeDecodeError:
        pass
    try:
        return data.decode("cp1255"), "הקובץ אינו UTF-8 ופוענח כ-cp1255. אם הטקסט נראה משובש, שמרו אותו מחדש כ-UTF-8."
    except UnicodeDecodeError as err:
        raise CorruptFile("קידוד הקובץ אינו מוכר") from err


def parse(name: str, data: bytes) -> Parsed:
    if len(data) > MAX_BYTES:
        raise FileTooLarge(f"הגודל המרבי הוא {MAX_BYTES // 1024} KB")
    extension = PurePosixPath(name).suffix.lstrip(".").lower()
    if extension not in _PARSERS:
        raise UnsupportedFormat(f"הסיומת '.{extension}' אינה נתמכת")
    if any(byte in _CONTROL_BYTES for byte in data):
        raise CorruptFile("נראה שזה קובץ בינארי ולא טקסט")
    text, notice = _decode(data)
    if not text.strip():
        raise EmptyFile
    parsed = _PARSERS[extension](text)
    parsed.notice = notice
    return parsed
