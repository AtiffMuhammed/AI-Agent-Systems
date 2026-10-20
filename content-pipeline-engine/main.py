import argparse
import json
from pathlib import Path

from metadata_processor import extract_metadata
from seo_generator import generate_seo_package

DEFAULT_OUTPUT = Path(__file__).resolve().parent / ".local" / "content-package.json"


def process_video(video_name, output_path=None):
    metadata = extract_metadata(video_name)
    output = {"video": video_name, "metadata": metadata,
              "seo": generate_seo_package(metadata)}
    target = Path(output_path) if output_path is not None else DEFAULT_OUTPUT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


def main():
    parser = argparse.ArgumentParser(description="Draft metadata from a video filename.")
    parser.add_argument("video_name")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = process_video(args.video_name, args.output)
    except (ValueError, OSError) as error:
        parser.exit(2, f"Content error: {error}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
