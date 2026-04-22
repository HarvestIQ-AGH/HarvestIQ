import os
from functools import wraps

from infrastructure.local.local_config import DEFAULT_PATHS, TEST_PATHS


def make_directories():
    for paths in (DEFAULT_PATHS, TEST_PATHS):
        os.makedirs(paths.data, exist_ok=True)
        os.makedirs(paths.artifacts, exist_ok=True)


def resolve_path(path_or_func):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            path = path_or_func() if callable(path_or_func) else path_or_func
            current_dir = os.getcwd()

            os.makedirs(path, exist_ok=True)

            os.chdir(path)
            try:
                result = func(*args, **kwargs)
            finally:
                os.chdir(current_dir)

            return result

        return wrapper

    return decorator
