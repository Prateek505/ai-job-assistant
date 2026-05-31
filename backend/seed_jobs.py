import asyncio, sys, traceback
sys.path.insert(0, r"c:\JOB AI\backend")

async def main():
    try:
        from app.database import async_session
        from app.models import Job
        from datetime import datetime, timedelta, timezone

        jobs = [
            Job(
                title="Frontend Developer (React/Next.js)",
                company="Techify Solutions",
                description="We are looking for a skilled Frontend Developer proficient in React, Next.js, and TypeScript. You will build modern, responsive web applications and collaborate closely with our design team. Experience with Tailwind CSS and state management (Redux, Zustand) is highly desirable.",
                location="Remote",
                salary_range="$80,000 - $110,000",
                posting_date=datetime.now(timezone.utc) - timedelta(days=2),
                source="lever"
            ),
            Job(
                title="Backend Engineer (Python/FastAPI)",
                company="DataStream Inc.",
                description="Join our core engineering team to build scalable microservices using Python, FastAPI, and PostgreSQL. You must have strong experience in API design, asynchronous programming, databases, and Docker. Experience with Celery or Redis is a plus.",
                location="New York, NY (Hybrid)",
                salary_range="$100k - $140k",
                posting_date=datetime.now(timezone.utc) - timedelta(days=1),
                source="greenhouse"
            ),
            Job(
                title="Full Stack Engineer",
                company="Innovate AI",
                description="We are seeking a versatile Full Stack Engineer to support our AI products. The ideal candidate has experience with both React/TypeScript on the frontend and Python/Django or Node.js on the backend. You will work on integrating complex machine learning models into user-friendly interfaces.",
                location="San Francisco, CA",
                salary_range="$120,000 - $160,000",
                posting_date=datetime.now(timezone.utc),
                source="linkedin"
            ),
            Job(
                title="Java Developer",
                company="Enterprise Systems Corp",
                description="Looking for an experienced Java Developer to maintain and upgrade legacy enterprise systems. Strong knowledge of Java 8+, Spring Boot, SQL, and microservices architecture is required. Must be comfortable writing unit tests and performing code reviews.",
                location="Austin, TX",
                salary_range="90k-120k",
                posting_date=datetime.now(timezone.utc) - timedelta(days=5),
                source="indeed"
            )
        ]

        async with async_session() as session:
            for job in jobs:
                session.add(job)
            await session.commit()
            print("Successfully seeded 4 jobs into the database.")
            
    except Exception as e:
        traceback.print_exc()

asyncio.run(main())
