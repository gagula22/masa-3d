"""Verify each video is actually embeddable.
For Vimeo: many are unlisted with domain privacy - mark these as broken.
For YouTube: most are fine, but check anyway.
"""
import json
import urllib.request
import urllib.parse
import concurrent.futures
import time
from pathlib import Path

HERE = Path(__file__).parent
VIDEOS_JSON = HERE / "videos.json"
REPORT = HERE / "verification_report.json"


def check_youtube(vid):
    """Returns (status, title_or_error). status in: 'ok', 'unavailable', 'embed_disabled', 'error'"""
    try:
        # Try the embed URL directly
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return "ok", data.get("title", "")
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return "embed_disabled", str(e)
        if e.code == 404:
            return "unavailable", "404"
        return "error", f"HTTP {e.code}"
    except Exception as e:
        return "error", f"{type(e).__name__}: {e}"


def check_vimeo(vid):
    """Vimeo oEmbed - returns ok if public/unlisted-with-embed-allowed, error if domain-locked."""
    try:
        url = f"https://vimeo.com/api/oembed.json?url=https://vimeo.com/{vid}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            # If the html field contains an iframe, it's embeddable
            html = data.get("html", "")
            if "iframe" in html:
                return "ok", data.get("title", "")
            return "embed_disabled", "no iframe in oembed response"
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return "embed_disabled", "private/domain-locked"
        if e.code == 404:
            return "unavailable", "404"
        return "error", f"HTTP {e.code}"
    except Exception as e:
        return "error", f"{type(e).__name__}: {e}"


def check_one(video):
    if video["platform"] == "youtube":
        status, info = check_youtube(video["video_id"])
    elif video["platform"] == "vimeo":
        status, info = check_vimeo(video["video_id"])
    else:
        status, info = "unknown_platform", video["platform"]
    return video["id"], video["platform"], video["video_id"], status, info


def main():
    data = json.load(open(VIDEOS_JSON, encoding="utf-8"))
    videos = data["videos"]
    print(f"Verifying {len(videos)} videos in parallel...")

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(check_one, v) for v in videos]
        for i, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            results.append(fut.result())
            if i % 25 == 0:
                print(f"  ... {i}/{len(videos)}")

    # Stats
    from collections import Counter
    by_status = Counter(r[3] for r in results)
    print("\n=== Verification results ===")
    for s, c in by_status.most_common():
        print(f"  {s}: {c}")

    # Build broken list
    broken = [r for r in results if r[3] != "ok"]
    print(f"\n=== Broken videos ({len(broken)}) ===")
    for vid_id, platform, video_id, status, info in broken:
        print(f"  id={vid_id} [{platform}:{video_id}] {status}: {info[:60]}")

    # Save report
    REPORT.write_text(json.dumps({
        "total": len(videos),
        "by_status": dict(by_status),
        "results": [
            {"id": r[0], "platform": r[1], "video_id": r[2], "status": r[3], "info": r[4]}
            for r in results
        ],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nReport saved: {REPORT}")


if __name__ == "__main__":
    main()
