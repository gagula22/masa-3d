# אתר הקורס — מערכת רענון דינמית

## הבעיה שנפתרה

לפני התיקון: רשימת 159 הסרטונים הייתה **קשיחה בתוך ה־HTML**. כשהמורה החליף/הסיר סרטונים ב־YouTube או הזיז קישורים ב־Discord — האתר נשבר כי ה־video IDs לא היו תקפים.

לאחר התיקון: ה־HTML טוען רשימה דינמית מקובץ `videos.json`. הקובץ נוצר על־ידי סקריפט (`refresh.py`) שמושך **ישירות מערוץ ה־YouTube של המורה** (@Adamantcapital) — בלי תלות ב־Discord.

## ארכיטקטורה

```
                          ┌──────────────────┐
                          │  YouTube Channel  │
                          │  @Adamantcapital  │
                          └────────┬─────────┘
                                   │ yt-dlp
                                   ▼
┌──────────────────┐      ┌──────────────────┐
│ Discord scrape   │─────▶│   refresh.py      │
│ (legacy Vimeo    │      │  (סקריפט מיזוג)   │
│  + early YouTube)│      └────────┬─────────┘
└──────────────────┘               │
                                   ▼
                          ┌──────────────────┐
                          │   videos.json     │
                          │ (source of truth) │
                          └────────┬─────────┘
                                   │ fetch()
                                   ▼
                          ┌──────────────────┐
                          │   index.html      │
                          │  (האתר במחשב/    │
                          │   GitHub Pages)   │
                          └──────────────────┘
```

## איך לרענן את רשימת הסרטונים

### כשהמורה מעלה סרטונים חדשים / משנה הגדרות:

```bash
cd "C:\Users\user\Documents\בנית אתר\website"
python refresh.py
```

זה:
1. מושך את הרשימה העדכנית מ־YouTube (`@Adamantcapital`)
2. מצרף את סרטוני ה־Vimeo הישנים מ־Discord
3. מסווג לפי נושאים
4. כותב `videos.json` חדש

### אם אין אינטרנט / רוצה להשתמש בנתונים שכבר ירדו:

```bash
python refresh.py --offline
```

## איך לפרסם את העדכון

### אופציה 1: GitHub Pages (מומלץ — `gagula22.github.io`)

```bash
# בתיקיית הריפו של GitHub Pages:
cp videos.json index.html /path/to/gagula22.github.io/
cd /path/to/gagula22.github.io/
git add videos.json index.html
git commit -m "Refresh videos"
git push
```

המבקרים יראו את הסרטונים החדשים מיידית. ה־HTML משתמש ב־cache-bust יומי
אוטומטית, כך שהדפדפן לא יציג רשימה ישנה.

### אופציה 2: בדיקה מקומית

```bash
cd "C:\Users\user\Documents\בנית אתר\website"
python -m http.server 8765
# פתח בדפדפן: http://localhost:8765/
```

**חשוב:** **אסור** לפתוח את `index.html` ישירות דרך `file://` — דפדפנים
חוסמים `fetch()` מקבצים מקומיים. תמיד דרך `http://` (שרת מקומי או GitHub Pages).

## טיפול בסרטונים שבורים (Graceful Fallback)

אם YouTube/Vimeo חוסם את ההטמעה (Embed) של סרטון מסוים — האתר מציג
אוטומטית הודעה ידידותית עם **כפתור פתיחה ישירה ב־YouTube/Vimeo**. המשתמש
לא רואה "שגיאה לבנה" אלא חוויית נפילה הגיונית.

## איזה סרטונים נכללים?

הסקריפט מתחזק את הרשימה כלהלן:

| מקור | כללים | סה"כ |
|---|---|---|
| YouTube — מ־Discord | תמיד נכללים (זוהו כשיעורים) | 106 |
| YouTube — חדשים מהערוץ | רק שיעורים ≥ 30 דקות | + |
| Vimeo — מ־Discord | תמיד נכללים | 44 |
| YouTube shorts (פחות מ־30 דק') | **לא נכללים** (תוכן שיווקי) | — |

**סה"כ כרגע:** 156 שיעורים, ב־14 קטגוריות תוכן.

## קבצים בתיקיית `website/`

| קובץ | תפקיד |
|---|---|
| `index.html` | האתר עצמו (מקבל JSON דינמית) |
| `videos.json` | מקור הנתונים הרשמי — מתעדכן בכל `refresh.py` |
| `refresh.py` | סקריפט הרענון |
| `patch_html.py` | פונקציה שהוסיפה את הלוגיקה הדינמית ל־HTML |
| `yt_channel_raw.json` | תוצר ביניים של yt-dlp (נשמר ל־offline mode) |
| `README.md` | המסמך הזה |

## דרישות מערכת

- Python 3.10+
- `yt-dlp` (מותקן: `pip install yt-dlp`)
- חיבור אינטרנט (כשמריצים בלי `--offline`)

## הערות לעתיד

### שיפורים אפשריים:

1. **רענון אוטומטי** — להגדיר Task Scheduler ב־Windows שירוץ `refresh.py` פעם ביום, ובאמצעות `git push` יעלה את ה־JSON המעודכן לאתר.
2. **גיבוי תאריכים** — סרטונים חדשים מהערוץ לא מקבלים תאריך (כי `--flat-playlist` לא מחזיר אותו). אפשר להוסיף קריאת `oembed` לכל אחד כדי לקבל תאריך פרסום מדויק.
3. **חיבור Vimeo channel** — אם המורה מעלה היום ל־Vimeo נוסף, אפשר להוסיף סקרייפר גם לערוץ Vimeo שלו.

## בדיקה ש־הכל עובד

```bash
cd "C:\Users\user\Documents\בנית אתר\website"
python -m http.server 8765
# פתח בדפדפן: http://localhost:8765/
# Console צריך להראות: "Loaded 156 videos. Last updated: 2026-..."
```
