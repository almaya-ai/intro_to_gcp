# מפת `.claude`

המבנה עוקב אחרי [התיעוד הרשמי](https://code.claude.com/docs/en/claude-directory). התיעוד של התיקיות מרוכז כאן ולא בתוכן, כי קובצי `.md` בתוך `agents/`, `commands/`, `rules/` ו-`output-styles/` מיועדים להיטען כרכיבים.

| נתיב | מה יש בו | מצב |
|---|---|---|
| `settings.json` | הרשאות, hooks, תוספים, כיבוי זיכרון גלובלי, תיקיית תוכניות | פעיל |
| `settings.local.json` | העדפות אישיות למחשב אחד | לא בריפו, נוצר בעת הצורך |
| `hooks/` | `guard_deploy.py`, `after_edit.py`, `session_context.py` | פעיל ובדוק ב-`tests/test_hooks.py` |
| `skills/live-check/` | בדיקת השירות החי: `/live-check` | פעיל |
| `skills/improve/` | סגירת עבודה ושיפור: `/improve` | פעיל |
| `agents/cloud-security-reviewer.md` | סוקר חשיפה בענן, קריאה בלבד | מוכן לשימוש |
| `rules/` | כללים לפי נתיבים: `python.md`, `gcp.md`, `docs.md` | פעיל |
| `memory/` | הזיכרון של הפרויקט ו-`MEMORY.md` | פעיל. זו מוסכמה של הפרויקט, לא תכונה מובנית |
| `commands/` | פקודה בקובץ יחיד. התיעוד מציג אותה כאותו מנגנון של skills | ריק, מעדיפים `skills/` |
| `output-styles/` | סגנונות תגובה | ריק |
| `workflows/` | סקריפטי `*.js` לתזמור סוכנים | ריק |
| `agent-memory/` | זיכרון של subagents שהוגדר להם `memory` | ריק |

**בשורש הפרויקט:** `CLAUDE.md`, `.mcp.json` (שרתי MCP משותפים, כרגע ריק), `.worktreeinclude` (קבצים מ-`.gitignore` שיועתקו ל-worktree), ו-`CLAUDE.local.md` (העדפות אישיות, לא בריפו, נוצר בעת הצורך).

## למה תיקיות ריקות?
כדי שהמבנה הרשמי יהיה גלוי, ו-`.gitkeep` שומר אותן ב-git. מוסיפים רכיב רק כשיש לו שימוש אמיתי: פעולה שחזרה שלוש פעמים ב-[`docs/skill-candidates.md`](../docs/skill-candidates.md), או כלל שנשכח פעמיים.

## למה הזיכרון כאן ולא בנתיב ברירת המחדל?
כברירת מחדל Claude Code שומר זיכרון ב-`~/.claude/projects/<project>/memory/`, מחוץ לריפו. `autoMemoryDirectory` מקבל רק נתיב מוחלט או `~/`, ולכן לא מתאים לריפו שעובר בין מחשבים. לכן `settings.json` מכבה את הזיכרון האוטומטי, ו-`CLAUDE.md` טוען את `memory/MEMORY.md`.

**המחיר:** הכתיבה לזיכרון נשענת על ההוראות ב-`CLAUDE.md` ועל `/improve`, ולא על מנגנון אוטומטי.
