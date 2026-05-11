# הגדרת גישה לאתר (Firebase Auth)

## איך זה עובד

האתר משתמש ב־**Firebase Auth של Google** — בדיוק כמו "המחברת שלי".
שתי האפליקציות חולקות את אותו פרויקט Firebase (`my-notebook-b5229`),
כך שאם אתה מחובר באחת — אתה מחובר אוטומטית גם בשנייה.

## הרשאת משתמש חדש

יש 2 רשימות שצריך לוודא:

### 1. רשימת המורשים באתר (`ALLOWED_EMAILS`)

ערוך את `index.html`, חפש את השורה:
```js
const ALLOWED_EMAILS = [
  'gagula22@gmail.com',
];
```

הוסף את המייל החדש:
```js
const ALLOWED_EMAILS = [
  'gagula22@gmail.com',
  'student1@gmail.com',     // ← כאן
  'student2@gmail.com',     // ← וכאן
];
```

### 2. דומיינים מורשים ב־Firebase Console (פעם אחת בלבד)

זה כבר מוגדר אם המחברת עובדת על `gagula22.github.io`.
אם לא — היכנס ל־[Firebase Console](https://console.firebase.google.com/) →
פרויקט `my-notebook-b5229` → Authentication → Settings → Authorized domains →
ודא ש־`gagula22.github.io` מופיע.

## תהליך עבור המשתמש החדש

1. שלח לו את הקישור לאתר
2. הוא ייכנס וייראה מסך התחברות
3. ילחץ על "התחבר עם Google"
4. ייפתח חלון של גוגל לבחירת חשבון
5. אם המייל שלו ב־`ALLOWED_EMAILS` → ייכנס לאתר
6. אם לא → יראה "גישה נדחתה" עם המייל שלו, ויוכל להתנתק ולנסות שוב

## ביטול גישה

פשוט מוחק את המייל מה־`ALLOWED_EMAILS` ב־`index.html`,
דוחף ל־GitHub Pages. הגישה תיחסם בדפדפן שלו במהלך 30 שניות
(עד שהדפדפן יקרא את העמוד מחדש).

## טכני: מה מוגן ומה לא

| תוכן | מוגן? |
|---|---|
| ממשק האתר (כפתורים, טקסטים, פריסה) | ✅ — נחסם ע"י overlay |
| רשימת השיעורים (videos.json) | ⚠️ נגיש בלינק ישיר אם יודעים את ה־URL |
| הסרטונים עצמם (YouTube/Vimeo) | ⚠️ נשלטים ע"י YouTube/Vimeo (unlisted) |

הגנה מלאה (כולל `videos.json`) תדרוש מעבר ל־Firebase Storage עם rules.
לרוב המקרים — ההגנה הנוכחית מספקת.

## איך לאלץ התנתקות

לחץ על כפתור "יציאה" שמופיע למעלה משמאל.
זה גם מתנתק מ"המחברת" (אותו Firebase session).
