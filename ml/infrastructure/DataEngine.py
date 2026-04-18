import pandas as pd


class DataEngine:
    def __init__(self, path) -> None:
        self.path = path

    def get_data(self):
        return pd.read_csv(self.path)
