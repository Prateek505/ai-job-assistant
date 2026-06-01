import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
async def test():
    try:
        engine = create_async_engine("postgresql+asyncpg://user:pass@ep-something.ap-south-1.aws.neon.tech/neondb", connect_args={"ssl": True})
        print("Engine created successfully with connect_args")
    except Exception as e:
        print(f"ERROR: {e}")
asyncio.run(test())
