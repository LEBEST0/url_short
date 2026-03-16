from unittest.mock import MagicMock, patch

import httpx
import pytest
from typer.testing import CliRunner

from pyshort.cli import app

runner = CliRunner()


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_shorten_response(short="http://localhost:8000/abc12x", code="abc12x", original="https://example.com"):
    return {"short": short, "code": code, "original": original}


def make_stats_response():
    return {
        "code": "abc12x",
        "short": "http://localhost:8000/abc12x",
        "original": "https://example.com/une/url/longue",
        "clicks": 7,
        "created_at": "2026-03-10T14:30:00.000",
    }


# ── Tests shorten ──────────────────────────────────────────────────────────────

def test_shorten_success():
    with patch("pyshort.cli.api_shorten", return_value=make_shorten_response()):
        with patch("pyshort.cli._try_copy", return_value=True):
            result = runner.invoke(app, ["shorten", "https://example.com"])
    assert result.exit_code == 0
    assert "abc12x" in result.output


def test_shorten_no_copy_flag():
    with patch("pyshort.cli.api_shorten", return_value=make_shorten_response()):
        with patch("pyshort.cli._try_copy") as mock_copy:
            result = runner.invoke(app, ["shorten", "https://example.com", "--no-copy"])
    mock_copy.assert_not_called()
    assert result.exit_code == 0


def test_shorten_http_error():
    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.text = "Unprocessable Entity"
    with patch("pyshort.cli.api_shorten", side_effect=httpx.HTTPStatusError("err", request=MagicMock(), response=mock_response)):
        result = runner.invoke(app, ["shorten", "pas-une-url"])
    assert result.exit_code == 1
    assert "422" in result.output


def test_shorten_connection_error():
    with patch("pyshort.cli.api_shorten", side_effect=httpx.RequestError("connection refused")):
        result = runner.invoke(app, ["shorten", "https://example.com"])
    assert result.exit_code == 1
    assert "Impossible" in result.output


# ── Tests stats ────────────────────────────────────────────────────────────────

def test_stats_with_code():
    with patch("pyshort.cli.api_stats", return_value=make_stats_response()):
        result = runner.invoke(app, ["stats", "abc12x"])
    assert result.exit_code == 0
    assert "abc12x" in result.output
    assert "7" in result.output


def test_stats_with_full_url():
    """Accepte une URL courte complète en plus du code seul."""
    with patch("pyshort.cli.api_stats", return_value=make_stats_response()) as mock_stats:
        result = runner.invoke(app, ["stats", "http://localhost:8000/abc12x"])
    mock_stats.assert_called_once_with("abc12x")
    assert result.exit_code == 0


def test_stats_not_found():
    mock_response = MagicMock()
    mock_response.status_code = 404
    with patch("pyshort.cli.api_stats", side_effect=httpx.HTTPStatusError("err", request=MagicMock(), response=mock_response)):
        result = runner.invoke(app, ["stats", "xxxxxx"])
    assert result.exit_code == 1
    assert "introuvable" in result.output


# ── Tests config ───────────────────────────────────────────────────────────────

def test_config_show():
    with patch("pyshort.cli.get_api_url", return_value="http://localhost:8000"):
        result = runner.invoke(app, ["config", "--show"])
    assert result.exit_code == 0
    assert "localhost:8000" in result.output


def test_config_set_api_url():
    with patch("pyshort.cli.save_api_url") as mock_save:
        result = runner.invoke(app, ["config", "--api-url", "https://mon-api.render.com"])
    mock_save.assert_called_once_with("https://mon-api.render.com")
    assert result.exit_code == 0
    assert "mise à jour" in result.output


# ── Tests version ──────────────────────────────────────────────────────────────

def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "pyshort" in result.output
