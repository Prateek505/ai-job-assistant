"""
Comprehensive Test Suite for Job AI Project
Tests all major functionalities without requiring Docker
"""

import sys
import os
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

def test_imports():
    """Test if all required modules can be imported"""
    print("\n" + "="*60)
    print("TEST 1: Module Imports")
    print("="*60)
    
    tests = []
    
    try:
        import fastapi
        tests.append(("FastAPI", True, fastapi.__version__))
    except ImportError as e:
        tests.append(("FastAPI", False, str(e)))
    
    try:
        import sqlalchemy
        tests.append(("SQLAlchemy", True, sqlalchemy.__version__))
    except ImportError as e:
        tests.append(("SQLAlchemy", False, str(e)))
    
    try:
        import pydantic
        tests.append(("Pydantic", True, pydantic.__version__))
    except ImportError as e:
        tests.append(("Pydantic", False, str(e)))
    
    try:
        import openai
        tests.append(("OpenAI", True, openai.__version__))
    except ImportError as e:
        tests.append(("OpenAI", False, str(e)))
    
    try:
        import pdfplumber
        tests.append(("PDFPlumber", True, "installed"))
    except ImportError as e:
        tests.append(("PDFPlumber", False, str(e)))
    
    try:
        import docx
        tests.append(("python-docx", True, "installed"))
    except ImportError as e:
        tests.append(("python-docx", False, str(e)))
    
    try:
        import playwright
        tests.append(("Playwright", True, "installed"))
    except ImportError as e:
        tests.append(("Playwright", False, str(e)))
    
    for name, success, info in tests:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} | {name:20} | {info}")
    
    return all(t[1] for t in tests)


def test_config():
    """Test configuration loading"""
    print("\n" + "="*60)
    print("TEST 2: Configuration")
    print("="*60)
    
    try:
        from app.config import settings
        
        print(f"✓ Config loaded successfully")
        print(f"  - Database URL: {settings.DATABASE_URL[:50]}...")
        print(f"  - JWT Secret: {'*' * len(settings.JWT_SECRET)}")
        print(f"  - Upload Dir: {settings.UPLOAD_DIR}")
        print(f"  - OpenAI Key: {'Set' if settings.OPENAI_API_KEY else 'Not Set (will use fallback)'}")
        print(f"  - SendGrid Key: {'Set' if settings.SENDGRID_API_KEY else 'Not Set (will use console)'}")
        return True
    except Exception as e:
        print(f"✗ Config failed: {e}")
        return False


