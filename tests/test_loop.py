import asyncio
from backend.main import proactive_messaging_loop

async def main():
    task = asyncio.create_task(proactive_messaging_loop())
    await asyncio.sleep(2)
    task.cancel()

asyncio.run(main())
