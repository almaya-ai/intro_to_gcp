"""Show a file from a private GCS bucket, re-read on every page load."""
import os
import re
from dataclasses import dataclass

from flask import Flask, render_template, request
from google.api_core import exceptions as gexc
from google.cloud import storage
from google.cloud.storage.retry import DEFAULT_RETRY
from markupsafe import Markup

import parsers

DEFAULT_FILE = "message.txt"
RETRY_SECONDS = 15
_SAFE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}")
_READ_OPTIONS = {"timeout": 5, "retry": DEFAULT_RETRY.with_timeout(10)}


class FileMissing(Exception):
    pass


class FileDenied(Exception):
    pass


class SourceUnavailable(Exception):
    pass


class InvalidName(Exception):
    pass


@dataclass
class ReadResult:
    data: bytes
    generation: int


class GcsSource:
    def __init__(self, bucket_name, client=None):
        self._bucket = (client or storage.Client()).bucket(bucket_name)

    def read(self, name):
        try:
            blob = self._bucket.get_blob(name, **_READ_OPTIONS)
            if blob is None:
                raise FileMissing
            if blob.size > parsers.MAX_BYTES:
                raise parsers.FileTooLarge(f"הגודל המרבי הוא {parsers.MAX_BYTES // 1024} KB")
            # Pinned so the generation shown always matches the bytes shown.
            data = blob.download_as_bytes(if_generation_match=blob.generation, **_READ_OPTIONS)
        except gexc.NotFound as err:
            raise FileMissing from err
        except (gexc.Forbidden, gexc.Unauthorized) as err:
            raise FileDenied from err
        except gexc.GoogleAPIError as err:
            raise SourceUnavailable from err
        return ReadResult(data, blob.generation)


@dataclass(frozen=True)
class State:
    status: int
    title: str
    message: str = ""
    retry: str | None = None  # "auto", "manual" or None.
    log: bool = False


AFTER_REPLACE = "החליפו את הקובץ באותו שם ב-Cloud Storage, ואז לחצו על הכפתור."
STATES = {
    FileMissing: State(404, "הקובץ עדיין לא הועלה", "ברגע שיועלה הוא יופיע כאן מעצמו. אין צורך לעשות דבר.", "auto"),
    parsers.EmptyFile: State(200, "הקובץ ריק", "כשיתווסף לו תוכן הוא יופיע כאן מעצמו.", "auto"),
    parsers.CorruptFile: State(422, "לא הצלחנו לקרוא את הקובץ", AFTER_REPLACE, "manual"),
    parsers.UnsupportedFormat: State(415, "הפורמט הזה לא נתמך", AFTER_REPLACE, "manual"),
    parsers.FileTooLarge: State(413, "הקובץ גדול מדי", AFTER_REPLACE, "manual"),
    FileDenied: State(500, "התקלה אצלנו", "לשירות אין הרשאה לקרוא את הקובץ. ניסיון חוזר לא יעזור, פנו למנהל המערכת.", log=True),
    SourceUnavailable: State(503, "יש כרגע תקלה זמנית", "הדף ינסה שוב בעצמו.", "auto", log=True),
    InvalidName: State(400, "שם הקובץ אינו תקין", "מותרים אותיות באנגלית, ספרות, נקודה, מקף וקו תחתון."),
}
UNEXPECTED = STATES[SourceUnavailable]


def create_app(source, revision=None):
    app = Flask(__name__)

    def show(name, state, detail=""):
        if state.log:
            app.logger.exception("Could not read %s", name)
        supported = parsers.SUPPORTED if state.status == 415 else ()
        html = render_template(
            "page.html",
            name=name,
            state=state,
            detail=detail,
            supported=supported,
            revision=revision,
            retry_seconds=RETRY_SECONDS,
        )
        headers = {"Retry-After": str(RETRY_SECONDS)} if state.status == 503 else {}
        return html, state.status, headers

    @app.get("/")
    def index():
        name = request.args.get("file", DEFAULT_FILE)
        try:
            if not _SAFE_NAME.fullmatch(name):
                raise InvalidName
            result = source.read(name)
            parsed = parsers.parse(name, result.data)
        except tuple(STATES) as err:
            detail = str(err) if isinstance(err, parsers.ParseFailure) else ""
            return show(name, STATES[type(err)], detail)
        except Exception:
            return show(name, UNEXPECTED)
        html = Markup(parsed.html) if parsed.html else None  # Sanitized by parsers.
        return render_template(
            "page.html",
            name=name,
            parsed=parsed,
            html=html,
            generation=result.generation,
            revision=revision,
        )

    @app.after_request
    def never_cache(response):
        response.headers["Cache-Control"] = "no-store"
        return response

    return app


def production_app():
    source = GcsSource(os.environ["BUCKET_NAME"])
    return create_app(source, revision=os.environ.get("K_REVISION"))
