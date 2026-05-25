import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.time_service import extract_proposed_time

async def main():
    res = await extract_proposed_time("That works")
    print("Extracted:", res)

asyncio.run(main())
