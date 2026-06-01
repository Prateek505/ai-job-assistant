import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
async def test():
    try:
        engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db?sslmode=require")
        async with engine.begin() as conn:
            pass
    except Exception as e:
        print(f"ERROR TYPE: {type(e)}")
        print(f"ERROR MSG: {e}")
asyncio.run(test())
