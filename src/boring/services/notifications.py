# Copyright 2026 Boring for Gemini Authors
# SPDX-License-Identifier: Apache-2.0

"""
System Notification Manager (V14.1)

Provides a unified interface for sending notifications across multiple channels
(Desktop, Slack, Discord, Email).

This module is the canonical implementation for Phase 6.4.
"""

import logging
from dataclasses import dataclass
from enum import Enum

from boring.core.config import settings

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class NotificationChannelConfig:
    enabled: bool = True
    webhook_url: str | None = None
    recipient: str | None = None


class NotificationManager:
    """
    Central manager for dispatching notifications to configured channels.
    """

    def __init__(self):
        self.config = {
            "slack": NotificationChannelConfig(
                enabled=settings.NOTIFICATIONS_ENABLED, webhook_url=settings.SLACK_WEBHOOK
            ),
            "discord": NotificationChannelConfig(
                enabled=settings.NOTIFICATIONS_ENABLED, webhook_url=settings.DISCORD_WEBHOOK
            ),
            "email": NotificationChannelConfig(
                enabled=settings.NOTIFICATIONS_ENABLED, recipient=settings.EMAIL_NOTIFY
            ),
            "line": NotificationChannelConfig(
                enabled=settings.NOTIFICATIONS_ENABLED, webhook_url=settings.LINE_NOTIFY_TOKEN
            ),
            "messenger": NotificationChannelConfig(
                enabled=settings.NOTIFICATIONS_ENABLED, webhook_url=settings.MESSENGER_ACCESS_TOKEN
            ),
            "desktop": NotificationChannelConfig(enabled=settings.NOTIFICATIONS_ENABLED),
        }

    def send(
        self,
        title: str,
        message: str,
        level: str = "info",
        exclude_channels: list[str] | None = None,
    ) -> dict[str, bool]:
        """
        Send a notification to all enabled channels.

        Args:
            title: The title of the notification
            message: The body of the notification
            level: 'info', 'success', 'warning', 'error'
            exclude_channels: List of channels to skip (e.g. ['desktop'])

        Returns:
            Dictionary mapping channel names to success status
        """
        results = {}
        exclude = set(exclude_channels) if exclude_channels else set()

        # Normalize level
        try:
            ntype = NotificationType(level)
        except ValueError:
            ntype = NotificationType.INFO

        # 1. Desktop Notification
        if "desktop" not in exclude and self.config["desktop"].enabled:
            results["desktop"] = self._send_desktop(title, message, ntype)

        # 2. Slack
        if "slack" not in exclude and self.config["slack"].webhook_url:
            results["slack"] = self._send_slack(title, message, ntype)

        # 3. Discord
        if "discord" not in exclude and self.config["discord"].webhook_url:
            results["discord"] = self._send_discord(title, message, ntype)

        # 4. Email (Gmail/SMTP)
        if "email" not in exclude and self.config["email"].recipient:
            results["email"] = self._send_email(title, message, ntype)

        # 5. LINE
        if "line" not in exclude and self.config["line"].webhook_url:
            results["line"] = self._send_line(title, message, ntype)

        # 6. Messenger
        if "messenger" not in exclude and self.config["messenger"].webhook_url:
            results["messenger"] = self._send_messenger(title, message, ntype)

        return results

    def _send_desktop(self, title: str, message: str, ntype: NotificationType) -> bool:
        """Send desktop notification via notifier backend or direct system calls."""
        try:
            from .notifier import notify as legacy_notify

            legacy_notify(title, message, ntype)
            return True
        except Exception as e:
            logger.debug(f"Desktop notification failed: {e}")
            return False

    def _send_slack(self, title: str, message: str, ntype: NotificationType) -> bool:
        """Send to Slack."""
        url = self.config["slack"].webhook_url
        if not url:
            return False

        try:
            import requests

            colors = {
                NotificationType.SUCCESS: "#2eb67d",
                NotificationType.ERROR: "#e01e5a",
                NotificationType.WARNING: "#ecb22e",
                NotificationType.INFO: "#36a64f",
            }

            payload = {
                "attachments": [
                    {
                        "fallback": f"{title}: {message}",
                        "color": colors.get(ntype, "#36a64f"),
                        "title": title,
                        "text": message,
                        "footer": "Boring-Gemini",
                    }
                ]
            }

            requests.post(url, json=payload, timeout=5)
            return True
        except Exception as e:
            logger.warning(f"Slack webhook failed: {e}")
            return False

    def _send_discord(self, title: str, message: str, ntype: NotificationType) -> bool:
        """Send to Discord."""
        url = self.config["discord"].webhook_url
        if not url:
            return False

        try:
            import requests

            colors = {
                NotificationType.SUCCESS: 3066993,
                NotificationType.ERROR: 15158332,
                NotificationType.WARNING: 16776960,
                NotificationType.INFO: 3447003,
            }

            payload = {
                "embeds": [
                    {
                        "title": title,
                        "description": message,
                        "color": colors.get(ntype, 3447003),
                        "footer": {"text": "Boring-Gemini"},
                    }
                ]
            }

            requests.post(url, json=payload, timeout=5)
            return True
        except Exception as e:
            logger.warning(f"Discord webhook failed: {e}")
            return False

    def _send_email(self, title: str, message: str, ntype: NotificationType) -> bool:
        """Send email via SMTP (Gmail support)."""
        recipient = self.config["email"].recipient
        if not recipient or not settings.GMAIL_USER or not settings.GMAIL_PASSWORD:
            return False

        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            msg = MIMEMultipart()
            msg["From"] = settings.GMAIL_USER
            msg["To"] = recipient
            msg["Subject"] = f"[{ntype.value.upper()}] {title}"
            body = f"{message}\n\n--\nSent by Boring-Gemini"
            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(settings.GMAIL_USER, settings.GMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            logger.warning(f"Email notification failed: {e}")
            return False

    def _send_line(self, title: str, message: str, ntype: NotificationType) -> bool:
        """Send to LINE via LINE Notify."""
        token = self.config["line"].webhook_url  # Used as token
        if not token:
            return False

        try:
            import requests

            url = "https://notify-api.line.me/api/notify"
            headers = {"Authorization": f"Bearer {token}"}
            data = {"message": f"\n[{ntype.value.upper()}] {title}\n{message}"}
            requests.post(url, headers=headers, data=data, timeout=5)
            return True
        except Exception as e:
            logger.warning(f"LINE notification failed: {e}")
            return False

    def _send_messenger(self, title: str, message: str, ntype: NotificationType) -> bool:
        """Send to Messenger via Meta Graph API."""
        token = self.config["messenger"].webhook_url  # Access Token
        recipient_id = settings.MESSENGER_RECIPIENT_ID
        if not token or not recipient_id:
            return False

        try:
            import requests

            url = f"https://graph.facebook.com/v19.0/me/messages?access_token={token}"
            payload = {
                "recipient": {"id": recipient_id},
                "message": {"text": f"[{ntype.value.upper()}] {title}\n{message}"},
            }
            requests.post(url, json=payload, timeout=5)
            return True
        except Exception as e:
            logger.warning(f"Messenger notification failed: {e}")
            return False


# Global Instance
manager = NotificationManager()
