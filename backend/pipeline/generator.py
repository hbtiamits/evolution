import anthropic
import json
import os
from typing import Optional
from dotenv import load_dotenv

from .fetcher import Article

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

COURSE_GENERATION_PROMPT = """You are an expert AI educator. Given the following research article or content, generate a structured mini-course that teaches the key concepts in a clear, engaging way.

Article Title: {title}
Article Summary: {summary}
Source URL: {url}

Generate a mini-course with the following JSON structure (respond with JSON only, no markdown):
{{
  "title": "Course title (engaging, learner-focused)",
  "summary": "2-3 sentence course overview explaining what the learner will understand",
  "difficulty": "beginner | intermediate | advanced",
  "estimated_minutes": 15,
  "modules": [
    {{
      "order": 1,
      "title": "Module title",
      "content": "Detailed explanation of the concept (3-5 paragraphs). Be clear and educational.",
      "key_takeaways": ["takeaway 1", "takeaway 2", "takeaway 3"]
    }}
  ]
}}

Requirements:
- Generate 3 to 5 modules
- Each module should build on the previous one
- Use plain language, avoid unnecessary jargon
- Make it practical and applicable
- Keep total estimated reading time around 15-20 minutes
"""


def generate_course(article: Article) -> Optional[dict]:
    prompt = COURSE_GENERATION_PROMPT.format(
        title=article.title,
        summary=article.summary,
        url=article.url,
    )

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # Strip markdown code block if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    course_data = json.loads(raw)
    course_data["source_url"] = article.url
    course_data["source_title"] = article.title
    course_data["domain"] = article.domain

    return course_data
