# תוכנית ביצוע

**מטרה:** לממש את [האפיון](../specs/2026-11-08-cloud-run-gcs-design.md).

## שלבים

| # | שלב | קבצים | בדיקה | סטטוס |
|---|---|---|---|---|
| 1 | Parsers ב-TDD | `tests/test_parsers.py`, `parsers.py` | `pytest` | בוצע |
| 2 | קריאה מ-GCS ב-TDD, עם חריגות Google אמיתיות | `tests/test_gcs.py`, `main.py` | `pytest` | בוצע |
| 3 | דף ומצבים ב-TDD | `tests/test_app.py`, `main.py`, `templates/page.html` | `pytest` | בוצע |
| 4 | פריסה | `deploy.sh`, `Dockerfile`, `.gcloudignore` | הכתובת החיה | בוצע |
| 5 | החלפה ב-Console | `samples/v2/message.txt` | `generation` משתנה, revision לא | בוצע |
| 6 | מצבי כשל חיים | קובצי `samples/` | קודים ב-[decisions.md](../../decisions.md) | בוצע |
| 7 | בידוד הרשאות | IAM על ה-Bucket | ניסוי החלפת תפקיד | בוצע |
| 8 | מבנה `.claude` ותיעוד | `.claude/`, `docs/`, `tests/test_hooks.py` | `pytest`, `/live-check` | בוצע |
| 9 | התאוששות בלשונית גלויה | - | `document.hidden=false`, והדף חוזר לתוכן לבד | בוצע |
| 10 | תצורה מחוץ לקוד, ללא סודות | `env.example`, `tests/test_config.py` | `pytest`, הרצה מקומית | בוצע |

## מה השתנה בדרך

- **השערה נפסלה.** הכוונה הייתה לתעד שבלי `storage.objects.list` קובץ חסר יחזיר 403. שתי מדידות החזירו 404, והלקח הפך ל"לא כותבים בלי למדוד" (L-003).
- **נוסף ניסיון חוזר ל-`deploy.sh`,** אחרי שהפריסה הראשונה נכשלה על Service Account שעוד לא הופץ (L-002).
- **שני תיקוני ניסוח** התגלו רק בבדיקה החיה: כפילות ב"הקובץ ריק" ו-"1 עמודות" לא דקדוקי. כל אחד תוקן ב-TDD.
- **הערכים יצאו מהקוד.** הפרויקט וה-Bucket היו כתובים ב-`deploy.sh` וב-`check.py`, ועברו ל-`.env`.
- **המבנה סביב הקוד נוסף אחרי הפריסה.** בפרויקט הבא מקימים אותו בשלב 0 (L-006).

## איך בודקים

בכל שלב: `.venv/bin/python -m pytest`. אחרי פריסה או שינוי הרשאה: `/live-check`. הפירוט ב-[runbook.md](../../runbook.md).
