import ast
import importlib.util
from pathlib import Path

from infrastructure.logger import logger

def _find_model_file(model_name: str, models_root: Path) -> Path:
    stem = Path(model_name).stem
    matches = list(models_root.rglob(f"{stem}.py"))
    if not matches:
        raise FileNotFoundError(
            f"No model file found for '{model_name}' under {models_root}/"
        )
    if len(matches) > 1:
        raise ValueError(
            f"Ambiguous model name '{model_name}', found: {[str(m) for m in matches]}"
        )
    return matches[0]


def _find_train_me_class_name(model_file: Path) -> str:
    tree = ast.parse(model_file.read_text())
    candidates = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for decorator in node.decorator_list:
            name = (
                decorator.id
                if isinstance(decorator, ast.Name)
                else (decorator.attr if isinstance(decorator, ast.Attribute) else None)
            )
            if name == "train_me":
                candidates.append(node.name)
    if not candidates:
        raise ValueError(f"No @train_me class found in {model_file}")
    if len(candidates) > 1:
        raise ValueError(f"Multiple @train_me classes in {model_file}: {candidates}")
    return candidates[0]


def load_model_class(model_name: str, models_root: Path):
    model_file = _find_model_file(model_name, models_root)
    class_name = _find_train_me_class_name(model_file)
    logger.info(f"Loading {class_name} from {model_file}")

    spec = importlib.util.spec_from_file_location(model_file.stem, model_file)
    assert spec is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return getattr(module, class_name)
