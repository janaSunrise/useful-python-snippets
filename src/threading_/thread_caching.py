import typing as t
from itertools import count
from threading import Lock, Thread

import outcome

IDLE_TIMEOUT = 10
name_counter = count()


class WorkerThread:
    def __init__(self, thread_cache: t.Any) -> None:
        self._job = None
        self._thread_cache = thread_cache
        self._worker_lock = Lock()
        self._worker_lock.acquire()

        thread = Thread(target=self._work, daemon=True)
        thread.name = f"Worker thread {next(name_counter)}"
        thread.start()

    def _work(self) -> None:
        while True:
            if self._worker_lock.acquire(timeout=IDLE_TIMEOUT):
                fn, deliver = self._job
                self._job = None
                result = outcome.capture(fn)
                self._thread_cache._idle_workers[self] = None
                deliver(result)
                del fn
                del deliver
            else:
                try:
                    del self._thread_cache._idle_workers[self]
                except KeyError:
                    continue
                else:
                    return


class ThreadCache:
    def __init__(self) -> None:
        self._idle_workers = {}

    def start_thread_soon(self, fn: t.Callable, deliver: t.Any) -> None:
        try:
            worker, _ = self._idle_workers.popitem()
        except KeyError:
            worker = WorkerThread(self)
        worker._job = (fn, deliver)
        worker._worker_lock.release()


THREAD_CACHE = ThreadCache()


def start_thread_soon(fn: t.Any, deliver: t.Any) -> None:
    THREAD_CACHE.start_thread_soon(fn, deliver)
