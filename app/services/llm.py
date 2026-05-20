from openai import OpenAI

from app.config import OPENAI_MODEL_NAME


class LLMService:
    def __init__(self):
        self.client = OpenAI()

    def generate_answer(
        self,
        question: str,
        context_chunks: list[dict],
        include_check_question: bool = False,
    ) -> str:
        prompt = self._build_prompt(
            question=question,
            context_text=self._build_context_text(context_chunks),
            include_check_question=include_check_question,
        )

        response = self.client.responses.create(
            model=OPENAI_MODEL_NAME,
            input=prompt,
        )
        return response.output_text.strip()

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
        question: str,
        context_text: str,
        include_check_question: bool,
    ) -> str:
        check_question_rule = ""

        if include_check_question:
            check_question_rule = """
- End with one optional learning question in this exact format: Check question: ...
"""

        return f"""
You are a repository learning assistant.

Answer the user's question using only the repository context below.

Rules:
- Answer in English.
- Be clear, direct, and beginner-friendly.
- Do not invent files, functions, metrics, datasets, links, dependencies, or implementation details.
- If the context is not enough, say exactly what is missing.
- Mention source files naturally when they matter.
- Do not use Markdown symbols such as #, **, tables, or code fences.
- Use short paragraphs.
- Use simple numbered lines only when a list is useful.
- Do not end with offers like "If you want" or "I can also".
{check_question_rule}

Repository context:
{context_text}

User question:
{question}

Answer:
"""
