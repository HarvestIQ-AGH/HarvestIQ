import pytest

from cli.from_pretrained import _find_latest_version, from_pretrained


def test_no_model_dir_returns_none(tmp_path):
    assert _find_latest_version("M", tmp_path) is None


def test_empty_model_dir_returns_none(tmp_path):
    (tmp_path / "M").mkdir()
    assert _find_latest_version("M", tmp_path) is None


def test_returns_single_version(tmp_path):
    v1 = tmp_path / "M" / "M_v1"
    v1.mkdir(parents=True)
    assert _find_latest_version("M", tmp_path) == v1


def test_returns_highest_version(tmp_path):
    for i in range(1, 4):
        (tmp_path / "M" / f"M_v{i}").mkdir(parents=True, exist_ok=True)
    result = _find_latest_version("M", tmp_path)
    assert result.name == "M_v3"


def test_ignores_non_version_dirs(tmp_path):
    (tmp_path / "M").mkdir()
    (tmp_path / "M" / "M_data").mkdir()
    (tmp_path / "M" / "M_analysis").mkdir()
    assert _find_latest_version("M", tmp_path) is None


def test_from_pretrained_no_weights_calls_sys_exit(isolated_config):
    with pytest.raises(SystemExit):
        from_pretrained("RegressionModel", isolated_config)
