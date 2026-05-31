import asyncio, sys, traceback
sys.path.insert(0, r"c:\JOB AI\backend")

async def main():
    try:
        from app.config import settings
        from app.services.resume_parser import parse_resume_file, extract_structured_data
        
        print(f"OpenAI Key Configured: {bool(settings.OPENAI_API_KEY)}")
        if not settings.OPENAI_API_KEY:
            print("ERROR: OPENAI_API_KEY is not set in environment!")
            return
            
        print("Parsing PDF...")
        raw_text = parse_resume_file(r"c:\JOB AI\Prateek_Resume.pdf", "pdf")
        print(f"Parsed {len(raw_text)} chars.")
        
        if not raw_text or raw_text.startswith("[PDF parsing error"):
            print("PDF Parse Error:", raw_text)
            return

        print("Testing LLM Extraction...")
        data = await extract_structured_data(raw_text)
        print("Extraction Output Keys:", data.keys())
        print("Skills found:", data.get('skills', [])[:5])
        print("Experience Count:", len(data.get('experience', [])))
        
        print("\n✅ OpenAI Test Passed!")
    except Exception as e:
        traceback.print_exc()

asyncio.run(main())
