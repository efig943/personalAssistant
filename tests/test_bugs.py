import asyncio
from backend.main import extract_proposed_time

async def main():
    res = await extract_proposed_time("How about next Saturday around 14:00")
    print(f"Extraction result: {res}")

asyncio.run(main())
