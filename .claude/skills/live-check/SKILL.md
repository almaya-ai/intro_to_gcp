---
name: live-check
description: Verify the deployed Cloud Run service and its private bucket end to end. Use after every deploy or IAM change, after replacing a file, and before claiming that anything works in production.
allowed-tools: Bash(python3 .claude/skills/live-check/check.py *)
---

# בדיקה חיה

הערכים נקראים מ-`.env` בתיקיית הפרויקט, או ממשתני הסביבה. הריצו מתיקיית הפרויקט:

```bash
python3 .claude/skills/live-check/check.py
```

אחרי החלפת קובץ או פריסה, העבירו את מה שאתם מצפים לראות:

```bash
python3 .claude/skills/live-check/check.py --expect-text "גרסה 2" --expect-revision REVISION_NAME
```

## מה נבדק
- הדף מחזיר 200 עם `Cache-Control: no-store`, ומציג `generation` ו-revision.
- קובץ חסר מחזיר 404, ושם קובץ לא בטוח מחזיר 400.
- גישה אנונימית ישירה לאובייקט נחסמת.
- ל-Bucket יש Public Access Prevention ו-Uniform Access.
- ל-Service Account יש `objectViewer` בלבד על ה-Bucket, ושום תפקיד ברמת הפרויקט.

## איך לקרוא את התוצאה
- קוד יציאה 0: כל הבדיקות עברו. כל שורת `FAIL` מסבירה מה התקבל ומה היה צפוי.
- מדווחים את הפלט בפועל. לא כותבים "עובד" בלי הרצה טרייה.
- הבדיקה לא מכסה החלפה דרך ה-Console ולא התאוששות אוטומטית בדפדפן. אלה מתועדות ב-`docs/runbook.md`.
