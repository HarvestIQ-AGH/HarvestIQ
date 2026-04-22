from itertools import islice
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from PIL import Image
from pynndescent import NNDescent
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from infrastructure.DataEngine import DataEngine
from infrastructure.logger import LoggerMixin
from models.ModelBase import ModelBase
from models.train_me import train_me

MAX_IMAGES = 5000


@train_me
class ImageSearch(ModelBase, LoggerMixin):
    def __init__(self, data_engine: DataEngine) -> None:
        super().__init__(data_engine)

    def clean_data(self):
        df = self._load_data()
        mask = (df["height"] >= 1000) & (df["width"] >= 1000)
        df = df.loc[mask, :]
        images_root = Path(self.data_engine.path).parent.parent / "small"
        self._image_paths = images_root.as_posix() + "/" + df["path"].astype(str)
        self.logger.info(f"Found {len(self._image_paths)} images after filtering.")

    def feature_engineeeing(self):
        self._embeddings = self._vectorize_images(self._image_paths)
        self.logger.info(f"Embeddings shape: {self._embeddings.shape}")

    def train(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model = SentenceTransformer("clip-ViT-B-32", device=device)
        self._index = NNDescent(
            self._embeddings,
            metric="cosine",
            random_state=0,
            n_jobs=-1,
        )
        self._indexed_paths = self._image_paths.iloc[:MAX_IMAGES].values
        self.logger.info("NNDescent index built.")

    def evaluate(self):
        for query in ["blue pillow", "wooden chair", "graphics card"]:
            results = self.query(query)
            self.logger.info(f"'{query}' -> {len(results)} results, first: {results[0]}")

    def query(self, text: str, n_neighbors: int = 9) -> list[str]:
        embedding = self._model.encode([text])
        indices, _ = self._index.query(embedding, k=n_neighbors)
        return [self._indexed_paths[i] for i in indices[0]]

    def show(self, image_paths: list[str]) -> None:
        import matplotlib.pyplot as plt
        from mpl_toolkits.axes_grid1 import ImageGrid

        fig = plt.figure(figsize=(12, 4))
        grid = ImageGrid(fig, 111, nrows_ncols=(1, len(image_paths)), axes_pad=0.1)
        for ax, path in zip(grid, image_paths):
            ax.imshow(Image.open(path))
            ax.axis("off")
        plt.show()

    def search(self, text: str, n_neighbors: int = 9) -> None:
        self.show(self.query(text, n_neighbors))

    def _vectorize_images(self, image_paths: pd.Series) -> np.ndarray:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = SentenceTransformer("clip-ViT-B-32", device=device)
        batch_size = joblib.cpu_count(only_physical_cores=True)

        def batched(iterable, n: int):
            it = iter(iterable)
            while batch := tuple(islice(it, n)):
                yield batch

        embeddings = np.empty((MAX_IMAGES, 512))

        with tqdm(total=MAX_IMAGES, desc="Vectorizing images") as pbar:
            start_idx = 0
            for batch in batched(image_paths.iloc[:MAX_IMAGES], batch_size):
                end_idx = min(start_idx + batch_size, MAX_IMAGES)
                images = [Image.open(p) for p in batch]
                embeddings[start_idx:end_idx] = model.encode(images)
                start_idx = end_idx
                pbar.update(batch_size)

        return embeddings
