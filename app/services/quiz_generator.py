import json
import re

from openai import OpenAI

from app.config import OPENAI_MODEL_NAME


class QuizGeneratorService:
    def __init__(self):
        self.client = OpenAI()

    def generate_quiz(
        self,
        topic: str,
        difficulty: str,
        num_questions: int,
        context_chunks: list[dict],
    ) -> list[dict]:
        prompt = self._build_prompt(
            topic=topic,
            difficulty=difficulty,
            num_questions=num_questions,
            context_text=self._build_context_text(context_chunks),
        )

        response = self.client.responses.create(
            model=OPENAI_MODEL_NAME,
            input=prompt,
        )
        return self._parse_quiz_json(response.output_text)

    def _build_context_text(self, context_chunks: list[dict]) -> str:
        parts = []

        for index, chunk in enumerate(context_chunks, start=1):
            parts.append(
                f"""
[Source {index}]
File: {chunk['file_path']}
Chunk: {chunk['chunk_index']}
Type: {chunk.get('chunk_type', 'text')}
Symbol: {chunk.get('symbol_name', '')}

{chunk['content']}
""".strip()
            )

        return "\n\n".join(parts)

    def _build_prompt(
        self,
        topic: str,
        difficulty: str,
        num_questions: int,
        context_text: str,
    ) -> str:
        return f"""
Create a quiz for a beginner learning from this repository.

Use only the repository context below.

Requirements:
- Write in English.
- Create exactly {num_questions} questions.
- Difficulty: {difficulty}.
- Topic: {topic}.
- Each question must have exactly 4 options.
- Only one option must be correct.
- correct_answer must exactly match one option.
- Add a short explanation for each answer.
- Do not invent files, functions, metrics, models, or implementation details.

Return only valid JSON in this format:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Option A",
      "explanation": "Short explanation"
    }}
  ]
}}

Repository context:
{context_text}
"""

    def _parse_quiz_json(self, raw_text: str) -> list[dict]:
        raw_text = raw_text.strip()

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
            if not match:
                raise ValueError("The model did not return valid quiz JSON.")
            data = json.loads(match.group(0))

        questions = data.get("questions")

        if not isinstance(questions, list):
            raise ValueError("Quiz JSON does not contain a valid questions list.")

        return questions
