import asyncio
import datetime
import inspect
import sys
import traceback
import typing as t

from src.algorithm.backoff import ExponentialBackoff


class Loop:
    def __init__(
            self, coro: t.Awaitable, seconds: int, hours: int, minutes: int, count: int, reconnect: bool,
            loop: asyncio.Task
    ):
        self.coro = coro
        self.reconnect = reconnect
        self.loop = loop
        self.count = count
        self._current_loop = 0
        self._task = None
        self._injected = None
        self._valid_exception = (OSError)

        self._before_loop = None
        self._after_loop = None
        self._is_being_cancelled = False
        self._has_failed = False
        self._stop_next_iteration = False

        if self.count is not None and self.count <= 0:
            raise ValueError('count must be greater than 0 or None.')

        self.change_interval(seconds=seconds, minutes=minutes, hours=hours)
        self._last_iteration_failed = False
        self._last_iteration = None
        self._next_iteration = None

        if not inspect.iscoroutinefunction(self.coro):
            raise TypeError('Expected coroutine function, not {0.__name__!r}.'.format(type(self.coro)))

    async def _call_loop_function(self, name: str, *args, **kwargs):
        coro = getattr(self, '_' + name)
        if coro is None:
            return

        if self._injected is not None:
            await coro(self._injected, *args, **kwargs)
        else:
            await coro(*args, **kwargs)

    async def _loop(self, *args, **kwargs):
        backoff = ExponentialBackoff()
        await self._call_loop_function('before_loop')
        self._last_iteration_failed = False
        self._next_iteration = datetime.datetime.now(datetime.timezone.utc)
        try:
            await asyncio.sleep(0)
            while True:
                if not self._last_iteration_failed:
                    self._last_iteration = self._next_iteration
                    self._next_iteration = self._get_next_sleep_time()
                try:
                    await self.coro(*args, **kwargs)
                    self._last_iteration_failed = False
                    now = datetime.datetime.now(datetime.timezone.utc)
                    if now > self._next_iteration:
                        self._next_iteration = now
                except self._valid_exception:
                    self._last_iteration_failed = True
                    if not self.reconnect:
                        raise
                    await asyncio.sleep(backoff.delay())
                else:
                    if self._stop_next_iteration:
                        return
                    self._current_loop += 1
                    if self._current_loop == self.count:
                        break

                    await sleep_until(self._next_iteration)
        except asyncio.CancelledError:
            self._is_being_cancelled = True
            raise
        except Exception as exc:
            self._has_failed = True
            await self._call_loop_function('error', exc)
            raise exc
        finally:
            await self._call_loop_function('after_loop')
            self._is_being_cancelled = False
            self._current_loop = 0
            self._stop_next_iteration = False
            self._has_failed = False

    def __get__(self, obj: t.Any, objtype: t.Any) -> t.Any:
        if obj is None:
            return self

        copy = Loop(
            self.coro, seconds=self.seconds, hours=self.hours, minutes=self.minutes,
            count=self.count, reconnect=self.reconnect, loop=self.loop
        )
        copy._injected = obj
        copy._before_loop = self._before_loop
        copy._after_loop = self._after_loop
        copy._error = self._error
        setattr(obj, self.coro.__name__, copy)
        return copy

    @property
    def current_loop(self) -> int:
        return self._current_loop

    @property
    def next_iteration(self) -> t.Optional[datetime.datetime]:
        if self._task is None:
            return None
        elif self._task and self._task.done() or self._stop_next_iteration:
            return None

        return self._next_iteration

    async def __call__(self, *args, **kwargs) -> asyncio.Task:
        if self._injected is not None:
            args = (self._injected, *args)

        return await self.coro(*args, **kwargs)

    def start(self, *args, **kwargs) -> asyncio.Task:
        if self._task is not None and not self._task.done():
            raise RuntimeError('Task is already launched and is not completed.')

        if self._injected is not None:
            args = (self._injected, *args)

        if self.loop is None:
            self.loop = asyncio.get_event_loop()

        self._task = self.loop.create_task(self._loop(*args, **kwargs))
        return self._task

    def stop(self) -> None:
        if self._task and not self._task.done():
            self._stop_next_iteration = True

    def _can_be_cancelled(self) -> bool:
        return not self._is_being_cancelled and self._task and not self._task.done()

    def cancel(self) -> None:
        if self._can_be_cancelled():
            self._task.cancel()

    def restart(self, *args, **kwargs) -> None:
        def restart_when_over(fut: t.Any, *, args: t.Any = args, kwargs: t.Any = kwargs) -> None:
            self._task.remove_done_callback(restart_when_over)
            self.start(*args, **kwargs)

        if self._can_be_cancelled():
            self._task.add_done_callback(restart_when_over)
            self._task.cancel()

    def add_exception_type(self, *exceptions) -> None:
        for exc in exceptions:
            if not inspect.isclass(exc):
                raise TypeError('{0!r} must be a class.'.format(exc))
            if not issubclass(exc, BaseException):
                raise TypeError('{0!r} must inherit from BaseException.'.format(exc))

        self._valid_exception = (*self._valid_exception, *exceptions)

    def clear_exception_types(self) -> None:
        self._valid_exception = tuple()

    def remove_exception_type(self, *exceptions) -> bool:
        old_length = len(self._valid_exception)
        self._valid_exception = tuple(x for x in self._valid_exception if x not in exceptions)
        return len(self._valid_exception) == old_length - len(exceptions)

    def get_task(self) -> asyncio.Task:
        return self._task

    def is_being_cancelled(self) -> bool:
        return self._is_being_cancelled

    def failed(self) -> bool:
        return self._has_failed

    def is_running(self) -> bool:
        return not bool(self._task.done()) if self._task else False

    async def _error(self, *args) -> None:
        exception = args[-1]
        print('Unhandled exception in internal background task {0.__name__!r}.'.format(self.coro), file=sys.stderr)
        traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)

    def before_loop(self, coro: t.Coroutine) -> t.Coroutine:
        if not inspect.iscoroutinefunction(coro):
            raise TypeError('Expected coroutine function, received {0.__name__!r}.'.format(type(coro)))

        self._before_loop = coro
        return coro

    def after_loop(self, coro: t.Coroutine) -> t.Coroutine:
        if not inspect.iscoroutinefunction(coro):
            raise TypeError('Expected coroutine function, received {0.__name__!r}.'.format(type(coro)))

        self._after_loop = coro
        return coro

    def error(self, coro: t.Coroutine) -> t.Coroutine:
        if not inspect.iscoroutinefunction(coro):
            raise TypeError('Expected coroutine function, received {0.__name__!r}.'.format(type(coro)))

        self._error = coro
        return coro

    def _get_next_sleep_time(self) -> int:
        return self._last_iteration + datetime.timedelta(seconds=self._sleep)

    def change_interval(self, *, seconds: int = 0, minutes: int = 0, hours: int = 0) -> None:
        sleep = seconds + (minutes * 60.0) + (hours * 3600.0)
        if sleep < 0:
            raise ValueError('Total number of seconds cannot be less than zero.')

        self._sleep = sleep
        self.seconds = seconds
        self.hours = hours
        self.minutes = minutes


async def sleep_until(when: datetime.datetime, result: t.Any = None) -> t.Any:
    MAX_ASYNCIO_SECONDS = 3456000

    if when.tzinfo is None:
        when = when.replace(tzinfo=datetime.timezone.utc)

    now = datetime.datetime.now(datetime.timezone.utc)
    delta = (when - now).total_seconds()

    while delta > MAX_ASYNCIO_SECONDS:
        await asyncio.sleep(MAX_ASYNCIO_SECONDS)
        delta -= MAX_ASYNCIO_SECONDS

    return await asyncio.sleep(max(delta, 0), result)


def loop(
    *,
    seconds: int = 0, minutes: int = 0, hours: int = 0, count: t.Any = None, reconnect: bool = True,
    loop: asyncio.Task = None
) -> t.Callable:
    def decorator(func: t.Callable) -> Loop:
        kwargs = {
            'seconds': seconds,
            'minutes': minutes,
            'hours': hours,
            'count': count,
            'reconnect': reconnect,
            'loop': loop
        }
        return Loop(func, **kwargs)
    return decorator
