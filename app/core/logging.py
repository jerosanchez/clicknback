import logging
from logging import LogRecord

from app.core.config import settings


class ExtraDictFormatter(logging.Formatter):
    def format(self, record: LogRecord) -> str:
        standard_attrs = set(
            [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "asctime",
                "message",
                "taskName",
            ]
        )
        extras = {k: v for k, v in record.__dict__.items() if k not in standard_attrs}
        base = super().format(record)
        if extras:
            return f"{base} | extra={extras}"
        return base


LOG_LEVEL = getattr(logging, getattr(settings, "log_level", "INFO"))

handler = logging.StreamHandler()
handler.setFormatter(
    ExtraDictFormatter(fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
)

root_logger = logging.getLogger()
root_logger.setLevel(LOG_LEVEL)
root_logger.handlers.clear()
root_logger.addHandler(handler)

logger = logging.getLogger(__name__)
