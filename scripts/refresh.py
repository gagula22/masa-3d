"""Refresh videos.json from the trader's YouTube channel + existing Vimeo data.

This is the SOURCE OF TRUTH script. Run it whenever:
- The trader uploads new videos to YouTube
- Existing videos get retitled / removed
- You want the website to reflect the current state

Output: videos.json (consumed by index.html via fetch).

Usage:
    python refresh.py            # fetch fresh from YouTube
    python refresh.py --offline  # use cached yt_channel_raw.json (no network)
"""
import json
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime

HERE = Path(__file__).parent
PROJECT = HERE.parent

YOUTUBE_CHANNEL = "https://www.youtube.com/@Adamantcapital/videos"
RAW_FILE = HERE / "yt_channel_raw.json"
LEGACY_CH1 = PROJECT / "discord_ch1_videos.json"
LEGACY_CH2 = PROJECT / "discord_ch2_videos.json"
FETCHED_TITLES = PROJECT / "fetched_titles.json"
OUT = HERE / "videos.json"

# Categorization rules (same as before — first match wins)
CATEGORIES = [
    ("שיעורי TPO", "TPO", [r"\bTPO\b", r"\btpo\b"]),
    ("יומן מסחר", "בניית/כתיבת יומן",
     [r"יומן", r"מעבר על יומנ", r"כותב יומ", r"לכתוב יומ", r"וכתיבת יומ"]),
    ("וויקוף ופאזות", "פאזה A", [r"פאזה ?A", r"פאזות ?A"]),
    ("וויקוף ופאזות", "פאזות B/C/D",
     [r"פאזה ?B", r"פאזה ?C", r"פאזה ?D", r"פאזות ?B"]),
    ("וויקוף ופאזות", "וויקוף - כללי",
     [r"וויקוף", r"ויקוף", r"שלב השני", r"שלב הראשון", r"מתי זה השל",
      r"שאר הפאזות", r"פאזות"]),
    ("ווליום", "ניתוח ווליום",
     [r"ווליום", r"וליום", r"\bvolume\b", r"שיעור על וול"]),
    ("ניהול סיכונים", "סטופ לוס",
     [r"סטופ ?לוס", r"stop ?loss", r"מציבים סטופ", r"מציב סטופ", r"איפה סטופ"]),
    ("ניהול סיכונים", "יחס סיכון/סיכוי",
     [r"יחס[ ]?סיכ", r"סיכון[ /]סיכוי", r"יחידת סיכון", r"חיסכון סיכוי"]),
    ("ניהול סיכונים", "ניהול עסקאות",
     [r"לקיחת עסקה", r"ניהול עסק", r"שתי עסקאות", r"להחזיק שני עסקאות",
      r"לקחית עסקה", r"לקחנו עסקה", r"לוקח עסקה", r"עסקאות נכשלו",
      r"עסקה נ?כ?שלה", r"כניסה לעסקה", r"כיניסה לעסקה", r"ניתחו עסקה",
      r"חיזוק עסקה", r"איך נכנסים", r"צ'?ק[ ]?ליסט", r"צק ?ך?ליסט",
      r"עסקאות לא טובות", r"קבלת החלטה"]),
    ("ניהול סיכונים", "צמצום הפסדים",
     [r"צמצום הפסד", r"צימצום הפסד", r"הפסדים"]),
    ("פסיכולוגיה ומנטליות", "פומו (FOMO)", [r"פומו", r"\bFOMO\b", r"\bfomo\b"]),
    ("פסיכולוגיה ומנטליות", "מנטליות וגישה",
     [r"מנטליות", r"מנטלי", r"אמוציונאלי", r"מבולבלים", r"דעות של אחרים",
      r"שינויים מנטל", r"תועדתי", r"החלק התודע", r"תוודעתי",
      r"מבולבול", r"נקודות הרגישות"]),
    ("סטאפים והזדמנויות", "זיהוי סטאפים",
     [r"סטאפ", r"\bsetup\b", r"זיהוי הזדמנ"]),
    ("השקעות", "השקעות וניהול תיק",
     [r"השקעות", r"ניהול השקעות", r"חברות נוטס", r"תשואה ללא סיכון",
      r"תיק השקע"]),
    ("באק טסטים", "באק טסטים",
     [r"באק[ ]?טסט", r"בקט טסט", r"\bbacktest\b", r"באקטסט"]),
    ("ניתוח שוק וסקירה", "מעבר על השוק",
     [r"מעבר על השוק", r"מה שקורה בשוק", r"מה ?ש?קורה בו",
      r"השוק בטירוף", r"פירוק השוק", r"עברנו על השוק",
      r"מעבר על העסקאת שוק", r"קריאה? של השוק", r"כיוןן שוק", r"כיוון שוק",
      r"שוק יומי", r"לדבר על השוק", r"שוק מטורף", r"סדר בגרף"]),
    ("ניתוח שוק וסקירה", "נקודות מימוש ותהליכים",
     [r"נקודות מימוש", r"תהליך", r"תהליכים", r"מימוש"]),
    ("ניתוח שוק וסקירה", "מעגליות ותנועת הכסף",
     [r"מעגליות", r"תנועת הכסף", r"חוזקת", r"חושלת"]),
    ("שאלות ותשובות", "שאלות ותשובות",
     [r"שאלות[ ]?תשובות", r"שאלות[ ]?-? ?תשובות", r"4 שאלות", r"שאלות חשובות"]),
    ("אסטרטגיה ותכנון", "אסטרטגיה ותכנית מסחר",
     [r"אסטרגט", r"אסטרטגי", r"תוכנית מסחר", r"חידוד האסטרטג",
      r"בונים נכון את התוכנית", r"תכנית מסחר"]),
    ("אסטרטגיה ותכנון", "טווחי זמן",
     [r"טווחי הזמן", r"טווח זמן", r"שילוב.*טווח"]),
    ("תיאוריה ויסודות", "תיאוריה",
     [r"מה זה בכלל מסחר", r"מה זה מסחר", r"מסחר ?\?",
      r"תיאורתי", r"תיאוריה", r"הסבר תיאורת"]),
    ("תיאוריה ויסודות", "סיכון/סבלנות/חוקים",
     [r"סבלנות", r"חוקים", r"סרגל להצלחה"]),
    ("דוחות ואירועי שוק", "דוחות מאקרו",
     [r"דוח הורד", r"דוח ריבית", r"ריבית", r"\bFED\b"]),
    ("לייב מסחר יומי", "הקלטת לייב יומי",
     [r"לייב מסחר", r"לייב סגור", r"לייב השקה", r"הקלטה של", r"לייב של",
      r"לייב תאריך", r"^לייב", r"חוזים", r"הצצה לשיעור לייב", r"שיעור לייב",
      r"שיעור מסחר תאריך", r"החברה הקישור לשיעור של היום",
      r"רצינו לקחת עסקה לא יצא"]),
    ("שיעורי יום חמישי", "סקירה / שיחות חופשיות",
     [r"יום חמישי", r"של יום חמישי", r"שיעור.{0,30}חמישי"]),
    ("שיעור שבועי", "יום שני", [r"יום שני", r"של יום שני"]),
    ("שונות", "תוכן משולב",
     [r"שיעור.{1,30}על\b", r"דיברנו על", r"עברנו על", r"מדברים על"]),
]


