"""
Runs on a schedule (every 5 hours via GitHub Actions) to:
  fetch latest, not-yet-posted cybersecurity news
  -> generate an original script for exactly ONE story
  -> render a video
  -> upload it to YouTube, published immediately

Dedup is enforced twice:
  - before fetching (skip anything matching posted.json by link or title)
  - before marking posted (only after upload_video() returns successfully,
    so a failed render/upload never falsely marks a story as "used")
"""

import json

from fetch_security_news import fetch_latest, save_daily_batch, load_posted, mark_posted
from generate_scripts import generate_daily_batch
from render_video import render
from upload_video import get_authenticated_service, upload_video

MAX_VIDEOS_PER_RUN = 1  # per run; with a 5-hour schedule that's up to ~4-5 videos/day


def run_daily_pipeline():
    # 1. Fetch only unposted, recent headlines -- capped early to save Gemini quota
    posted_links, posted_titles = load_posted()
    items = fetch_latest(posted_links=posted_links, posted_titles=posted_titles)

    if not items:
        print("No new, unposted headlines found this run -- nothing to do.")
        return

    # Trim BEFORE generating scripts so we never burn API quota on stories we won't use
    items = items[:MAX_VIDEOS_PER_RUN]
    save_daily_batch(items)

    # 2. Generate original scripts for just these trimmed items
    scripts = generate_daily_batch()

    if not scripts:
        print("No scripts generated this run -- nothing to upload.")
        return

    # 3. Render + upload
    youtube = get_authenticated_service()

    for entry in scripts[:MAX_VIDEOS_PER_RUN]:
        title = entry["title"][:95]  # YouTube title limit safety margin
        script_text = entry["script"]
        out_file = "daily_video.mp4"

        print(f"Rendering: {title}")
        render(script_text, title_card=title, output_path=out_file)

        description = (
            f"{script_text}\n\n"
            f"Source story: {entry['source']} ({entry['source_link']})\n"
            f"#cybersecurity #infosec #techtips"
        )

        try:
            upload_video(
                youtube,
                file_path=out_file,
                title=title,
                description=description,
                publish_at=None,  # None -> uploads as public immediately
                tags=["cybersecurity", "infosec", "tech tips"],
            )
        except Exception as e:
            # Do NOT mark as posted if the upload failed -- otherwise this
            # story would be silently skipped forever on future runs.
            print(f"Upload failed for '{title}': {e}")
            raise
        else:
            # Only mark posted on confirmed success.
            mark_posted(entry["source_link"], entry["title"])


if __name__ == "__main__":
    run_daily_pipeline()
