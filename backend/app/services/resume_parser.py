"""
Resume parser — extracts text from PDF/DOCX and structures it via LLM or fallback.
"""

import json
import re
from typing import Optional

from ..config import settings


def parse_resume_file(file_path: str, ext: str) -> str:
    """Extract raw text from a PDF or DOCX file."""
    if ext == "pdf":
        return _parse_pdf(file_path)
    elif ext == "docx":
        return _parse_docx(file_path)
    return ""


def _parse_pdf(file_path: str) -> str:
    """Extract text from a PDF using pdfplumber."""
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)
    except Exception as e:
        return f"[PDF parsing error: {e}]"


def _parse_docx(file_path: str) -> str:
    """Extract text from a DOCX using python-docx."""
    try:
        from docx import Document
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        return f"[DOCX parsing error: {e}]"


async def extract_structured_data(raw_text: str) -> dict:
    """
    Extract structured resume data (skills, experience, education, projects).
    Uses OpenAI if API key is available; otherwise falls back to keyword extraction.
    """
    if settings.OPENAI_API_KEY:
        return await _extract_with_llm(raw_text)
    return _extract_fallback(raw_text)


async def _extract_with_llm(raw_text: str) -> dict:
    """Use OpenAI to extract structured information from resume text."""
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract structured information from this resume. "
                        "Return a JSON object with keys: skills (list of strings), "
                        "technologies (list of strings), experience (list of objects with "
                        "title, company, duration), education (list of objects with degree, "
                        "institution), and projects (list of objects with name, description). "
                        "Return ONLY valid JSON, no markdown."
                    ),
                },
                {"role": "user", "content": raw_text[:4000]},
            ],
            temperature=0,
            max_tokens=1500,
        )

        content = response.choices[0].message.content or "{}"
        # Strip markdown code fences if present
        content = re.sub(r"```json\s*", "", content)
        content = re.sub(r"```\s*", "", content)
        return json.loads(content)
    except Exception as e:
        return _extract_fallback(raw_text)


def _extract_fallback(raw_text: str) -> dict:
    """
    Simple keyword-based extraction used when no LLM is available.
    Looks for common tech skills and section headers.
    """
    text_lower = raw_text.lower()

    # Common tech skills to search for
    known_skills = [
        "python", "javascript", "typescript", "react", "node.js", "java", "c++",
        "sql", "postgresql", "mongodb", "docker", "kubernetes", "aws", "azure",
        "gcp", "git", "linux", "html", "css", "fastapi", "django", "flask",
        "machine learning", "deep learning", "tensorflow", "pytorch", "nlp",
        "data science", "agile", "scrum", "rest api", "graphql", "redis",
        "celery", "rabbitmq", "ci/cd", "terraform", "ansible",
    ]
    found_skills = [s for s in known_skills if s in text_lower]

    return {
        "skills": found_skills,
        "technologies": found_skills,
        "experience": [],
        "education": [],
        "projects": [],
    }
