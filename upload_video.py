
import os
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

credentials = Credentials(
    token=None,
    refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.environ["YOUTUBE_CLIENT_ID"],
    client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
    scopes=SCOPES,
)

youtube = build("youtube", "v3", credentials=credentials)

metadata_file = Path("output/metadata.json")

if metadata_file.exists():
    metadata = json.loads(
        metadata_file.read_text(encoding="utf-8")
    )
else:
    metadata = {
        "title": "Daily Brain Challenge #Shorts",
        "description": "Watch for the answer! #BrainTeaser #Shorts"
    }

title = metadata["title"][:100]
description = metadata["description"]

request = youtube.videos().insert(
    part="snippet,status",
    body={
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": "27",
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": os.environ.get("VIDEO_PRIVACY", "private")
        },
    },
    media_body=MediaFileUpload(
        "output/short.mp4",
        mimetype="video/mp4",
        resumable=True,
    ),
)

response = request.execute()
print("アップロード成功:", response["id"])
print("タイトル:", title)
