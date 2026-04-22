import ast
import importlib
import importlib.util
import os
import sys
from pathlib import Path

from .logger import logger


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


def _import_path(model_file: Path) -> str | None:
    abs_path = model_file.resolve()
    for raw in sys.path:
        base = Path(os.getcwd() if not raw else raw).resolve()
        try:
            rel = abs_path.relative_to(base)
            return ".".join(rel.with_suffix("").parts)
        except ValueError:
            continue
    return None


def load_model_class(model_name: str, models_root: Path):
    model_file = _find_model_file(model_name, models_root)
    class_name = _find_train_me_class_name(model_file)
    logger.info(f"Loading {class_name} from {model_file}")

    import_path = _import_path(model_file)
    if import_path and "." in import_path:
        module = importlib.import_module(import_path)
    else:
        name = import_path or model_file.stem
        spec = importlib.util.spec_from_file_location(name, model_file)
        assert spec is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)

    return getattr(module, class_name)
