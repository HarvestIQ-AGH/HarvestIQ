from abc import ABC, abstractmethod
from pathlib import Path

from infrastructure.data_engine import DataEngine
from infrastructure.local.local_config import LocalConfiguration


class ModelBase(ABC):
    def __init__(self, data_engine: DataEngine, config: LocalConfiguration) -> None:
        self.data_engine = data_engine
        self.config = config

    @abstractmethod
    def clean_data(self):
        pass

    @abstractmethod
    def feature_engineeeing(self):
        pass

    @abstractmethod
    def train(self):
        pass

    @abstractmethod
    def evaluate(self):
        pass

    @abstractmethod
    def load_pretrained(self, path: Path):
        pass

    def interact(self):
        self.evaluate()
