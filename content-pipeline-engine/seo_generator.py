"""Simple editable metadata suggestions; no ranking or SEO guarantee."""
import re


def generate_seo_package(metadata):
    title = metadata["title"]
    words = list(dict.fromkeys(re.findall(r"[a-zA-Z0-9]+", title.lower())))
    return {"seo_title": title, "hashtags": ["#" + word for word in words[:4]],
            "keywords": words[:8], "needs_editorial_review": True}
