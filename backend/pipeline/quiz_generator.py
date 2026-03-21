import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

QUIZ_GENERATION_PROMPT = """You are an expert educator creating a comprehension quiz for a mini-course.

Course Title: {title}
Course Summary: {summary}

Modules:
{modules_text}

Generate a 5-question multiple-choice quiz that tests understanding of the key concepts across all modules.

Respond with JSON only (no markdown), matching this exact structure:
{{
  "questions": [
    {{
      "id": 1,
      "question": "Clear, specific question about a key concept",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_index": 0,
      "explanation": "Brief explanation of why this answer is correct and others are not"
    }}
  ]
}}

Requirements:
- Exactly 5 questions
- Each question must have exactly 4 options
- correct_index is 0-based (0, 1, 2, or 3)
- Questions should span different modules, not cluster on one topic
- Distractors (wrong answers) should be plausible but clearly distinguishable from correct answer
- Keep questions factual and based strictly on the course content
"""


def generate_quiz(course) -> list[dict]:
    modules_text = "\n\n".join(
        f"Module {m['order']}: {m['title']}\n{m['content'][:500]}..."
        for m in sorted(course.modules, key=lambda m: m["order"])
    )

    prompt = QUIZ_GENERATION_PROMPT.format(
        title=course.title,
        summary=course.summary,
        modules_text=modules_text,
    )

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    data = json.loads(raw)
    return data["questions"]
