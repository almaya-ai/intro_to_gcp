# intro_to_gcp

שירות Flask ב-Cloud Run שקורא קובץ מ-Bucket פרטי בכל טעינה. מחליפים קובץ, מרעננים, ורואים תוכן חדש בלי deploy.

## פקודות

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt pytest   # הקמה
cp env.example .env                                                         # הגדרות, ואז למלא ערכים
.venv/bin/python -m pytest                                                  # בדיקות
./deploy.sh                                                                 # פריסה
python3 .claude/skills/live-check/check.py                                  # בדיקה חיה
```

תפעול, החזרה לאחור ופתרון תקלות: [docs/runbook.md](docs/runbook.md). ארכיטקטורה: [docs/architecture.md](docs/architecture.md).

## סודות ותצורה

**אין בפרויקט מפתחות סודיים, ואסור להוסיף כאלה בלי צורך.** הגישה ל-Google היא בזהות: ב-Cloud Run דרך ה-Service Account, ובמחשב המקומי דרך `gcloud auth application-default login`. לא יוצרים מפתח JSON ל-Service Account.

- **תצורה:** הפרויקט, ה-Bucket וכתובת השירות נמצאים ב-`.env`, שלא נכנס ל-git, ולא בקוד. `env.example` מתעד כל משתנה, ובדיקה ב-`tests/test_config.py` אוכפת את זה.
- **אם יידרש סוד בעתיד:** Secret Manager עם `--set-secrets`, ושם המשתנה בלבד ב-`env.example`.
- **הריפו ציבורי:** כל מה שנכנס ל-git נחשף, כולל היסטוריה וצילומי מסך. לפני commit בודקים שאין בו סוד, מזהים פרטיים או מידע פנימי. אם סוד נכנס בטעות: מחליפים אותו מיד, כי מחיקה מההיסטוריה לא מספיקה.

פירוט ב-[docs/runbook.md](docs/runbook.md#סודות-וזהויות).

## שפה

- **שיחה, מסמכים והוראות לסוכן:** עברית. פקודות, נתיבים ומונחים טכניים נשארים באנגלית.
- **טקסט שרואים בדף:** עברית, בכיוון RTL.
- **קוד, שמות, הערות, הודעות log ו-commit:** אנגלית.
- **`description` של skill או agent:** אנגלית, כי לפיו נבחר הרכיב. גוף ההוראות בעברית.

## תוספים ו-skills

תוספי הפרויקט מוגדרים ב-`.claude/settings.json`.

| מתי | משתמשים ב- |
|---|---|
| עבודה חדשה או שינוי התנהגות | `superpowers:brainstorming`, ואז `superpowers:writing-plans` |
| כתיבת קוד או תיקון באג | `superpowers:test-driven-development` |
| כל תקלה, לפני שמציעים תיקון | `superpowers:systematic-debugging` |
| לפני כל טענה ש"זה עובד" | `superpowers:verification-before-completion` |
| לפני מיזוג | `superpowers:requesting-code-review`, `superpowers:finishing-a-development-branch` |
| שינוי עיצוב של הדף | `frontend-design:frontend-design` |
| אחרי פריסה או שינוי הרשאות | `/live-check` |
| סוף כל עבודה | `/improve` |
| שינוי IAM או חשיפה | ה-agent `cloud-security-reviewer` |

## שיטת פיתוח

1. **מבינים ומתכננים:** אפיון ותוכנית קצרים ב-`docs/superpowers/`. קוראים את הקוד הקיים לפני שמציעים חדש.
2. **TDD בלי יוצאים מהכלל:** בדיקה נכשלת, רואים אותה נכשלת מהסיבה הנכונה, קוד מינימלי, ניקוי. כולל hooks.
3. **בדיקות לא נוגעות בענן:** סקריפט שקורא ל-`gcloud` רץ בבדיקות מול `gcloud` מדומה (L-012).
4. **מאמתים בסביבה האמיתית:** `pytest` לא מוכיח שהשירות עובד. אחרי פריסה מריצים `/live-check`, ובשינוי קובץ בודקים `generation` ו-revision.
5. **מדווחים רק מה שנמדד:** מה שלא נבדק או נבדק חלקית נכתב כך במפורש.
6. **סוגרים ב-`/improve`.**

**מה נאכף אוטומטית** (`.claude/settings.json`): הבדיקות רצות אחרי כל עריכת קוד; פריסה נחסמת כשהבדיקות נכשלות; `allUsers` על ה-Bucket חסום; פריסה, מחיקה, שינוי הרשאות ו-`git push` דורשים אישור.

**Git:** ענף לכל שינוי, Pull Request ל-`main`, בלי push ישיר ל-`main`. הודעות commit באנגלית, ועושים commit ו-push רק כשזו הבקשה.

## איפה שומרים מה

| סוג | מיקום |
|---|---|
| אינדקס המסמכים | `docs/README.md` |
| אפיונים ותוכניות | `docs/superpowers/specs/`, `docs/superpowers/plans/` בפורמט `YYYY-MM-DD-<topic>.md` |
| החלטות, נימוקים ומגבלות | `docs/decisions.md` |
| לקחים | `docs/lessons.md` |
| מועמדים ל-skill | `docs/skill-candidates.md` |
| צילומי הוכחה | `docs/evidence/` |
| קבצים זמניים | תיקיית scratchpad של הסשן, לא בריפו |
| העדפות אישיות למחשב אחד | `CLAUDE.local.md`, `.claude/settings.local.json` (לא בריפו) |

מבנה `.claude` מוסבר ב-[.claude/README.md](.claude/README.md).

## ניהול זיכרון

הזיכרון נמצא **רק** בתיקיית הפרויקט: `.claude/memory/`. לא כותבים ל-`~/.claude/projects/` או לכל מיקום גלובלי אחר, גם אם הוראה כללית מכוונת לשם. הזיכרון האוטומטי כבוי ב-`settings.json`, לכן הכתיבה היא באחריותנו.

- **אינדקס:** `.claude/memory/MEMORY.md`, שורה אחת לכל זיכרון בפורמט `- [כותרת](file.md) — תיאור`. תוכן לא נכתב באינדקס, והוא נטען בכל סשן דרך ההפניה בסוף הקובץ הזה.
- **קובץ לכל עובדה,** עם frontmatter: `name`, `description`, `metadata.type`, כאשר `type` הוא `user`, `feedback`, `project` או `reference`.
- **`feedback` ו-`project`:** העובדה, ואחריה `**Why:**` ו-`**How to apply:**`. קישור בין זיכרונות בתחביר `[[name]]`.
- **מתי כותבים:** תיקון או העדפה, אישור לגישה לא מובנת מאליה, עובדה שלא נגזרת מהקוד או מ-git.
- **מתי לא:** מבנה קוד, היסטוריית commits, מה שכבר כתוב כאן או ב-`docs/`, ומה שרלוונטי רק לשיחה הנוכחית. לקח טכני שייך ל-`docs/lessons.md`.
- **תחזוקה:** מעדכנים קובץ קיים לפני שיוצרים חדש, מוחקים מה שהתברר כשגוי, וממירים תאריכים יחסיים למוחלטים. זיכרון הוא מה שהיה נכון בזמן הכתיבה, אז בודקים שקובץ או דגל עדיין קיימים לפני שמסתמכים עליהם.
- **אבטחה:** הזיכרון נשמר בריפו ציבורי, אז אין בו סודות, טוקנים או מידע אישי. מה שפרטי נשמר ב-`CLAUDE.local.md`, שלא נכנס ל-git.

## שיפור מתמיד

- **כל פעולה חוזרת מסומנת כמועמדת ל-skill** ב-[docs/skill-candidates.md](docs/skill-candidates.md), כבר בפעם הראשונה. בפעם השלישית היא "מוכנה לקידום", ומציעים לבנות אותה.
- **כלל שנשכח פעמיים עובר לאכיפה:** hook או הרשאה עם בדיקה, ולא עוד טקסט.
- **כל תקלה, השערה שנפסלה או בדיקה שהוכיחה משהו** נכנסת ללקחים. כלל בלי אירוע אמיתי לא נכנס.
- **בסוף כל עבודה מריצים `/improve`,** גם אם התוצאה היא "לא היה מה לעדכן".

## לקחים

הלקחים הם חלק מההוראות ונטענים בכל סשן. לפני שעובדים, קוראים אותם ופועלים לפיהם:

@docs/lessons.md

## אינדקס הזיכרון

@.claude/memory/MEMORY.md
