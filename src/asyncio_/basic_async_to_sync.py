import asyncio


async def test():
    return "Hello"

# Running the async function as sync
asyncio.get_event_loop().run_until_complete(test())
