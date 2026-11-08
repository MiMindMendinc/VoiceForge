"""Packaging and download-gate tests. No network, no model files."""

from __future__ import annotations

from pathlib import Path

import pytest

import voiceforge_cli as cli

ROOT = Path(__file__).resolve().parent.parent


def test_console_script_declared():
    tomllib = pytest.importorskip("tomllib")
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert data["project"]["scripts"]["voiceforge"] == "voiceforge_cli:main"
    assert "serve" in cli.build_parser().format_help()


@pytest.mark.parametrize(
    "env,flag",
    [({"VOICEFORGE_NO_DOWNLOAD": "1"}, False), ({"CI": "true"}, False), ({}, True)],
)
def test_download_blocked(env, flag):
    assert cli.download_blocked(env, flag) is not None


def test_download_allowed_by_default():
    assert cli.download_blocked({}, False) is None
    assert cli.download_blocked({"VOICEFORGE_NO_DOWNLOAD": "0"}, False) is None


def test_ensure_models_skips_download_when_blocked(monkeypatch, tmp_path):
    import download_models

    def fail(*_a, **_k):
        raise AssertionError("download attempted")

    monkeypatch.setattr(download_models, "main", fail)
    monkeypatch.setattr(download_models, "download", fail)
    reason = cli.download_blocked({"CI": "true"})
    assert cli.ensure_models(tmp_path, ["kokoro-v1.0.onnx"], reason) == 0
    assert not any(tmp_path.iterdir())
