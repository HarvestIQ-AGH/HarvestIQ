import pytest

from cli import visualize


def test_no_analysis_dir_exits(isolated_config):
    with pytest.raises(SystemExit):
        visualize("RegressionModel", isolated_config)


def test_no_pngs_exits(isolated_config):
    analysis_dir = isolated_config.paths.artifacts / "RegressionModel" / "analysis"
    analysis_dir.mkdir(parents=True)
    with pytest.raises(SystemExit):
        visualize("RegressionModel", isolated_config)


def test_opens_browser(isolated_config, fake_png_bytes, monkeypatch):
    raw_dir = isolated_config.paths.artifacts / "RegressionModel" / "analysis" / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "test_plot.png").write_bytes(fake_png_bytes)

    opened = []
    monkeypatch.setattr("webbrowser.open", lambda url: opened.append(url))
    visualize("RegressionModel", isolated_config)
    assert len(opened) == 1


def test_html_contains_model_name(isolated_config, fake_png_bytes, monkeypatch):
    raw_dir = isolated_config.paths.artifacts / "RegressionModel" / "analysis" / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "test_plot.png").write_bytes(fake_png_bytes)

    captured = []
    monkeypatch.setattr("webbrowser.open", lambda url: captured.append(url))
    visualize("RegressionModel", isolated_config)

    html = open(captured[0].removeprefix("file://")).read()
    assert "RegressionModel" in html


def test_html_embeds_png_as_base64(isolated_config, fake_png_bytes, monkeypatch):
    raw_dir = isolated_config.paths.artifacts / "RegressionModel" / "analysis" / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "test_plot.png").write_bytes(fake_png_bytes)

    captured = []
    monkeypatch.setattr("webbrowser.open", lambda url: captured.append(url))
    visualize("RegressionModel", isolated_config)

    html = open(captured[0].removeprefix("file://")).read()
    assert "data:image/png;base64," in html


def test_html_label_is_relative(isolated_config, fake_png_bytes, monkeypatch):
    raw_dir = isolated_config.paths.artifacts / "RegressionModel" / "analysis" / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "foo.png").write_bytes(fake_png_bytes)

    captured = []
    monkeypatch.setattr("webbrowser.open", lambda url: captured.append(url))
    visualize("RegressionModel", isolated_config)

    html = open(captured[0].removeprefix("file://")).read()
    assert "raw/foo.png" in html
    assert str(raw_dir) not in html


def test_multiple_pngs_all_in_html(isolated_config, fake_png_bytes, monkeypatch):
    raw_dir = isolated_config.paths.artifacts / "RegressionModel" / "analysis" / "raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "plot1.png").write_bytes(fake_png_bytes)
    (raw_dir / "plot2.png").write_bytes(fake_png_bytes)

    captured = []
    monkeypatch.setattr("webbrowser.open", lambda url: captured.append(url))
    visualize("RegressionModel", isolated_config)

    html = open(captured[0].removeprefix("file://")).read()
    assert html.count("<img") == 2
