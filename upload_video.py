"""
Uploads a video to YouTube.

Credentials are loaded from environment variables so this can run headless
in GitHub Actions (no browser, no local token.pickle file needed):
  YOUTUBE_CLIENT_ID
  YOUTUBE_CLIENT_SECRET
  YOUTUBE_REFRESH_TOKEN

For LOCAL runs, you can still set these same env vars, or fall back to the
old token.pickle flow by calling get_authenticated_service_local() instead.

Usage:
  python upload_video.py --file video.mp4 --title "..." --description "..."
"""

import argparse
import os

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_authenticated_service():
    """Build credentials from environment variables (works in GitHub Actions)."""
    creds = Credentials(
        token=None,  # force a refresh on first use
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)


def upload_video(youtube, file_path, title, description, publish_at=None, tags=None):
    """
    publish_at: ISO 8601 UTC timestamp, e.g. '2026-07-06T09:00:00Z'
    If provided, video is uploaded as private and scheduled to go public at that time.
    If omitted, video is uploaded as public immediately.
    """
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": "28",  # Science & Technology
        },
        "status": {
            "selfDeclaredMadeForKids": False,
        }
    }

    if publish_at:
        body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = publish_at
    else:
        body["status"]["privacyStatus"] = "public"

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")

    print(f"Upload complete. Video ID: {response['id']}")
    print(f"URL: https://youtube.com/watch?v={response['id']}")
    return response


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Path to video file")
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--publish_at", default=None, help="ISO 8601 UTC, e.g. 2026-07-06T09:00:00Z")
    parser.add_argument("--tags", nargs="*", default=[])
    args = parser.parse_args()

    yt = get_authenticated_service()
    upload_video(
        yt,
        file_path=args.file,
        title=args.title,
        description=args.description,
        publish_at=args.publish_at,
        tags=args.tags,
    )