def categorize(title: str):
    text = (title or "") + " | "
    for topic, sub, patterns in CATEGORIES:
        for p in patterns:
            if re.search(p, text, re.IGNORECASE):
                return topic, sub
    return "שונות", "תוכן כללי / לא מסווג"


def fetch_youtube_channel():
    """Run yt-dlp to fetch the latest channel listing."""
    print(f"[1/4] Fetching YouTube channel listing ({YOUTUBE_CHANNEL}) ...")
    result = subprocess.run(
        ["yt-dlp", "--flat-playlist", "--dump-single-json",
         "--no-warnings", YOUTUBE_CHANNEL],
        capture_output=True, text=True, encoding="utf-8", timeout=300,
    )
    if result.returncode != 0:
        print("yt-dlp failed:", result.stderr[:500])
        sys.exit(1)
    RAW_FILE.write_text(result.stdout, encoding="utf-8")
    print(f"      -> {RAW_FILE.name}")
    return json.loads(result.stdout)


def load_legacy_dates():
    """Build {video_id: date} from existing Discord scrape data (for dates)."""
    dates = {}
    for f in (LEGACY_CH1, LEGACY_CH2):
        if not f.exists():
            continue
        for v in json.load(open(f, encoding="utf-8")):
            src = v.get("s", "")
            if src.startswith("yt:"):
                dates[src[3:]] = v.get("d", "")
            elif src.startswith("vimeo:"):
                dates[src[6:]] = v.get("d", "")
    return dates


def load_full_titles():
    """Load oEmbed-fetched full titles."""
    if not FETCHED_TITLES.exists():
        return {}
    out = {}
    for k, v in json.load(open(FETCHED_TITLES, encoding="utf-8")).items():
        if v and not v.startswith("[ERROR"):
            if k.startswith("yt:"):
                out[k[3:]] = v
    return out


def load_legacy_categorization():
    """Pre-existing categorization from Discord scrape (we already curated these)."""
    cat_by_id = {}
    for f in (LEGACY_CH1, LEGACY_CH2):
        if not f.exists():
            continue
        for v in json.load(open(f, encoding="utf-8")):
            src = v.get("s", "")
            ttl = (v.get("ttl") or "").strip()
            if not src:
                continue
            cat_by_id[src] = ttl
    return cat_by_id


# Duration threshold: videos shorter than this are likely shorts/marketing
LESSON_MIN_DURATION = 30 * 60  # 30 minutes


def load_legacy_youtube():
    """Return {video_id: legacy_title} for all YouTube videos in scrape."""
    by_id = {}
    for f in (LEGACY_CH1, LEGACY_CH2):
        if not f.exists():
            continue
        for v in json.load(open(f, encoding="utf-8")):
            src = v.get("s", "")
            if src.startswith("yt:"):
                ttl = (v.get("ttl") or "").strip()
                if ttl in ("", "Vimeo"):
                    ttl = ""
                by_id[src[3:]] = ttl
    return by_id


