import asyncio
import time
import typing as t
from functools import partial, wraps


def async_wrap(func: t.Callable) -> None:
    @wraps(func)
    async def run(*args, loop: t.Any = None, executor: t.Any = None, **kwargs) -> t.Any:
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
def my_async_sleep(duration: int) -> None:
    time.sleep(duration)
