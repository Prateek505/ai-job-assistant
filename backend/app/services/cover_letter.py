"""
Cover letter generator — creates tailored cover letters using LLM or template.
"""

import json
import re
from ..config import settings
from ..models import Resume, Job
from ..schemas import CoverLetterResponse


async def generate_cover_letter(resume: Resume, job: Job) -> CoverLetterResponse:
    """Generate a tailored cover letter for a specific job + resume combination."""
    if settings.OPENAI_API_KEY:
        return await _generate_with_llm(resume, job)
    return _generate_template(resume, job)


async def _generate_with_llm(resume: Resume, job: Job) -> CoverLetterResponse:
    """Use LLM to generate a professional cover letter."""
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        prompt = f"""Write a professional cover letter for this job application.

Resume:
{resume.raw_text[:2500]}

Job Title: {job.title}
Company: {job.company}
Job Description:
{job.description[:2500]}

The cover letter should:
- Be 3-4 paragraphs
- Highlight relevant skills and experience from the resume
- Show enthusiasm for the specific role and company
- Be professional but personable
- Not exceed 400 words"""

        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional career consultant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=800,
        )

        letter = response.choices[0].message.content or ""
        return CoverLetterResponse(
            cover_letter=letter,
            job_title=job.title,
            company=job.company,
        )
    except Exception:
        return _generate_template(resume, job)


def _generate_template(resume: Resume, job: Job) -> CoverLetterResponse:
    """Generate a template-based cover letter without LLM."""
    parsed = resume.parsed_json or {}
    skills = parsed.get("skills", [])[:5]
    skills_text = ", ".join(skills) if skills else "my relevant skills"

    letter = f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job.title} position at {job.company}. With my background in {skills_text}, I believe I would be a valuable addition to your team.

Throughout my career, I have developed expertise in areas directly relevant to this role. My experience has equipped me with both the technical skills and collaborative mindset needed to excel in this position. I am particularly drawn to {job.company} because of its reputation for innovation and the exciting challenges this role presents.

I am confident that my combination of technical proficiency and problem-solving abilities makes me an ideal candidate for this position. I would welcome the opportunity to discuss how my skills and experience align with your team's needs.

Thank you for considering my application. I look forward to the opportunity to speak with you further.

Best regards,
[Your Name]"""

    return CoverLetterResponse(
        cover_letter=letter,
        job_title=job.title,
        company=job.company,
    )
