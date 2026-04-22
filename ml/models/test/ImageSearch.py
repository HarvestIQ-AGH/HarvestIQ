import joblib
import json
import numpy as np
from pathlib import Path
import pandas as pd
from PIL import Image
from pynndescent import NNDescent
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from infrastructure.data_engine import DataEngine
from infrastructure.local.local_config import LocalConfiguration
from infrastructure.logger import LoggerMixin
from models.model_base import ModelBase
from models.model_lineage import ModelLineage
from models.train_me import train_me
from utilities.path_resolver import resolve_path

MAX_IMAGES = 5000


@train_me
class ImageSearch(ModelBase, LoggerMixin):
    def __init__(self, data_engine: DataEngine, config: LocalConfiguration) -> None:
        super().__init__(data_engine, config)
        self.model_lineage = ModelLineage(self, config.paths.artifacts)

    def clean_data(self):
        df = self.data_engine.get_csv_data(self.config.paths.data / "images" / "metadata" / "images.csv.gz")
        mask = (df["height"] >= 1000) & (df["width"] >= 1000)
        df = df.loc[mask, :]
        images_root = self.config.paths.data / "images" / "small"
        self._image_paths = images_root.as_posix() + "/" + df["path"].astype(str)
        self.logger.info(f"Found {len(self._image_paths)} images after filtering.")

    def feature_engineeeing(self):
        self._embeddings = self._vectorize_images(self._image_paths)
        self.logger.info(f"Embeddings shape: {self._embeddings.shape}")
        self.model_lineage.add_metadata_entries(
            embeddings_shape=list(self._embeddings.shape),
            max_images=MAX_IMAGES,
            query_params={"n_neighbors": 9},
        )
        self.model_lineage.export()

    def train(self):
        self._model = SentenceTransformer("clip-ViT-B-32", device=self.config.device)
        self._index = NNDescent(
            self._embeddings,
            metric="cosine",
            random_state=0,
            n_jobs=-1,
        )
        self._indexed_paths = self._image_paths.iloc[:MAX_IMAGES].values
        self.logger.info("NNDescent index built.")

        @resolve_path(self.model_lineage.path)
        def _save():
            np.save("embeddings.npy", self._embeddings)
            joblib.dump(self._index, "index.joblib")
            np.save("indexed_paths.npy", self._indexed_paths)

        _save()

    def evaluate(self):
        for query in ["blue pillow", "wooden chair", "graphics card"]:
            results = self.query(query)
            self.logger.info(
                f"'{query}' -> {len(results)} results, first: {results[0]}"
            )

    def load_pretrained(self, path: Path):
        self._embeddings = np.load(path / "embeddings.npy")
        self._index = joblib.load(path / "index.joblib")
        self._indexed_paths = np.load(path / "indexed_paths.npy", allow_pickle=True)
        self._model = SentenceTransformer("clip-ViT-B-32", device=self.config.device)
        metadata_file = path / f"{path.name}_metadata.json"
        metadata = json.loads(metadata_file.read_text()) if metadata_file.exists() else {}
        self._query_params: dict = metadata.get("query_params", {"n_neighbors": 9})

    def interact(self):
        n_neighbors = self._query_params.get("n_neighbors", 9)
        print(f"ImageSearch ready  |  n_neighbors={n_neighbors}  |  enter 'q' to quit")
        while True:
            try:
                query = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if query.lower() in ("q", "quit", "exit"):
                break
            if not query:
                continue
            for path in self.query(query, n_neighbors=n_neighbors):
                print(f"  {path}")

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
        model = SentenceTransformer("clip-ViT-B-32", device=self.config.device)
        batch_size = joblib.cpu_count(only_physical_cores=True)

        embeddings = np.empty((MAX_IMAGES, 512))

        with tqdm(total=MAX_IMAGES, desc="Vectorizing images") as pbar:
            start_idx = 0
            for batch in self.data_engine.get_images_batch(image_paths.iloc[:MAX_IMAGES], batch_size):
                end_idx = min(start_idx + len(batch), MAX_IMAGES)
                embeddings[start_idx:end_idx] = model.encode(batch)
                start_idx = end_idx
                pbar.update(len(batch))

        return embeddings
