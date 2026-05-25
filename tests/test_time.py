import asyncio
import os
import sys

# add parent directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.time_service import extract_proposed_time

async def main():
    res = await extract_proposed_time("4pm on Tuesday")
    print(res)

asyncio.run(main())
