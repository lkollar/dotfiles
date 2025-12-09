#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""
CCometixLine - Simple Python implementation of Claude Code status line.
Reads JSON from stdin and outputs a formatted ANSI-colored status line.

Run the included test suite with 'python3 -m unittest -v ccline'.
"""

import json
import os
import platform
import subprocess
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


# ANSI color codes
RESET = "\033[0m"
CYAN = "\033[1;36m"
YELLOW = "\033[1;33m"
GREEN = "\033[1;32m"
MAGENTA = "\033[1;35m"
RED = "\033[1;31m"

# Model context window limit
MODEL_CONTEXT_LIMIT = 200000

# Usage API caching
CACHE_FILE = Path.home() / ".claude" / "ccline" / ".usage_cache.json"
CACHE_TTL = timedelta(minutes=5)


def is_zai_endpoint() -> bool:
    """Check if using z.ai API endpoint."""
    base_url = os.getenv("ANTHROPIC_BASE_URL", "")
    return "z.ai" in base_url


def get_model_display_name(model_id: str) -> str:
    """Map model ID to simplified display name."""
    if is_zai_endpoint():
        return "GLM 4.6"
    elif "sonnet-4" in model_id:
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
        (percentage, formatted_tokens) if valid assistant/summary message with tokens, None otherwise
    """
    try:
        entry = json.loads(line)
        entry_type = entry.get("type")

        # Handle both assistant messages and summary entries
        if entry_type in ("assistant", "summary"):
            usage = entry.get("message", {}).get("usage", {})

            # Include all token types (matching CCometixLine's display_tokens behavior)
            total_tokens = (
                usage.get("input_tokens", 0) +
                usage.get("output_tokens", 0) +
                usage.get("cache_creation_input_tokens", 0) +
                usage.get("cache_read_input_tokens", 0)
            )

            if total_tokens == 0:
                return None

            percentage = (total_tokens / MODEL_CONTEXT_LIMIT) * 100
            tokens_fmt = f"{total_tokens/1000:.1f}k" if total_tokens >= 1000 else str(total_tokens)
            return percentage, tokens_fmt
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def format_reset_time(iso_time: str | None) -> str:
    """Format ISO timestamp as time remaining (e.g., '3 hr 36 min').

    Args:
        iso_time: ISO 8601 timestamp (e.g., "2025-12-05T20:15:00Z")

    Returns:
        Formatted time remaining (e.g., "3 hr 36 min", "45 min", or "?" if invalid)
    """
    if not iso_time:
        return "?"

    try:
        # Parse ISO timestamp and calculate time remaining
        dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo)
        remaining = dt - now

        # Handle past times
        if remaining.total_seconds() <= 0:
            return "0 min"

        total_minutes = int(remaining.total_seconds() / 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60

        if hours > 0:
            return f"{hours} hr {minutes} min"
        else:
            return f"{minutes} min"
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

        if not lines:
            return 0.0, "0"

        # First check if last line is a summary (Claude Code writes cumulative usage here)
        last_line = lines[-1].strip()
        if last_line:
            try:
                entry = json.loads(last_line)
                if entry.get("type") == "summary":
                    # Summary contains cumulative usage - use it!
                    result = parse_transcript_line(last_line)
                    if result is not None:
                        return result
            except (json.JSONDecodeError, KeyError):
                pass

        # Fallback: Look through last 50 lines for most recent assistant message
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
        # Use red color for z.ai models, cyan for Anthropic models
        model_color = RED if is_zai_endpoint() else CYAN
        parts.append(f"{model_color}🤖 {segments['model']}{RESET}")

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
        parts.append(f"{MAGENTA}⏱️ {pct}% · resets in {reset}{RESET}")

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
        # Only show for Anthropic API, not for z.ai
        if not is_zai_endpoint():
            usage_data = get_api_usage()
            if usage_data:
                segments["usage_percent"], segments["usage_reset"] = usage_data

        output = render_statusline(segments)
        print(output)

    except (json.JSONDecodeError, KeyError, Exception):
        print(f"{CYAN}Claude Code{RESET}")


# ============================================================================
# TESTS - Run with: python -m unittest ccline
# ============================================================================


class TestZaiDetection(unittest.TestCase):
    """Test is_zai_endpoint()"""

    def setUp(self):
        # Store original value
        self.original_base_url = os.environ.get("ANTHROPIC_BASE_URL")

    def tearDown(self):
        # Restore original value
        if self.original_base_url is not None:
            os.environ["ANTHROPIC_BASE_URL"] = self.original_base_url
        elif "ANTHROPIC_BASE_URL" in os.environ:
            del os.environ["ANTHROPIC_BASE_URL"]

    def test_zai_endpoint_detected(self):
        os.environ["ANTHROPIC_BASE_URL"] = "https://api.z.ai/api/anthropic"
        self.assertTrue(is_zai_endpoint())

    def test_anthropic_endpoint_not_detected(self):
        os.environ["ANTHROPIC_BASE_URL"] = "https://api.anthropic.com"
        self.assertFalse(is_zai_endpoint())

    def test_unset_endpoint_not_detected(self):
        if "ANTHROPIC_BASE_URL" in os.environ:
            del os.environ["ANTHROPIC_BASE_URL"]
        self.assertFalse(is_zai_endpoint())

    def test_empty_endpoint_not_detected(self):
        os.environ["ANTHROPIC_BASE_URL"] = ""
        self.assertFalse(is_zai_endpoint())


class TestModelMappingWithZai(unittest.TestCase):
    """Test get_model_display_name() with z.ai detection"""

    def setUp(self):
        # Store original value
        self.original_base_url = os.environ.get("ANTHROPIC_BASE_URL")

    def tearDown(self):
        # Restore original value
        if self.original_base_url is not None:
            os.environ["ANTHROPIC_BASE_URL"] = self.original_base_url
        elif "ANTHROPIC_BASE_URL" in os.environ:
            del os.environ["ANTHROPIC_BASE_URL"]

    def test_zai_returns_glm_model(self):
        os.environ["ANTHROPIC_BASE_URL"] = "https://api.z.ai/api/anthropic"
        result = get_model_display_name("any-model-id")
        self.assertEqual(result, "GLM 4.6")

    def test_anthropic_returns_standard_model(self):
        os.environ["ANTHROPIC_BASE_URL"] = "https://api.anthropic.com"
        result = get_model_display_name("claude-sonnet-4-5-20250929")
        self.assertEqual(result, "Sonnet 4.5")

    def test_unset_returns_standard_model(self):
        if "ANTHROPIC_BASE_URL" in os.environ:
            del os.environ["ANTHROPIC_BASE_URL"]
        result = get_model_display_name("claude-opus-4-5")
        self.assertEqual(result, "Opus 4.5")


class TestModelMapping(unittest.TestCase):
    """Test get_model_display_name()"""

    def setUp(self):
        # Store original value and ensure z.ai is not set for these tests
        self.original_base_url = os.environ.get("ANTHROPIC_BASE_URL")
        if "ANTHROPIC_BASE_URL" in os.environ:
            del os.environ["ANTHROPIC_BASE_URL"]

    def tearDown(self):
        # Restore original value
        if self.original_base_url is not None:
            os.environ["ANTHROPIC_BASE_URL"] = self.original_base_url
        elif "ANTHROPIC_BASE_URL" in os.environ:
            del os.environ["ANTHROPIC_BASE_URL"]

    def test_sonnet_4(self):
        self.assertEqual(get_model_display_name("claude-sonnet-4-5-20250929"), "Sonnet 4.5")

    def test_opus_4(self):
        self.assertEqual(get_model_display_name("claude-opus-4-5"), "Opus 4.5")

    def test_sonnet_3_5(self):
        self.assertEqual(get_model_display_name("claude-3-5-sonnet-20241022"), "Sonnet 3.5")

    def test_haiku(self):
        self.assertEqual(get_model_display_name("claude-3-haiku"), "Haiku")

    def test_fallback(self):
        self.assertEqual(get_model_display_name("unknown-model"), "Claude")


class TestDirectoryName(unittest.TestCase):
    """Test get_directory_name()"""

    def test_unix_path(self):
        self.assertEqual(get_directory_name("/Users/test/project"), "project")

    def test_windows_path(self):
        # Note: On Unix systems, Path won't parse Windows paths correctly
        # This tests the function's behavior, which returns the last component
        result = get_directory_name("C:\\Users\\test\\project")
        # On Windows: "project", on Unix: full path (no parsing)
        self.assertIn("project", result)

    def test_single_component(self):
        self.assertEqual(get_directory_name("project"), "project")


class TestTranscriptParsing(unittest.TestCase):
    """Test parse_transcript_line()"""

    def test_valid_assistant_all_tokens(self):
        line = '{"type":"assistant","message":{"usage":{"input_tokens":1000,"output_tokens":2000,"cache_creation_input_tokens":500,"cache_read_input_tokens":300}}}'
        pct, tokens = parse_transcript_line(line)
        self.assertEqual(pct, 1.9)  # 3800/200000 * 100
        self.assertEqual(tokens, "3.8k")

    def test_valid_assistant_basic_tokens(self):
        line = '{"type":"assistant","message":{"usage":{"input_tokens":100,"output_tokens":50}}}'
        pct, tokens = parse_transcript_line(line)
        self.assertEqual(pct, 0.075)  # 150/200000 * 100
        self.assertEqual(tokens, "150")

    def test_summary_entry(self):
        # Summary entries contain cumulative token usage
        line = '{"type":"summary","message":{"usage":{"input_tokens":50000,"output_tokens":30000,"cache_creation_input_tokens":10000,"cache_read_input_tokens":5000}}}'
        pct, tokens = parse_transcript_line(line)
        self.assertEqual(pct, 47.5)  # 95000/200000 * 100
        self.assertEqual(tokens, "95.0k")

    def test_user_message(self):
        line = '{"type":"user","message":{"content":"hello"}}'
        result = parse_transcript_line(line)
        self.assertIsNone(result)

    def test_zero_tokens(self):
        line = '{"type":"assistant","message":{"usage":{"input_tokens":0,"output_tokens":0}}}'
        result = parse_transcript_line(line)
        self.assertIsNone(result)

    def test_invalid_json(self):
        result = parse_transcript_line("not json")
        self.assertIsNone(result)


class TestResetTimeFormatting(unittest.TestCase):
    """Test format_reset_time()"""

    def test_none_input(self):
        self.assertEqual(format_reset_time(None), "?")

    def test_valid_timestamp_future(self):
        # Test with a future timestamp (3 hours 36 minutes from now)
        future = datetime.now().astimezone() + timedelta(hours=3, minutes=36)
        iso_time = future.isoformat()
        result = format_reset_time(iso_time)
        # Should show hours and minutes
        self.assertRegex(result, r"\d+ hr \d+ min")

    def test_valid_timestamp_minutes_only(self):
        # Test with a timestamp less than 1 hour away
        future = datetime.now().astimezone() + timedelta(minutes=45)
        iso_time = future.isoformat()
        result = format_reset_time(iso_time)
        self.assertRegex(result, r"\d+ min")

    def test_past_timestamp(self):
        # Test with a past timestamp
        past = datetime.now().astimezone() - timedelta(hours=1)
        iso_time = past.isoformat()
        result = format_reset_time(iso_time)
        self.assertEqual(result, "0 min")

    def test_invalid_timestamp(self):
        self.assertEqual(format_reset_time("invalid"), "?")


class TestRendering(unittest.TestCase):
    """Test render_statusline()"""

    def test_all_segments(self):
        segments = {
            "model": "Sonnet 4.5",
            "directory": "project",
            "git_branch": "main",
            "git_status": "✓",
            "context_pct": 10.5,
            "tokens": "21.1k",
            "usage_percent": 42,
            "usage_reset": "3 hr 36 min"
        }
        result = render_statusline(segments)
        self.assertIn("Sonnet 4.5", result)
        self.assertIn("project", result)
        self.assertIn("main", result)
        self.assertIn("10.5%", result)
        self.assertIn("21.1k", result)
        self.assertIn("42%", result)
        self.assertIn("resets in", result)
        self.assertIn("|", result)

    def test_partial_segments(self):
        segments = {"model": "Claude", "directory": "test"}
        result = render_statusline(segments)
        self.assertIn("Claude", result)
        self.assertIn("test", result)
        self.assertNotIn("git", result)

    def test_empty_segments(self):
        result = render_statusline({})
        self.assertEqual(result, "")

    def test_ansi_colors_present(self):
        segments = {"model": "Claude"}
        result = render_statusline(segments)
        self.assertIn("\033[", result)  # ANSI escape code
        self.assertIn("\033[0m", result)  # Reset code

    def test_zai_uses_red_color(self):
        # Mock z.ai endpoint
        import unittest.mock
        with unittest.mock.patch('ccline.is_zai_endpoint', return_value=True):
            segments = {"model": "GLM 4.6"}
            result = render_statusline(segments)
            self.assertIn(RED, result)
            self.assertNotIn(CYAN, result)

    def test_anthropic_uses_cyan_color(self):
        # Mock Anthropic endpoint
        import unittest.mock
        with unittest.mock.patch('ccline.is_zai_endpoint', return_value=False):
            segments = {"model": "Sonnet 4.5"}
            result = render_statusline(segments)
            self.assertIn(CYAN, result)
            self.assertNotIn(RED, result)


if __name__ == "__main__":
    main()
