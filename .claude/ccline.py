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


# ANSI color codes
RESET = "\033[0m"
CYAN = "\033[1;36m"
YELLOW = "\033[1;33m"
GREEN = "\033[1;32m"
MAGENTA = "\033[1;35m"

# Model context window limit
MODEL_CONTEXT_LIMIT = 200000


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

        output = render_statusline(segments)
        print(output)

    except (json.JSONDecodeError, KeyError, Exception):
        print(f"{CYAN}Claude Code{RESET}")


if __name__ == "__main__":
    main()
