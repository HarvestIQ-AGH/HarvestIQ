import os
from functools import wraps
from pathlib import Path

ARTIFACTS_DEFAULT_PATH = Path("artifacts")
ARTIFACTS_TEST_PATH = ARTIFACTS_DEFAULT_PATH / Path("test")

DATA_DEFAULT_PATH = Path("data")
DATA_TEST_PATH = DATA_DEFAULT_PATH / Path("test")


def make_directories():
    os.makedirs(ARTIFACTS_DEFAULT_PATH, exist_ok=True)
    os.makedirs(ARTIFACTS_TEST_PATH, exist_ok=True)
    os.makedirs(DATA_DEFAULT_PATH, exist_ok=True)
    os.makedirs(DATA_TEST_PATH, exist_ok=True)


def resolve_path(path_func):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            path = path_func()
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
