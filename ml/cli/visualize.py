import base64
import sys
import tempfile
import webbrowser
from pathlib import Path

from infrastructure import logger
from infrastructure.local import LocalConfiguration


def visualize(model_name: str, config: LocalConfiguration) -> None:
    analysis_dir = config.paths.artifacts / model_name / "analysis"

    if not analysis_dir.exists():
        logger.error(
            f"No analysis directory found at {analysis_dir}. "
            f"Run --train --stop-stage 2 (or higher) first."
        )
        sys.exit(1)

    png_files = sorted(analysis_dir.rglob("*.png"))

    if not png_files:
        logger.error(f"No PNG files found under {analysis_dir}.")
        sys.exit(1)

    logger.info(f"Found {len(png_files)} plot(s) — opening in browser.")
    html = _build_html(model_name, png_files, analysis_dir)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        tmp_path = f.name

    webbrowser.open(f"file://{tmp_path}")


def _build_html(model_name: str, png_files: list[Path], analysis_dir: Path) -> str:
    cards = []
    for png in png_files:
        label = png.relative_to(analysis_dir)
        b64 = base64.b64encode(png.read_bytes()).decode("ascii")
        cards.append(
            f'<div class="card">'
            f'<p class="label">{label}</p>'
            f'<img src="data:image/png;base64,{b64}" alt="{label}">'
            f'</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{model_name} — Analysis Plots</title>
  <style>
    body {{ font-family: sans-serif; background: #1a1a2e; color: #eee; padding: 2rem; }}
    h1   {{ text-align: center; margin-bottom: 2rem; }}
    .grid {{ display: flex; flex-wrap: wrap; gap: 1.5rem; justify-content: center; }}
    .card {{ background: #16213e; border-radius: 8px; padding: 1rem;
             max-width: 720px; box-shadow: 0 4px 12px rgba(0,0,0,0.4); }}
    .card img {{ max-width: 100%; border-radius: 4px; }}
    .label {{ font-size: 0.85rem; color: #aaa; margin-bottom: 0.5rem; word-break: break-all; }}
  </style>
</head>
<body>
  <h1>{model_name} — Analysis Plots</h1>
  <div class="grid">
    {"".join(cards)}
  </div>
</body>
</html>"""
