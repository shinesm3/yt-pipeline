"""
Takes daily_news.json (from fetch_security_news.py) and generates
ORIGINAL short-form video scripts for each headline -- rewritten in
your channel's own words, never copied from the source article.

Uses Google Gemini's free-tier API (no billing required for normal use).

Requires: pip install google-genai --break-system-packages
Requires: GEMINI_API_KEY environment variable set
Get a free key at: https://aistudio.google.com/app/apikey
"""

import json
import os
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL_NAME = "gemini-2.5-flash"  # fast, free-tier friendly

SCRIPT_PROMPT = """You are writing a 30-45 second script for a faceless \
cybersecurity news/tips YouTube Short. You will be given a news headline \
and a short summary snippet.

Rules:
- Do NOT copy any wording from the summary. Explain the underlying event \
or fact entirely in your own words.
- Do NOT include exploit code, working attack techniques, or step-by-step \
instructions that could enable someone to replicate an attack. Explain \
WHAT happened and WHY it matters, not HOW to do it.
- Structure: Hook (1 sentence) -> Explanation (3-5 sentences, plain \
language, assume a general audience) -> Takeaway or practical tip (1-2 \
sentences) -> short CTA.
- Keep total length to about 100-130 words (fits 30-45 sec at normal \
speaking pace).
- Tone: clear, confident, SOC-analyst-explains-it-simply. No hype, no \
clickbait exaggeration.

Headline: {title}
Summary snippet: {summary}
Source: {source}

Output ONLY the script text, no preamble, no labels."""


def generate_script(item):
    prompt = SCRIPT_PROMPT.format(
        title=item["title"],
        summary=item["summary"],
        source=item["source"],
    )
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )
    return response.text.strip()


def generate_daily_batch(input_path="daily_news.json", output_path="daily_scripts.json"):
    with open(input_path) as f:
        items = json.load(f)

    results = []
    for item in items:
        try:
            script = generate_script(item)
            results.append({
                "title": item["title"],
                "source": item["source"],
                "source_link": item["link"],
                "script": script,
            })
            print(f"Generated script for: {item['title']}")
        except Exception as e:
            print(f"Failed on '{item['title']}': {e}")

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved {len(results)} scripts to {output_path}")
    return results


if __name__ == "__main__":
    generate_daily_batch()
