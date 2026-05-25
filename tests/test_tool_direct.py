import asyncio
from backend.tools.agent_tools import execute_remove_event_tool

async def main():
    res = await execute_remove_event_tool("8241224953", "", "")
    print("Result of tool:", res)

asyncio.run(main())
