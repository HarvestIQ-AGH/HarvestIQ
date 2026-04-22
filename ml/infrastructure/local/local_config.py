from dataclasses import dataclass
from pathlib import Path

from .mode import Mode


@dataclass(frozen=True)
class Paths:
    data: Path
    artifacts: Path
    models: Path


DEFAULT_PATHS = Paths(
    data=Path("data"),
    artifacts=Path("artifacts"),
    models=Path("models"),
)

TEST_PATHS = Paths(
    data=Path("data") / "test",
    artifacts=Path("artifacts") / "test",
    models=Path("models") / "test",
)


class LocalConfiguration:
    def __init__(self, mode: Mode) -> None:
        import torch
        self.mode = mode
        self.paths = TEST_PATHS if mode == Mode.TEST else DEFAULT_PATHS
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
