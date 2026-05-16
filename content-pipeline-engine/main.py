from metadata_processor import extract_metadata
from seo_generator import generate_seo_package
import json


def process_video(video_name):
    metadata = extract_metadata(video_name)
    seo_data = generate_seo_package(metadata)

    output = {
        "video": video_name,
        "metadata": metadata,
        "seo": seo_data
    }

    with open("sample_output.json", "w") as f:
        json.dump(output, f, indent=4)

    print("✅ Content package generated successfully")


if __name__ == "__main__":
    video = input("Enter video name: ")
    process_video(video)
