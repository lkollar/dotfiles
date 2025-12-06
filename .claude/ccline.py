#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""
CCometixLine - Simple Python implementation of Claude Code status line.
Reads JSON from stdin and outputs a formatted ANSI-colored status line.
"""

import json
import subprocess
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


# ANSI color codes
RESET = "\033[0m"
CYAN = "\033[1;36m"
YELLOW = "\033[1;33m"
GREEN = "\033[1;32m"
MAGENTA = "\033[1;35m"

# Model context window limit
MODEL_CONTEXT_LIMIT = 200000

# Usage API caching
CACHE_FILE = Path.home() / ".claude" / "ccline" / ".usage_cache.json"
CACHE_TTL = timedelta(minutes=5)


def get_model_display_name(model_id: str) -> str:
    """Map model ID to simplified display name."""
    if "sonnet-4" in model_id:
        return "Sonnet 4.5"
    elif "opus-4" in model_id:
        return "Opus 4.5"
    elif "3-5-sonnet" in model_id:
        return "Sonnet 3.5"
    elif "haiku" in model_id:
        return "Haiku"
    return "Claude"


def get_directory_name(current_dir: str) -> str:
    """Extract directory basename from full path."""
    return Path(current_dir).name


def get_oauth_token() -> str | None:
    """Extract OAuth token from Claude Code credentials.

    Returns:
        OAuth access token or None if unavailable
    """
    # Try macOS Keychain first
    if platform.system() == "Darwin":
        try:
            result = subprocess.run(
                ["security", "find-generic-password", "-a", os.getenv("USER", "user"),
                 "-w", "-s", "Claude Code-credentials"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                creds = json.loads(result.stdout.strip())
                return creds.get("claudeAiOauth", {}).get("accessToken")
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            pass

    # Fallback: Read from file
    try:
        creds_path = Path.home() / ".claude" / ".credentials.json"
        if creds_path.exists():
            creds = json.loads(creds_path.read_text())
            return creds.get("claudeAiOauth", {}).get("accessToken")
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass

    return None


def get_git_info() -> tuple[str, str]:
    """Get git branch and clean/dirty status.

    Returns:
        (branch_name, status_indicator) - status is "✓" for clean or "●" for dirty
    """
    try:
        # Get current branch
        branch_result = subprocess.run(
            ["git", "--no-optional-locks", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True,
            timeout=2
        )
        branch = branch_result.stdout.strip()

        if not branch:
            return "", ""

        # Get status (clean vs dirty)
        status_result = subprocess.run(
            ["git", "--no-optional-locks", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=2
        )
        status = status_result.stdout.strip()

        indicator = "✓" if not status else "●"
        return branch, indicator
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        return "", ""


def parse_transcript_line(line: str) -> tuple[float, str] | None:
    """Parse JSONL line and calculate context window percentage.

    Returns:
        (percentage, formatted_tokens) if valid assistant message with tokens, None otherwise
    """
    try:
        entry = json.loads(line)
        if entry.get("type") == "assistant":
            usage = entry.get("message", {}).get("usage", {})
            total_tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)

            if total_tokens == 0:
                return None

            percentage = (total_tokens / MODEL_CONTEXT_LIMIT) * 100
            tokens_fmt = f"{total_tokens/1000:.1f}k" if total_tokens >= 1000 else str(total_tokens)
            return percentage, tokens_fmt
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def format_reset_time(iso_time: str | None) -> str:
    """Format ISO timestamp to M-D-H format.

    Args:
        iso_time: ISO 8601 timestamp (e.g., "2025-12-05T20:15:00Z")

    Returns:
        Formatted time (e.g., "12-5-14" for Dec 5, 14:00 local time)
    """
    if not iso_time:
        return "?"

    try:
        # Parse ISO timestamp and convert to local time
        dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        local_dt = dt.astimezone()

        # Round up if minutes > 45
        if local_dt.minute > 45:
            local_dt = local_dt + timedelta(hours=1)

        return f"{local_dt.month}-{local_dt.day}-{local_dt.hour}"
    except (ValueError, AttributeError):
        return "?"


def get_context_info(transcript_path: str) -> tuple[float, str]:
    """Parse transcript to get token usage and calculate context window percentage.

    Returns:
        (percentage, formatted_token_count) - e.g., (10.5, "21.1k")
    """
    try:
        transcript = Path(transcript_path)
        if not transcript.exists():
            return 0.0, "0"

        content = transcript.read_text()
        lines = content.strip().split('\n')

        # Look through last 50 lines for most recent assistant message
        for line in reversed(lines[-50:]):
            result = parse_transcript_line(line)
            if result is not None:
                return result

        return 0.0, "0"
    except (FileNotFoundError, IOError):
        return 0.0, "0"


def get_api_usage() -> tuple[int, str] | None:
    """Fetch API usage with 5-minute caching.

    Returns:
        (five_hour_percent, reset_time_formatted) or None if unavailable
    """
    # Check cache validity
    if CACHE_FILE.exists():
        try:
            cache = json.loads(CACHE_FILE.read_text())
            cached_at = datetime.fromisoformat(cache["cached_at"])
            if datetime.now() - cached_at < CACHE_TTL:
                return cache["five_hour_percent"], cache["reset_time"]
        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    # Fetch from API
    token = get_oauth_token()
    if not token:
        return None

    try:
        req = Request("https://api.anthropic.com/api/oauth/usage")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("anthropic-beta", "oauth-2025-04-20")

        with urlopen(req, timeout=3) as response:
            data = json.loads(response.read())

        # Extract data
        five_hour = data["five_hour"]
        utilization = five_hour["utilization"]
        percent = round(utilization)  # API returns percentage already (e.g., 11.0 for 11%)

        # Format reset time (ISO -> M-D-H)
        reset_time = format_reset_time(five_hour.get("resets_at"))

        # Cache result
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps({
            "five_hour_percent": percent,
            "reset_time": reset_time,
            "cached_at": datetime.now().isoformat()
        }))

        return percent, reset_time
    except (URLError, json.JSONDecodeError, KeyError, OSError):
        # Fallback to stale cache if API fails
        if CACHE_FILE.exists():
            try:
                cache = json.loads(CACHE_FILE.read_text())
                return cache["five_hour_percent"], cache["reset_time"]
            except (json.JSONDecodeError, KeyError):
                pass
        return None


def render_statusline(segments: dict) -> str:
    """Render segments into colored status line with separators.

    Args:
        segments: Dict containing optional keys:
            - model: model display name
            - directory: directory name
            - git_branch: branch name
            - git_status: status indicator (✓ or ●)
            - context_pct: context window percentage
            - tokens: formatted token count
            - usage_percent: API usage percentage (5-hour limit)
            - usage_reset: reset time formatted as M-D-H

    Returns:
        Formatted ANSI-colored status line
    """
    parts = []

    if segments.get("model"):
        parts.append(f"{CYAN}🤖 {segments['model']}{RESET}")

    if segments.get("directory"):
        parts.append(f"{YELLOW}📁 {segments['directory']}{RESET}")

    if segments.get("git_branch"):
        branch = segments['git_branch']
        status = segments.get('git_status', '')
        parts.append(f"{GREEN}🌿 {branch} {status}{RESET}")

    if segments.get("context_pct") is not None:
        pct = segments['context_pct']
        tokens = segments.get('tokens', '0')
        parts.append(f"{MAGENTA}⚡ {pct:.1f}% · {tokens} tokens{RESET}")

    if segments.get("usage_percent") is not None:
        pct = segments["usage_percent"]
        reset = segments.get("usage_reset", "")
        parts.append(f"{MAGENTA}⏱️ {pct}% · {reset}{RESET}")

    return " | ".join(parts)


def main():
    """Main entry point - read JSON from stdin and output status line."""
    try:
        input_data = json.load(sys.stdin)

        model_id = input_data.get("model", {}).get("id", "")
        current_dir = input_data.get("workspace", {}).get("current_dir", "")
        transcript_path = input_data.get("transcript_path", "")

        segments = {}

        if model_id:
            segments["model"] = get_model_display_name(model_id)

        if current_dir:
            segments["directory"] = get_directory_name(current_dir)

        git_branch, git_status = get_git_info()
        if git_branch:
            segments["git_branch"] = git_branch
            segments["git_status"] = git_status

        if transcript_path:
            context_pct, tokens = get_context_info(transcript_path)
            if context_pct > 0:
                segments["context_pct"] = context_pct
                segments["tokens"] = tokens

        # Usage segment (optional - gracefully fails if OAuth unavailable)
        usage_data = get_api_usage()
        if usage_data:
            segments["usage_percent"], segments["usage_reset"] = usage_data

        output = render_statusline(segments)
        print(output)

    except (json.JSONDecodeError, KeyError, Exception):
        print(f"{CYAN}Claude Code{RESET}")


if __name__ == "__main__":
    main()
