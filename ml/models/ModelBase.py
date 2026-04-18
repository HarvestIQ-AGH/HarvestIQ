from abc import ABC, abstractmethod

from infrastructure.DataEngine import DataEngine


class ModelBase(ABC):
    def __init__(self, data_engine: DataEngine) -> None:
        self.data_engine = data_engine

    def _load_data(self):
        return self.data_engine.get_data()

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
