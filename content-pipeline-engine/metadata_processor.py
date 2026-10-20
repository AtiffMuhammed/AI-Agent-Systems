"""Build draft metadata from a filename; does not read media contents."""
from pathlib import Path


def extract_metadata(video_name):
    if not isinstance(video_name, str) or not video_name.strip():
        raise ValueError("Video name must be a non-empty string.")
    title = Path(video_name.strip()).stem.replace("_", " ").replace("-", " ").strip()
    if not title:
        raise ValueError("Video name must have a title.")
    return {"title": title, "description": f"Draft description for {title}.",
            "category": "Video", "language": "English",
            "source": "filename-template"}