def build_videos_json(channel_data, dates_by_id, full_titles):
    """Build merged list:
    - ALL legacy YouTube videos (verified lessons, even if now unlisted)
    - NEW long-form YouTube videos from channel (>=30min)
    - ALL legacy Vimeo videos.
    """
    legacy_yt = load_legacy_youtube()
    channel_by_id = {e["id"]: e for e in channel_data.get("entries", []) if e.get("id")}

    videos = []
    next_id = 1
    seen_yt = set()

    # 1. ALL legacy YouTube videos (verified lessons)
    print(f"[2/4] Adding {len(legacy_yt)} legacy YouTube videos from scrape")
    for yid, legacy_title in legacy_yt.items():
        if yid in seen_yt:
            continue
        seen_yt.add(yid)
        ch_entry = channel_by_id.get(yid, {})
        title = (full_titles.get(yid)
                 or (ch_entry.get("title") or "").strip()
                 or legacy_title
                 or f"שיעור {yid}")
        title = title.strip()
        date = dates_by_id.get(yid, "")
        duration = ch_entry.get("duration") or 0
        on_channel = yid in channel_by_id
        topic, sub = categorize(title)
        videos.append({
            "id": next_id,
            "category": topic,
            "subcategory": sub,
            "title": title,
            "date": date,
            "duration": duration,
            "platform": "youtube",
            "video_id": yid,
            "url": f"https://youtu.be/{yid}",
            "on_channel": on_channel,
        })
        next_id += 1

    # 2. NEW lessons from channel (not in scrape, >=30 min)
    new_lessons = 0
    skipped_short = 0
    for entry in channel_data.get("entries", []):
        yid = entry.get("id")
        if not yid or yid in seen_yt:
            continue
        seen_yt.add(yid)
        duration = entry.get("duration") or 0
        if duration < LESSON_MIN_DURATION:
            skipped_short += 1
            continue
        title = (full_titles.get(yid) or entry.get("title") or "").strip()
        topic, sub = categorize(title)
        videos.append({
            "id": next_id,
            "category": topic,
            "subcategory": sub,
            "title": title,
            "date": "",
            "duration": duration,
            "platform": "youtube",
            "video_id": yid,
            "url": f"https://youtu.be/{yid}",
            "on_channel": True,
        })
        next_id += 1
        new_lessons += 1
    print(f"      -> +{new_lessons} new lessons from channel, "
          f"skipped {skipped_short} shorts (<30min)")

    # 2. Vimeo videos from legacy scrape (early Discord uploads)
    vimeo_count = 0
    for f in (LEGACY_CH1, LEGACY_CH2):
        if not f.exists():
            continue
        for v in json.load(open(f, encoding="utf-8")):
            src = v.get("s", "")
            if not src.startswith("vimeo:"):
                continue
            vid = src[6:]
            title = (v.get("ttl") or "").strip()
            if title in ("Vimeo", ""):
                title = "(ללא כותרת)"
            date = v.get("d", "")
            topic, sub = categorize(title)
            videos.append({
                "id": next_id,
                "category": topic,
                "subcategory": sub,
                "title": title,
                "date": date,
                "duration": 0,
                "platform": "vimeo",
                "video_id": vid,
                "url": f"https://vimeo.com/{vid}",
                "on_channel": False,
            })
            next_id += 1
            vimeo_count += 1
    print(f"[3/4] Added {vimeo_count} legacy Vimeo videos")

    # Sort: by date ascending (newest at bottom), undated at top
    videos.sort(key=lambda v: v["date"] or "0000")

    return videos


def main():
    offline = "--offline" in sys.argv
    if offline and RAW_FILE.exists():
        print(f"[1/4] OFFLINE mode — using cached {RAW_FILE.name}")
        channel_data = json.load(open(RAW_FILE, encoding="utf-8"))
    else:
        channel_data = fetch_youtube_channel()

    dates_by_id = load_legacy_dates()
    full_titles = load_full_titles()
    videos = build_videos_json(channel_data, dates_by_id, full_titles)

    # Save with metadata
    output = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": "YouTube channel @Adamantcapital + legacy Vimeo from Discord",
        "channel_id": channel_data.get("channel_id"),
        "channel_name": channel_data.get("channel"),
        "total_videos": len(videos),
        "videos": videos,
    }
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    size_kb = OUT.stat().st_size / 1024
    print(f"[4/4] Saved {OUT.name} — {len(videos)} videos, {size_kb:.1f} KB")

    # Quick stats
    from collections import Counter
    print("\nBreakdown by category:")
    for cat, cnt in Counter(v["category"] for v in videos).most_common():
        print(f"  {cat}: {cnt}")
    print("\nBy platform:")
    for plat, cnt in Counter(v["platform"] for v in videos).most_common():
        print(f"  {plat}: {cnt}")


if __name__ == "__main__":
    main()
