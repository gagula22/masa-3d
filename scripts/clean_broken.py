"""Remove broken/unavailable videos from videos.json based on verification report."""
import json
from pathlib import Path

HERE = Path(__file__).parent
VIDEOS_JSON = HERE / "videos.json"
REPORT = HERE / "verification_report.json"

report = json.load(open(REPORT, encoding="utf-8"))
broken_keys = {(r["platform"], r["video_id"])
               for r in report["results"]
               if r["status"] != "ok"}

print(f"Will remove {len(broken_keys)} broken videos")

data = json.load(open(VIDEOS_JSON, encoding="utf-8"))
original_count = len(data["videos"])

# Filter
kept = []
removed = []
for v in data["videos"]:
    key = (v["platform"], v["video_id"])
    if key in broken_keys:
        removed.append(v)
    else:
        kept.append(v)

# Renumber IDs
for i, v in enumerate(kept, 1):
    v["id"] = i

data["videos"] = kept
data["total_videos"] = len(kept)
data["removed_at_cleanup"] = len(removed)

# Backup original first
backup = VIDEOS_JSON.with_suffix(".bak.json")
import shutil
if not backup.exists():
    shutil.copy(VIDEOS_JSON, backup)
    print(f"Backup: {backup.name}")

VIDEOS_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                       encoding="utf-8")

print(f"\nSaved {VIDEOS_JSON.name}: {len(kept)}/{original_count} videos (removed {len(removed)})")
print(f"\nNew breakdown by category:")
from collections import Counter
import sys
for cat, cnt in Counter(v["category"] for v in kept).most_common():
    sys.stdout.buffer.write(f"  {cat}: {cnt}\n".encode("utf-8"))
print("\nBy platform:")
for plat, cnt in Counter(v["platform"] for v in kept).most_common():
    print(f"  {plat}: {cnt}")
