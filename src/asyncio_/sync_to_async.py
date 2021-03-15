import asyncio
import time
from functools import wraps, partial


def async_wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()

        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)
    return run


# -- USAGE --

# Normal conversion to async
async_sleep = async_wrap(time.sleep)


# Decorator usage
@async_wrap
def my_async_sleep(duration):
    time.sleep(duration)
