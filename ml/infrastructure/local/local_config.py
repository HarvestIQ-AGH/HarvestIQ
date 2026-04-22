from dataclasses import dataclass
from pathlib import Path

import torch

from infrastructure import Configuration

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


class LocalConfiguration(Configuration):
    def __init__(self, mode: Mode) -> None:
        super().__init__()
        self._mode = mode
        self.paths = TEST_PATHS if mode == Mode.TEST else DEFAULT_PATHS
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
