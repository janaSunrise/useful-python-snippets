import functools
import typing as t

import logging

logger = logging.getLogger(__name__)


# -- Decorators --
def log_error() -> t.Any:
    """Decorator for logging errors."""
    def error_logging(func: t.Callable) -> t.Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> t.Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"ERROR: {e!r} | Location: {func.__name__}", exc_info=True
                )
                return {"error": f"{e!r} | Please try again later."}

        return wrapper
    return error_logging
