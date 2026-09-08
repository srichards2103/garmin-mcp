import stat
from unittest.mock import Mock, patch

import pytest

from garmin_mcp.auth import login, protect_files, restore_client, secure_directory


def test_private_token_permissions(tmp_path):
    directory = tmp_path / "tokens"
    secure_directory(directory)
    token = directory / "garmin_tokens.json"
    token.write_text("synthetic-test-token")
    protect_files(directory)
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    assert stat.S_IMODE(token.stat().st_mode) == 0o600


def test_reject_symlink_token_directory(tmp_path):
    link = tmp_path / "link"
    link.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(RuntimeError):
        secure_directory(link)


def test_missing_session_does_not_prompt(tmp_path, monkeypatch):
    monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path / "absent"))
    with patch("builtins.input") as prompt, pytest.raises(RuntimeError):
        restore_client()
    prompt.assert_not_called()


def test_interactive_login_saves_session_explicitly(tmp_path, monkeypatch):
    monkeypatch.setenv("GARMIN_TOKEN_DIR", str(tmp_path))
    client = Mock()
    with (
        patch("garminconnect.Garmin", return_value=client),
        patch("builtins.input", return_value="synthetic@example.test"),
        patch("garmin_mcp.auth.getpass", return_value="synthetic-password"),
    ):
        login()
    client.login.assert_called_once_with(str(tmp_path))
    client.client.dump.assert_called_once_with(str(tmp_path))
