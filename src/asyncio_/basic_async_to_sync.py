import asyncio


async def test() -> str:
    return "Hello"

# Running the async function as sync
asyncio.get_event_loop().run_until_complete(test())
