"""Tests for configuration resolution precedence."""

import pytest

from aicommit.config import DEFAULT_MODEL, load_config
from aicommit.errors import ConfigError


@pytest.fixture(autouse=True)
def _isolated_config_dir(tmp_path, monkeypatch):
    """Keep config-file lookups off the real filesystem for every test here."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))


def test_default_model(monkeypatch) -> None:
    monkeypatch.delenv("AICOMMIT_MODEL", raising=False)
    config = load_config()
    assert config.model == DEFAULT_MODEL


def test_env_overrides_default(monkeypatch) -> None:
    monkeypatch.setenv("AICOMMIT_MODEL", "claude-sonnet-5")
    config = load_config()
    assert config.model == "claude-sonnet-5"


def test_flag_overrides_env(monkeypatch) -> None:
    monkeypatch.setenv("AICOMMIT_MODEL", "claude-sonnet-5")
    config = load_config(model="claude-opus-4-8")
    assert config.model == "claude-opus-4-8"


def test_type_and_scope_default_to_none() -> None:
    config = load_config()
    assert config.commit_type is None
    assert config.scope is None


def test_type_and_scope_from_flags() -> None:
    config = load_config(commit_type="fix", scope="api")
    assert config.commit_type == "fix"
    assert config.scope == "api"


def test_local_config_file_sets_model(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("AICOMMIT_MODEL", raising=False)
    (tmp_path / ".aicommit.toml").write_text('model = "claude-sonnet-5"\n')
    config = load_config()
    assert config.model == "claude-sonnet-5"


def test_env_overrides_config_file(tmp_path, monkeypatch) -> None:
    (tmp_path / ".aicommit.toml").write_text('model = "claude-sonnet-5"\n')
    monkeypatch.setenv("AICOMMIT_MODEL", "claude-opus-4-8")
    config = load_config()
    assert config.model == "claude-opus-4-8"


def test_flag_overrides_config_file(tmp_path) -> None:
    (tmp_path / ".aicommit.toml").write_text('model = "claude-sonnet-5"\n')
    config = load_config(model="claude-opus-4-8")
    assert config.model == "claude-opus-4-8"


def test_config_file_sets_type_and_scope(tmp_path) -> None:
    (tmp_path / ".aicommit.toml").write_text('type = "fix"\nscope = "api"\n')
    config = load_config()
    assert config.commit_type == "fix"
    assert config.scope == "api"


def test_flag_overrides_config_file_type_and_scope(tmp_path) -> None:
    (tmp_path / ".aicommit.toml").write_text('type = "fix"\nscope = "api"\n')
    config = load_config(commit_type="feat", scope="cli")
    assert config.commit_type == "feat"
    assert config.scope == "cli"


def test_config_file_sets_max_diff_bytes(tmp_path) -> None:
    (tmp_path / ".aicommit.toml").write_text("max_diff_bytes = 5000\n")
    config = load_config()
    assert config.max_diff_bytes == 5000


def test_xdg_config_file_used_when_no_local_file(tmp_path, monkeypatch) -> None:
    xdg_dir = tmp_path / "xdg" / "aicommit"
    xdg_dir.mkdir(parents=True)
    (xdg_dir / "config.toml").write_text('model = "claude-sonnet-5"\n')
    config = load_config()
    assert config.model == "claude-sonnet-5"


def test_local_config_file_wins_over_xdg(tmp_path, monkeypatch) -> None:
    xdg_dir = tmp_path / "xdg" / "aicommit"
    xdg_dir.mkdir(parents=True)
    (xdg_dir / "config.toml").write_text('model = "claude-sonnet-5"\n')
    (tmp_path / ".aicommit.toml").write_text('model = "claude-opus-4-8"\n')
    config = load_config()
    assert config.model == "claude-opus-4-8"


def test_malformed_config_file_raises_config_error(tmp_path) -> None:
    (tmp_path / ".aicommit.toml").write_text("this is not [valid toml\n")
    with pytest.raises(ConfigError):
        load_config()
