import typing as t


class MaybeUnlock:
    def __init__(self, lock: t.Any) -> None:
        self.lock = lock
        self._unlock = True

    def __enter__(self) -> "MaybeUnlock":
        return self

    def defer(self) -> None:
        self._unlock = False

    def __exit__(self, type: t.Any, value: t.Any, traceback: t.Any) -> None:
        if self._unlock:
            self.lock.release()