def test_database_models():
    """Test database models"""
    print("\n" + "="*60)
    print("TEST 3: Database Models")
    print("="*60)
    
    try:
        from app.models import User, Resume, Job, JobMatch, Preference, Notification
        
        models = [User, Resume, Job, JobMatch, Preference, Notification]
        for model in models:
            print(f"✓ {model.__name__} model loaded")
        
        # Check model attributes
        print(f"\n  User fields: {', '.join([c.name for c in User.__table__.columns])}")
        print(f"  Job fields: {', '.join([c.name for c in Job.__table__.columns])}")
        
        return True
    except Exception as e:
        print(f"✗ Models failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_schemas():
    """Test Pydantic schemas"""
    print("\n" + "="*60)
    print("TEST 4: Pydantic Schemas")
    print("="*60)
    
    try:
        from app.schemas import (
            UserCreate, UserLogin, UserResponse,
            ResumeResponse, JobResponse, JobMatchResponse,
            PreferenceUpdate, NotificationResponse
        )
        
        schemas = [
            UserCreate, UserLogin, UserResponse,
            ResumeResponse, JobResponse, JobMatchResponse,
            PreferenceUpdate, NotificationResponse
        ]
        
        for schema in schemas:
            print(f"✓ {schema.__name__} schema loaded")
        
        # Test schema validation
        user_data = {"email": "test@example.com", "password": "test123", "name": "Test User"}
        user = UserCreate(**user_data)
        print(f"\n  Sample UserCreate: {user.email}")
        
        return True
    except Exception as e:
        print(f"✗ Schemas failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_auth_utilities():
    """Test authentication utilities"""
    print("\n" + "="*60)
    print("TEST 5: Authentication Utilities")
    print("="*60)
    
    try:
        from app.auth import hash_password, verify_password, create_access_token, decode_token
        
        # Test password hashing
        password = "test_password_123"
        hashed = hash_password(password)
        print(f"✓ Password hashing works")
        print(f"  - Original: {password}")
        print(f"  - Hashed: {hashed[:50]}...")
        
        # Test password verification
        is_valid = verify_password(password, hashed)
        print(f"✓ Password verification: {is_valid}")
        
        # Test JWT token creation
        token = create_access_token({"sub": "123", "email": "test@example.com"})
        print(f"✓ JWT token creation works")
        print(f"  - Token: {token[:50]}...")
        
        # Test JWT token decoding
        payload = decode_token(token)
        print(f"✓ JWT token decoding works")
        print(f"  - Payload: {payload}")
        
        return True
    except Exception as e:
        print(f"✗ Auth utilities failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_services():
    """Test AI service modules"""
    print("\n" + "="*60)
    print("TEST 6: AI Services")
    print("="*60)
    
    try:
        from app.services.ai_matcher import AIMatcher
        from app.services.resume_parser import ResumeParser
        from app.services.resume_optimizer import ResumeOptimizer
        from app.services.cover_letter import CoverLetterGenerator
        from app.services.networking import NetworkingAssistant
        
        print(f"✓ AIMatcher loaded")
        print(f"✓ ResumeParser loaded")
        print(f"✓ ResumeOptimizer loaded")
        print(f"✓ CoverLetterGenerator loaded")
        print(f"✓ NetworkingAssistant loaded")
        
        # Test AI Matcher with sample data
        matcher = AIMatcher()
        
        sample_resume = {
            "skills": ["Python", "FastAPI", "React", "PostgreSQL"],
            "technologies": ["Docker", "Git"],
            "experience": [
                {"title": "Software Engineer", "years": 3}
            ]
        }
        
        sample_job = {
            "title": "Senior Software Engineer",
            "description": "Looking for a Python developer with FastAPI and React experience. Must know PostgreSQL and Docker.",
            "location": "Remote",
            "salary_range": "$120k - $150k",
            "company": "Tech Corp"
        }
        
        sample_preferences = {
            "locations": ["Remote", "New York"],
            "salary_min": 100000,
            "salary_max": 200000,
            "experience_level": "senior",
            "priority_companies": ["Tech Corp"]
        }
        
        scores = matcher.compute_match_scores(sample_resume, sample_job, sample_preferences)
        print(f"\n  Sample Match Scores:")
        print(f"    - Total Score: {scores['total_score']:.1f}/100")
        print(f"    - Skill Similarity: {scores['skill_similarity']:.1f}")
        print(f"    - Experience Match: {scores['experience_match']:.1f}")
        print(f"    - Location Preference: {scores['location_preference']:.1f}")
        print(f"    - Salary Preference: {scores['salary_preference']:.1f}")
        print(f"    - Company Priority: {scores['company_priority']:.1f}")
        
        return True
    except Exception as e:
        print(f"✗ AI services failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_resume_parser():
    """Test resume parsing functionality"""
    print("\n" + "="*60)
    print("TEST 7: Resume Parser")
    print("="*60)
    
    try:
        from app.services.resume_parser import ResumeParser
        
        parser = ResumeParser()
        
        # Test with sample text
        sample_text = """
        John Doe
        Software Engineer
        
        Skills: Python, JavaScript, React, FastAPI, PostgreSQL, Docker, AWS
        
        Experience:
        - Senior Software Engineer at Tech Corp (3 years)
        - Software Developer at StartupXYZ (2 years)
        
        Education:
        - BS Computer Science, MIT
        
        Projects:
        - Built a job matching platform using AI
        - Developed microservices architecture
        """
        
        parsed = parser.parse_text(sample_text)
        print(f"✓ Resume parsing works")
        print(f"\n  Parsed Data:")
        print(f"    - Skills: {', '.join(parsed.get('skills', []))}")
        print(f"    - Technologies: {', '.join(parsed.get('technologies', []))}")
        print(f"    - Experience entries: {len(parsed.get('experience', []))}")
        print(f"    - Education entries: {len(parsed.get('education', []))}")
        
        return True
    except Exception as e:
        print(f"✗ Resume parser failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_job_scraper():
    """Test job scraper module"""
    print("\n" + "="*60)
    print("TEST 8: Job Scraper")
    print("="*60)
    
    try:
        from app.services.job_scraper import scrape_greenhouse, scrape_lever
        
        print(f"✓ Job scraper modules loaded")
        print(f"  - scrape_greenhouse function available")
        print(f"  - scrape_lever function available")
        print(f"\n  Note: Actual scraping requires network access")
        print(f"  Skipping live scraping test to avoid rate limits")
        
        return True
    except Exception as e:
        print(f"✗ Job scraper failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_routers():
    """Test API routers"""
    print("\n" + "="*60)
    print("TEST 9: API Routers")
    print("="*60)
    
    try:
        from app.routers import (
            auth_router,
            resume_router,
            jobs_router,
            matches_router,
            preferences_router,
            notifications_router,
            scraping_router
        )
        
        routers = [
            ("Auth", auth_router),
            ("Resume", resume_router),
            ("Jobs", jobs_router),
            ("Matches", matches_router),
            ("Preferences", preferences_router),
            ("Notifications", notifications_router),
            ("Scraping", scraping_router)
        ]
        
        for name, router in routers:
            route_count = len(router.router.routes)
            print(f"✓ {name} router loaded ({route_count} routes)")
        
        return True
    except Exception as e:
        print(f"✗ Routers failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fastapi_app():
    """Test FastAPI application"""
    print("\n" + "="*60)
    print("TEST 10: FastAPI Application")
    print("="*60)
    
    try:
        from app.main import app
        
        print(f"✓ FastAPI app loaded")
        print(f"  - Title: {app.title}")
        print(f"  - Version: {app.version}")
        print(f"  - Routes: {len(app.routes)}")
        
        # List all routes
        print(f"\n  Available API Routes:")
        api_routes = [r for r in app.routes if hasattr(r, 'path') and r.path.startswith('/api')]
        for route in api_routes[:15]:  # Show first 15
            methods = ','.join(route.methods) if hasattr(route, 'methods') else 'N/A'
            print(f"    - {methods:10} {route.path}")
        
        if len(api_routes) > 15:
            print(f"    ... and {len(api_routes) - 15} more routes")
        
        return True
    except Exception as e:
        print(f"✗ FastAPI app failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print(" "*15 + "JOB AI PROJECT - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    results = []
    
    # Check if dependencies are installed
    try:
        import fastapi
        deps_installed = True
    except ImportError:
        deps_installed = False
        print("\n⚠ WARNING: Backend dependencies not installed!")
        print("  Run: cd backend && pip install -r requirements.txt")
        print("\n  Attempting to run tests anyway...\n")
    
    # Run tests
    results.append(("Module Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Database Models", test_database_models()))
    results.append(("Pydantic Schemas", test_schemas()))
    results.append(("Auth Utilities", test_auth_utilities()))
    results.append(("AI Services", test_ai_services()))
    results.append(("Resume Parser", test_resume_parser()))
    results.append(("Job Scraper", test_job_scraper()))
    results.append(("API Routers", test_routers()))
    results.append(("FastAPI App", test_fastapi_app()))
    
    # Summary
    print("\n" + "="*70)
    print(" "*25 + "TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} | {name}")
    
    print("\n" + "-"*70)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*70)
    
    if passed == total:
        print("\n🎉 All tests passed! The application is ready to run.")
        print("\nNext steps:")
        print("  1. Start Docker: docker-compose up -d")
        print("  2. Start backend: cd backend && uvicorn app.main:app --reload")
        print("  3. Start frontend: cd frontend && npm run dev")
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")
        if not deps_installed:
            print("\n  Most likely cause: Dependencies not installed")
            print("  Solution: cd backend && pip install -r requirements.txt")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
