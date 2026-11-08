---
name: improve
description: Close a piece of work by capturing what it taught. Use at the end of every task, and whenever an activity repeats, a mistake happens, a hypothesis fails, or the user corrects the way of working.
---

# שיפור בסוף עבודה

עברו על מה שקרה בעבודה הזו, וענו על ארבע שאלות. עדכנו רק מה שבאמת השתנה.

1. **פעולה חוזרת?** פתחו את `docs/skill-candidates.md`.
   - פעולה חדשה: הוסיפו שורה עם ספירה 1.
   - פעולה קיימת: העלו את הספירה.
   - בספירה 3: סמנו "מוכן לקידום" והציעו למשתמש לבנות skill.
2. **לקח?** תקלה, השערה שנפסלה, או בדיקה שהוכיחה משהו: הוסיפו רשומה ל-`docs/lessons.md` בתבנית שמופיעה שם. כלל בלי אירוע אמיתי לא נכנס.
3. **זיכרון?** תיקון או העדפה של המשתמש, או עובדה שלא נגזרת מהקוד: שמרו ב-`.claude/memory/` ועדכנו את `MEMORY.md`. עדכנו קובץ קיים לפני שיוצרים חדש, ומחקו מה שהתברר כשגוי.
4. **אכיפה?** כלל שנשכח פעמיים לא נשאר טקסט: העבירו אותו ל-hook או להרשאה ב-`.claude/settings.json`, ובדקו אותו ב-`tests/test_hooks.py`.

## סיום
דווחו למשתמש בשורה או שתיים מה עודכן. אם לא היה מה לעדכן, כתבו את זה.
