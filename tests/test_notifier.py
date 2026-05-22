from __future__ import annotations

from unittest.mock import patch

from plume.notifier import notify


def test_notify_calls_notify_send() -> None:
    with patch("subprocess.run") as mock_run:
        notify("Titre", "Corps")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "notify-send" in args
        assert "Titre" in args
        assert "Corps" in args


def test_notify_silent_if_notify_send_missing() -> None:
    with patch("subprocess.run", side_effect=FileNotFoundError):
        notify("Titre", "Corps")  # must not raise


def test_notify_level_passed() -> None:
    with patch("subprocess.run") as mock_run:
        notify("T", "B", level="critical")
        args = mock_run.call_args[0][0]
        assert "critical" in args
