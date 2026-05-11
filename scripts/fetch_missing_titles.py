"""Fetch full YouTube titles for any video whose title is truncated with '...'.
Stores in fetched_titles.json so refresh.py can use them."""
import json
import urllib.request
import urllib.parse
import time
import concurrent.futures
from pathlib import Path

HERE = Path(__file__).parent
PROJECT = HERE.parent
VIDEOS_JSON = HERE / "videos.json"
FT_PATH = PROJECT / "fetched_titles.json"


def fetch(vid):
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return vid, data.get("title", "")
    except Exception as e:
        return vid, f"[ERROR: {type(e).__name__}: {e}]"


def main():
    videos = json.load(open(VIDEOS_JSON, encoding="utf-8"))["videos"]
    ft = json.load(open(FT_PATH, encoding="utf-8")) if FT_PATH.exists() else {}

    # Find videos that need fetching: truncated title AND not yet in cache
    to_fetch = []
    for v in videos:
        if v["platform"] != "youtube":
            continue
        key = f"yt:{v['video_id']}"
        title = v.get("title", "")
        cached = ft.get(key, "")
        # Re-fetch if truncated AND no good cached version
        if title.endswith("..."):
            if not cached or cached.startswith("[ERROR") or cached.endswith("..."):
                to_fetch.append(v["video_id"])

    print(f"Fetching {len(to_fetch)} titles in parallel...")
    fetched_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(fetch, vid): vid for vid in to_fetch}
        for i, fut in enumerate(concurrent.futures.as_completed(futs), 1):
            vid, title = fut.result()
            ft[f"yt:{vid}"] = title
            fetched_count += 1
            if i % 10 == 0:
                print(f"  ... {i}/{len(to_fetch)}")

    FT_PATH.write_text(json.dumps(ft, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for k, v in ft.items() if not v.startswith("[ERROR"))
    print(f"\nSaved {FT_PATH.name}: {ok}/{len(ft)} valid titles, {fetched_count} new")


if __name__ == "__main__":
    main()
