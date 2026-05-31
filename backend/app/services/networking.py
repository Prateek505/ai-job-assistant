"""
Networking assistant — suggests relevant contacts and connection messages.
Uses LLM when available, otherwise provides template-based suggestions.
"""

from ..config import settings
from ..models import Job
from ..schemas import NetworkingResponse, NetworkingContact


async def suggest_networking(job: Job) -> NetworkingResponse:
    """Generate networking suggestions for the company of a specific job."""
    if settings.OPENAI_API_KEY:
        return await _suggest_with_llm(job)
    return _suggest_template(job)


async def _suggest_with_llm(job: Job) -> NetworkingResponse:
    """Use LLM to generate personalised networking suggestions."""
    try:
        import json, re
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        prompt = f"""For a job application at {job.company} for the role "{job.title}",
suggest 3 types of people to connect with at the company for networking.

For each person, provide:
- name: a placeholder name
- role: their likely title
- department: their department
- connection_message: a professional LinkedIn message template

Also provide 3 networking tips specific to this company/role.

Return ONLY valid JSON with keys: contacts (list), tips (list of strings)."""

        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a career networking expert."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=800,
        )

        content = response.choices[0].message.content or "{}"
        content = re.sub(r"```json\s*", "", content)
        content = re.sub(r"```\s*", "", content)
        data = json.loads(content)

        contacts = [NetworkingContact(**c) for c in data.get("contacts", [])]
        tips = data.get("tips", [])

        return NetworkingResponse(company=job.company, contacts=contacts, tips=tips)
    except Exception:
        return _suggest_template(job)


def _suggest_template(job: Job) -> NetworkingResponse:
    """Template-based networking suggestions without LLM."""
    contacts = [
        NetworkingContact(
            name="Hiring Manager",
            role=f"Engineering Manager — {job.title} team",
            department="Engineering",
            connection_message=(
                f"Hi! I'm excited about the {job.title} role at {job.company}. "
                f"I'd love to learn more about the team and the work you're doing. "
                f"Would you be open to a brief chat?"
            ),
        ),
        NetworkingContact(
            name="Team Member",
            role=f"Senior {job.title.split()[0]} Engineer",
            department="Engineering",
            connection_message=(
                f"Hello! I noticed you work at {job.company} and I'm applying "
                f"for the {job.title} position. I'd appreciate hearing about your "
                f"experience on the team."
            ),
        ),
        NetworkingContact(
            name="Recruiter",
            role="Technical Recruiter",
            department="People / Talent",
            connection_message=(
                f"Hi! I recently applied for the {job.title} role at {job.company} "
                f"and would love to connect. I believe my background could be a great fit."
            ),
        ),
    ]

    tips = [
        f"Research {job.company}'s recent news and mention it in conversations",
        "Engage with company posts on LinkedIn before reaching out",
        "Ask for informational interviews rather than directly asking about the role",
    ]

    return NetworkingResponse(company=job.company, contacts=contacts, tips=tips)
