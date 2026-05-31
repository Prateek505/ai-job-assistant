"""
Resume Optimizer — compares a resume to a job description and suggests improvements.
Uses LLM when available, otherwise provides keyword-based suggestions.
"""

import json
import re
from ..config import settings
from ..models import Resume, Job
from ..schemas import ResumeOptimizationResponse


async def optimize_resume_for_job(resume: Resume, job: Job) -> ResumeOptimizationResponse:
    """Generate resume optimization suggestions for a specific job."""
    if settings.OPENAI_API_KEY:
        return await _optimize_with_llm(resume, job)
    return _optimize_fallback(resume, job)


async def _optimize_with_llm(resume: Resume, job: Job) -> ResumeOptimizationResponse:
    """Use LLM to analyze gaps and generate optimized resume text."""
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        prompt = f"""Analyze this resume against the job description and provide:
1. missing_keywords: keywords in the job not found in the resume
2. missing_skills: required skills the candidate may lack
3. suggestions: specific recommendations to improve the resume
4. optimized_text: rewritten resume text tailored for this job

Resume:
{resume.raw_text[:3000]}

Job Title: {job.title}
Job Description:
{job.description[:3000]}

Return ONLY valid JSON with keys: missing_keywords, missing_skills, suggestions, optimized_text."""

        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional resume consultant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
        )

        content = response.choices[0].message.content or "{}"
        content = re.sub(r"```json\s*", "", content)
        content = re.sub(r"```\s*", "", content)
        data = json.loads(content)

        return ResumeOptimizationResponse(
            missing_keywords=data.get("missing_keywords", []),
            missing_skills=data.get("missing_skills", []),
            suggestions=data.get("suggestions", []),
            optimized_text=data.get("optimized_text", resume.raw_text),
        )
    except Exception:
        return _optimize_fallback(resume, job)


def _optimize_fallback(resume: Resume, job: Job) -> ResumeOptimizationResponse:
    """Keyword-based resume optimization when no LLM is available."""
    resume_lower = resume.raw_text.lower()
    job_words = set(re.findall(r"\b[a-z]{3,}\b", job.description.lower()))
    resume_words = set(re.findall(r"\b[a-z]{3,}\b", resume_lower))

    # Important technical keywords from the job not in the resume
    stop_words = {
        "the", "and", "for", "are", "you", "our", "will", "with", "this",
        "that", "your", "have", "from", "they", "been", "more", "can",
        "about", "all", "also", "but", "not", "what", "has", "was", "who",
        "how", "may", "its", "than", "other", "into", "some", "these",
        "such", "each", "any", "work", "team", "role", "able", "must",
    }
    missing_keywords = sorted(job_words - resume_words - stop_words)[:15]

    # Identify skill-like keywords
    tech_terms = {
        "python", "javascript", "typescript", "react", "node", "docker",
        "kubernetes", "aws", "azure", "gcp", "sql", "postgresql", "mongodb",
        "redis", "graphql", "terraform", "ansible", "jenkins", "git",
        "agile", "scrum", "machine", "learning", "deep", "nlp",
        "fastapi", "django", "flask", "spring", "java", "golang",
    }
    missing_skills = sorted(tech_terms & set(missing_keywords))

    suggestions = []
    if missing_skills:
        suggestions.append(f"Add experience with: {', '.join(missing_skills[:5])}")
    if len(missing_keywords) > 5:
        suggestions.append(f"Include industry terms: {', '.join(missing_keywords[:5])}")
    suggestions.append("Tailor your summary/objective to match the job title")
    suggestions.append("Quantify your achievements with metrics where possible")

    return ResumeOptimizationResponse(
        missing_keywords=missing_keywords[:10],
        missing_skills=missing_skills[:8],
        suggestions=suggestions,
        optimized_text=resume.raw_text,  # Unchanged without LLM
    )
