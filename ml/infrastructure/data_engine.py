import sqlite3
from collections.abc import Iterable, Iterator
from pathlib import Path

import pandas as pd
from PIL import Image


class DataEngine:
    def get_csv_data(self, path: Path | str) -> pd.DataFrame:
        return pd.read_csv(path)

    def get_sqlite_data(self, path: Path | str, table: str) -> pd.DataFrame:
        with sqlite3.connect(path) as conn:
            return pd.read_sql_query(f'SELECT * FROM "{table}"', conn)

    def get_images_batch(
        self,
        image_paths: Iterable[str | Path],
        batch_size: int,
    ) -> Iterator[list[Image.Image]]:
        batch: list[Image.Image] = []
        for path in image_paths:
            batch.append(Image.open(path))
            if len(batch) == batch_size:
                yield batch
                batch = []
        if batch:
            yield batch
