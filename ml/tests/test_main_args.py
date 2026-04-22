import subprocess
import sys


def _run(*args):
    return subprocess.run(
        [sys.executable, "main.py", *args],
        capture_output=True,
        text=True,
    )


def test_train_requires_run():
    result = _run("--train")
    assert result.returncode != 0
    assert "error" in result.stderr.lower()


def test_from_pretrained_requires_run():
    result = _run("--from-pretrained")
    assert result.returncode != 0


def test_visualize_requires_run():
    result = _run("--visualize")
    assert result.returncode != 0


def test_stop_stage_too_low():
    result = _run("--run", "RegressionModel", "--train", "--stop-stage", "0")
    assert result.returncode != 0


def test_stop_stage_too_high():
    result = _run("--run", "RegressionModel", "--train", "--stop-stage", "6")
    assert result.returncode != 0


def test_train_and_from_pretrained_mutually_exclusive():
    result = _run("--train", "--from-pretrained")
    assert result.returncode != 0


def test_run_alone_error():
    result = _run("--run", "Foo")
    assert result.returncode != 0


def test_help_exits_zero():
    result = _run("--help")
    assert result.returncode == 0
