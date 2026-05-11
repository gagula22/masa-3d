# 🛠️ סקריפטים לתחזוקת האתר

סקריפטים של Python לתחזוקת רשימת הסרטונים. ראה את `docs/מדריך_תחזוקה_האתר.docx` להוראות מלאות.

## דרישות

```bash
pip install yt-dlp openpyxl python-docx requests
```

## שימוש

### עדכון רשימת סרטונים (מהמקור)
```bash
python refresh.py
```
מושך את כל הסרטונים העדכניים מערוץ ה-YouTube של הסוחר (@Adamantcapital) ומאחד עם סרטוני Vimeo קיימים.

### בדיקת תקינות הסרטונים
```bash
python verify_videos.py
```
בודק שכל הסרטונים ב-videos.json עדיין נגישים (לא נמחקו / לא נעשו פרטיים).

### ניקוי סרטונים שבורים
```bash
python clean_broken.py
```
מסיר מ-videos.json את הסרטונים שבדיקת ה-verify סימנה כשבורים.

### השלמת כותרות חסרות
```bash
python fetch_missing_titles.py
```
מביא כותרות מלאות מ-YouTube oEmbed לסרטונים שכותרתם נחתכה ב-"...".

## תהליך מומלץ לעדכון

```bash
python refresh.py             # 1. מושך נתונים חדשים
python fetch_missing_titles.py # 2. משלים כותרות
python verify_videos.py        # 3. בודק תקינות
python clean_broken.py         # 4. מסיר שבורים
# 5. cp videos.json ../  (להעלאת השינוי)
# 6. git add videos.json && git commit -m "Refresh videos" && git push
```
