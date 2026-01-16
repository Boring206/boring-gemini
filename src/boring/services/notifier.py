# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0
"""
BoringDone - Completion Notification System

Notifies users when AI tasks complete, so they don't need to watch the screen.
Supports: Windows Toast, macOS Notification Center, Sound Alert, Terminal Bell.
"""

import logging
import platform
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications."""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class NotificationConfig:
    """Configuration for notifications."""

    enable_toast: bool = True  # Desktop notification
    enable_sound: bool = True  # Beep/sound alert
    enable_terminal_bell: bool = True  # Terminal \a
    sound_file: str | None = None  # Custom sound path

    # External Channels (V14.1)
    slack_webhook: str | None = None
    discord_webhook: str | None = None
    email_recipient: str | None = None


# Global config (can be overridden via .boring.toml)
_config = NotificationConfig()


def configure(
    enable_toast: bool = True,
    enable_sound: bool = True,
    enable_terminal_bell: bool = True,
    sound_file: str | None = None,
    slack_webhook: str | None = None,
    discord_webhook: str | None = None,
    email_recipient: str | None = None,
):
    """Configure notification settings."""
    global _config
    _config = NotificationConfig(
        enable_toast=enable_toast,
        enable_sound=enable_sound,
        enable_terminal_bell=enable_terminal_bell,
        sound_file=sound_file,
        slack_webhook=slack_webhook,
        discord_webhook=discord_webhook,
        email_recipient=email_recipient,
    )


def _notify_windows(title: str, message: str, icon: str = "info") -> bool:
    """Send Windows toast notification."""
    try:
        # Try plyer first (cross-platform)
        from plyer import notification

        notification.notify(title=title, message=message, app_name="Boring", timeout=10)
        return True
    except ImportError:
        pass

    # Fallback: PowerShell toast
    try:
        ps_script = f'''
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        $template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
        $xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template)
        $text = $xml.GetElementsByTagName("text")
        $text[0].AppendChild($xml.CreateTextNode("{title}")) | Out-Null
        $text[1].AppendChild($xml.CreateTextNode("{message}")) | Out-Null
        $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Boring")
        $notifier.Show([Windows.UI.Notifications.ToastNotification]::new($xml))
        '''
        subprocess.run(["powershell", "-Command", ps_script], capture_output=True, timeout=5)
        return True
    except Exception as e:
        logger.debug(f"Windows toast failed: {e}")
        return False


def _notify_macos(title: str, message: str) -> bool:
    """Send macOS notification via osascript."""
    try:
        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
        return True
    except Exception as e:
        logger.debug(f"macOS notification failed: {e}")
        return False


def _notify_linux(title: str, message: str) -> bool:
    """Send Linux notification via notify-send."""
    try:
        subprocess.run(["notify-send", title, message], capture_output=True, timeout=5)
        return True
    except Exception as e:
        logger.debug(f"Linux notification failed: {e}")
        return False


def _play_sound() -> bool:
    """Play completion sound."""
    system = platform.system()

    # Custom sound file
    if _config.sound_file and Path(_config.sound_file).exists():
        try:
            if system == "Windows":
                import winsound

                winsound.PlaySound(_config.sound_file, winsound.SND_FILENAME)
            elif system == "Darwin":
                subprocess.run(["afplay", _config.sound_file], timeout=5)
            else:
                subprocess.run(["aplay", _config.sound_file], timeout=5)
            return True
        except Exception:
            pass

    # System beep
    try:
        if system == "Windows":
            import winsound

            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        elif system == "Darwin":
            subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], timeout=5)
        else:
            print("\a", end="", flush=True)  # Terminal bell
        return True
    except Exception as e:
        logger.debug(f"Sound failed: {e}")
        return False


def _terminal_bell():
    """Simple terminal bell."""
    print("\a", end="", flush=True)


# Slack/Discord logic moved to src/boring/services/notifications.py
# This file remains for backward compatibility and low-level system sounds


def notify(
    title: str = "Boring Done! 🎉",
    message: str = "Your AI task has completed.",
    notification_type: NotificationType = NotificationType.SUCCESS,
    force_all: bool = False,
) -> dict:
    """
    Send a completion notification to the user.

    Args:
        title: Notification title
        message: Notification message
        notification_type: Type of notification (success/error/warning/info)
        force_all: Ignore config and try all methods

    Returns:
        dict with status and methods used
    """
    methods_tried = []
    methods_success = []

    system = platform.system()

    # 1. Desktop toast notification
    if force_all or _config.enable_toast:
        methods_tried.append("toast")
        success = False
        if system == "Windows":
            success = _notify_windows(title, message)
        elif system == "Darwin":
            success = _notify_macos(title, message)
        else:
            success = _notify_linux(title, message)
        if success:
            methods_success.append("toast")

    # 2. Sound alert
    if force_all or _config.enable_sound:
        methods_tried.append("sound")
        if _play_sound():
            methods_success.append("sound")

    # 3. Terminal bell
    if force_all or _config.enable_terminal_bell:
        methods_tried.append("bell")
        _terminal_bell()
        methods_success.append("bell")

    # 4. External Channels via NotificationManager
    try:
        from .notifications import manager

        # Exclude 'desktop' to prevent infinite recursion (since manager._send_desktop calls this function)
        results = manager.send(
            title, message, notification_type.value, exclude_channels=["desktop"]
        )

        if "slack" in results and results["slack"]:
            methods_tried.append("slack")
            methods_success.append("slack")

        if "discord" in results and results["discord"]:
            methods_tried.append("discord")
            methods_success.append("discord")

    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"External notification failed: {e}")

    return {
        "status": "success" if methods_success else "partial",
        "title": title,
        "message": message,
        "type": notification_type.value,
        "methods_tried": methods_tried,
        "methods_success": methods_success,
    }


def done(task_name: str = "AI Task", success: bool = True, details: str = "") -> dict:
    """
    Quick helper for task completion notification.

    Args:
        task_name: Name of the completed task
        success: Whether the task succeeded
        details: Additional details

    Returns:
        Notification result
    """
    if success:
        title = f"✅ {task_name} Complete!"
        message = details or "Ready for your review."
        ntype = NotificationType.SUCCESS
    else:
        title = f"❌ {task_name} Failed"
        message = details or "Check the logs for details."
        ntype = NotificationType.ERROR

    return notify(title=title, message=message, notification_type=ntype)


# Convenience aliases
notify_done = done
boring_done = done
