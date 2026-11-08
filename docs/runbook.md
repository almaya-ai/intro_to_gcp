# מדריך תפעול

הפקודות מניחות שהרצתם מתיקיית הפרויקט, ושהערכים מ-`.env` נטענו לטרמינל:

```bash
set -a; source .env; set +a
```

## סודות וזהויות

**בפרויקט אין מפתחות סודיים.** ה-Service Account לא צריך מפתח JSON, השירות לא מפנה ל-Secret Manager, והמשתנה היחיד שמוגדר בו הוא `BUCKET_NAME`, שאינו סוד.

| מה | איפה זה נמצא | בריפו? |
|---|---|---|
| זהות השירות ב-Cloud Run | Google מנפיקה אסימונים קצרי מועד ל-Service Account. אין קובץ מפתח | לא |
| ההתחברות שלך ל-Google | `~/.config/gcloud/`, כולל `application_default_credentials.json` | לא |
| הפרויקט, ה-Bucket וכתובת השירות | `.env` | לא |
| שמות המשתנים | `env.example` | כן |

**למה זה מספיק:** ההרשאה מוגדרת ב-IAM ולא בקובץ, ולכן אין מה לגנוב מהריפו. גם מי שמכיר את שם ה-Bucket מקבל 403 בניסיון גישה ישירה.

**חשוב לא לבלבל:** קובץ `application_default_credentials.json` במחשב שלך הוא התחברות אישית. לא מעתיקים אותו, ולא מעלים אותו לשום מקום.

## הרצה מקומית

```bash
gcloud auth application-default login
```
```bash
set -a; source .env; set +a; .venv/bin/flask --app 'main:production_app()' run --port 8080
```
הקוד המקומי קורא מאותו Bucket אמיתי, בזהות שלך. בתחתית הדף מופיע `revision local`.

## בדיקה מהירה: האם הכול תקין?

```bash
python3 .claude/skills/live-check/check.py
```

קוד יציאה 0 פירושו שכל הבדיקות עברו. הבדיקה מכסה דף, מצבי כשל, פרטיות וזהות. היא לא מכסה העלאה דרך ה-Console או התאוששות אוטומטית בדפדפן.

## פריסה

```bash
.venv/bin/python -m pytest
```
```bash
./deploy.sh
```
```bash
python3 .claude/skills/live-check/check.py
```

הסקריפט בטוח להרצה חוזרת, ועוצר לפני כל פעולה בענן אם חסרה הגדרה. פריסה יוצרת revision חדש. בפריסה הראשונה מעתיקים את הכתובת שמודפסת ל-`SERVICE_URL` ב-`.env`.

## החלפת הקובץ

**ב-Console:** פותחים את ה-Bucket ב-Cloud Storage, לוחצים Upload ואז Upload files, בוחרים `samples/v2/message.txt`, ובחלון ההתנגשות בוחרים **Overwrite object**.

**בשורת הפקודה:**
```bash
gcloud storage cp samples/v2/message.txt "gs://$BUCKET_NAME/message.txt" --project "$PROJECT"
```

**בדיקה:**
```bash
python3 .claude/skills/live-check/check.py --expect-text "גרסה 2" --expect-revision REVISION_NAME
```
ה-`generation` חייב להשתנות, וה-revision לא.

## חזרה למצב ההתחלתי

```bash
gcloud storage cp samples/message.txt "gs://$BUCKET_NAME/message.txt" --project "$PROJECT"
```
כך הדף חוזר ל"גרסה 1". אחרי זמן ללא תעבורה הטעינה הראשונה איטית יותר, כי השירות יורד לאפס מופעים.

## החזרה לאחור

```bash
gcloud run revisions list --service "$SERVICE" --region "$REGION" --project "$PROJECT"
```
```bash
gcloud run services update-traffic "$SERVICE" --to-revisions REVISION_NAME=100 --region "$REGION" --project "$PROJECT"
```
**קובץ:** ב-Bucket לא מופעל Object Versioning, אז גרסה קודמת של קובץ לא נשמרת כגרסה זמינה. התיקון הוא העלאה מחדש מ-`samples/`.

## לוגים

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE AND severity>=ERROR" --project "$PROJECT" --limit 20 --freshness=1d
```
מצבי תקלה (הרשאות, תקלה זמנית, שגיאה לא צפויה) נרשמים עם stack trace. קובץ חסר או פגום לא נרשם, כי זה מצב תוכן ולא תקלה בשירות.

## פתרון תקלות

| מה רואים | סיבה סבירה | מה עושים |
|---|---|---|
| "Missing setting" | חסר ערך ב-`.env` | מעתיקים מ-`env.example` וממלאים |
| "התקלה אצלנו" (500) | ל-Service Account אין הרשאת קריאה | מריצים `./deploy.sh`, שמחזיר את ההרשאה. נמדד: ההרשאה נכנסת לתוקף תוך שניות |
| "הקובץ עדיין לא הועלה" (404) | הקובץ חסר או ששמו שונה | בודקים `gcloud storage ls "gs://$BUCKET_NAME/" --project "$PROJECT"` |
| "יש כרגע תקלה זמנית" (503) | תקלה ב-GCS, חריגה לא צפויה או החלפה באמצע קריאה | הדף מנסה שוב לבד. אם זה נמשך, בודקים לוגים |
| "לא הצלחנו לקרוא את הקובץ" (422) | קובץ בינארי, קידוד לא מוכר או CSV שבור | קוראים את הפירוט בדף ומחליפים את הקובץ |
| טקסט משובש עם הערת `cp1255` | הקובץ לא באמת ב-cp1255 | שומרים מחדש כ-UTF-8 |
| הספירה לאחור לא זזה | הלשונית מוסתרת, וזו התנהגות מכוונת | חוזרים ללשונית |
| "הבדיקה האוטומטית נעצרה" | עברו 40 ניסיונות בלשונית | לוחצים "נסו שוב" |
| התוכן לא התעדכן | השירות תמיד קורא מחדש, אז כנראה הקובץ לא הוחלף | משווים `generation` בדף מול `gcloud storage objects describe` |
| פריסה נחסמה ב-"Deploy blocked" | `pytest` נכשל | מתקנים את הבדיקות. לא עוקפים את ה-hook |
| `add-iam-policy-binding` נכשל ב-400 | Service Account חדש עוד לא הופץ | `deploy.sh` מנסה שוב לבד (L-002) |
| שם ה-Bucket תפוס | שם Bucket ייחודי בכל Google Cloud | בוחרים שם אחר ב-`.env` |

## פירוק

**פעולות בלתי הפיכות.** הן מוחקות את השירות ואת הקבצים, ועוצרות עלויות:

```bash
gcloud run services delete "$SERVICE" --region "$REGION" --project "$PROJECT"
```
```bash
gcloud storage rm -r "gs://$BUCKET_NAME" --project "$PROJECT"
```
```bash
gcloud iam service-accounts delete "$SERVICE@$PROJECT.iam.gserviceaccount.com" --project "$PROJECT"
```
