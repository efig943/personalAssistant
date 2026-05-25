import asyncio
from backend.services.time_service import extract_proposed_time
async def main():
    res = await extract_proposed_time("2pm on Tuesday")
    print(res)

if __name__ == "__main__":
    asyncio.run(main())
