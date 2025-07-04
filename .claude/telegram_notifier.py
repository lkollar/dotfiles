#!/usr/bin/env python3
"""
Telegram notifier for Claude Code hooks
Sends notifications when Claude stops or needs attention
"""

import json
import sys
import os
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime


def send_telegram_message(message, bot_token, chat_id):
    """Send a message to Telegram via bot API"""
    if not bot_token or not chat_id:
        print("Error: Missing bot token or chat ID", file=sys.stderr)
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}

    try:
        data = urllib.parse.urlencode(params).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                return True
            else:
                response_text = response.read().decode("utf-8")
                print(
                    f"Telegram API error: {response.status} - {response_text}",
                    file=sys.stderr,
                )
                return False
    except urllib.error.URLError as e:
        print(f"Failed to send Telegram message: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return False


def main():
    # Read configuration from environment variables
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print(
            "Error: Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables",
            file=sys.stderr,
        )
        sys.exit(1)

    # Read hook input from stdin
    try:
        hook_input = json.loads(sys.stdin.read()) if sys.stdin.isatty() == False else {}
    except json.JSONDecodeError:
        hook_input = {}

    # Get hook type and context
    hook_type = hook_input.get("type", "unknown")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create notification message based on hook type
    if hook_type == "Stop":
        message = (
            f"🤖 *Claude Code Alert*\n\n"
            f"Claude has finished responding and may need your attention.\n\n"
            f"Time: `{timestamp}`\n"
            f"Working directory: `{os.getcwd()}`"
        )
    elif hook_type == "Notification":
        notification_text = hook_input.get("notification", "No details provided")
        message = (
            f"🔔 *Claude Code Notification*\n\n"
            f"{notification_text}\n\n"
            f"Time: `{timestamp}`"
        )
    else:
        message = (
            f"📢 *Claude Code Hook*\n\n"
            f"Hook type: `{hook_type}`\n"
            f"Time: `{timestamp}`\n"
            f"Working directory: `{os.getcwd()}`"
        )

    # Send the message
    if send_telegram_message(message, bot_token, chat_id):
        print("Notification sent successfully")
    else:
        print("Failed to send notification", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
