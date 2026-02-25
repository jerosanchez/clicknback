import logging

from .config import settings

LOG_LEVEL = getattr(logging, getattr(settings, "log_level", "INFO"))

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

logger = logging.getLogger(__name__)
