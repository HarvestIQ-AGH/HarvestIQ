import logging
import sys

_ROOT_LOGGER_NAME = "harvestiq-ml"
_configured = False

def _configure_default_logger():
    global _configured
    if _configured:
        return

    root = logging.getLogger(_ROOT_LOGGER_NAME)

    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            fmt="%(asctime)s  %(levelname)-8s  [%(name)s]  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        root.addHandler(handler)

    root.propagate = False
    _configured = True


def get_logger(name: str | None = None) -> logging.Logger:
    _configure_default_logger()
    if name:
        return logging.getLogger(f"{_ROOT_LOGGER_NAME}.{name}")
    return logging.getLogger(_ROOT_LOGGER_NAME)


logger = get_logger()

class LoggerMixin:
    @property
    def logger(self) -> logging.Logger:
        return get_logger(type(self).__name__)
