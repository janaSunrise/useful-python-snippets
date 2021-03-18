import asyncio
import time


class GatewayRatelimiter:
    def __init__(self, count: int = 110, per: float = 60.0) -> None:
        self.max = count
        self.remaining = count
        self.window = 0.0
        self.per = per
        self.lock = asyncio.Lock()
        self.shard_id = None

    def is_ratelimited(self) -> bool:
        current = time.time()
        if current > self.window + self.per:
            return False
        return self.remaining == 0

    def get_delay(self) -> float:
        current = time.time()

        if current > self.window + self.per:
            self.remaining = self.max

        if self.remaining == self.max:
            self.window = current

        if self.remaining == 0:
            return self.per - (current - self.window)

        self.remaining -= 1
        if self.remaining == 0:
            self.window = current

        return 0.0

    async def block(self) -> None:
        async with self.lock:
            delta = self.get_delay()
            if delta:
                await asyncio.sleep(delta)
