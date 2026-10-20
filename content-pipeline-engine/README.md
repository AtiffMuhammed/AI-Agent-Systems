# Content metadata draft

Generate an editable draft from a filename without opening the video.

```bash
python content-pipeline-engine/main.py "ESP32_workflow_demo.mp4"
python content-pipeline-engine/main.py "ESP32_workflow_demo.mp4" --output /path/to/draft.json
```

The filename stem becomes a title; simple word extraction produces candidate hashtags and keywords. Output includes `source: "filename-template"` and `needs_editorial_review: true`.

The default output is `content-pipeline-engine/.local/content-package.json`. The tracked sample is not overwritten. This does not inspect video/audio, use AI, guarantee SEO performance, or upload anything. Review all suggestions before publishing. A practical next step is a batch CSV input with per-row validation and tests.
