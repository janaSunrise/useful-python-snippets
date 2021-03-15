import asyncio
import threading


# -- The portal for the sync object creation --
class Portal:
    def __init__(self, stop_event):
        self.loop = asyncio.get_event_loop()
        self.stop_event = stop_event

    @staticmethod
    async def _call(fn, args, kwargs):
        return await fn(*args, **kwargs)

    async def _stop(self):
        self.stop_event.set()

    def call(self, fn, *args, **kwargs):
        return asyncio.run_coroutine_threadsafe(self._call(fn, args, kwargs), self.loop)

    def stop(self):
        return self.call(self._stop)


# -- Helper function to generate portal objects --
def create_portal():
    """
    Usage Documentation:

    ```
    async def test(msg):
        await asyncio.sleep(0.5)
        print(msg)
        return "HELLO " + msg

    # It'll run a new event loop in separate thread
    portal = create_portal()

    # It'll call `test` in the separate thread and return a Future
    print(portal.call(test, "WORLD").result())

    portal.stop().result()
    ```
    """
    portal = None

    async def wait_stop():
        nonlocal portal
        stop_event = asyncio.Event()
        portal = Portal(stop_event)
        running_event.set()
        await stop_event.wait()

    def run():
        asyncio.run(wait_stop())

    # -- Give each even a new thread so it's coroutine safe. --
    running_event = threading.Event()
    thread = threading.Thread(target=run)
    thread.start()
    running_event.wait()

    return portal
