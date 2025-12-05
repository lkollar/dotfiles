#!/bin/bash

# Read JSON input from stdin
input=$(cat)

# Extract values from JSON
current_dir=$(echo "$input" | jq -r '.workspace.current_dir')
model_name=$(echo "$input" | jq -r '.model.display_name')
output_style=$(echo "$input" | jq -r '.output_style.name')
transcript_path=$(echo "$input" | jq -r '.transcript_path')

# Get directory name (basename of current directory)
dir_name=$(basename "$current_dir")

# Get git branch and status (if in a git repo)
git_info=""
if git -C "$current_dir" rev-parse --git-dir > /dev/null 2>&1; then
    branch=$(git -C "$current_dir" --no-optional-locks branch --show-current 2>/dev/null)

    # Check for modifications and untracked files
    status_indicators=""
    if ! git -C "$current_dir" --no-optional-locks diff --quiet 2>/dev/null || \
       ! git -C "$current_dir" --no-optional-locks diff --cached --quiet 2>/dev/null; then
        status_indicators="${status_indicators}*"
    fi
    if [ -n "$(git -C "$current_dir" --no-optional-locks ls-files --others --exclude-standard 2>/dev/null)" ]; then
        status_indicators="${status_indicators}+"
    fi

    if [ -n "$branch" ]; then
        git_info=$(printf "\033[90m%s%s\033[0m " "$branch" "$status_indicators")
    fi
fi

# Get context usage percentage from transcript
context_usage=""
if [ -f "$transcript_path" ]; then
    # Get the last message's token usage (represents cumulative context)
    last_line=$(tail -1 "$transcript_path")

    # Extract input tokens (including cached)
    input=$(echo "$last_line" | jq -r '.message.usage.input_tokens // 0')
    cache_read=$(echo "$last_line" | jq -r '.message.usage.cache_read_input_tokens // 0')
    cache_creation=$(echo "$last_line" | jq -r '.message.usage.cache_creation_input_tokens // 0')
    output=$(echo "$last_line" | jq -r '.message.usage.output_tokens // 0')

    # Total tokens in context (input + cache represents the full context window)
    total_tokens=$((input + cache_read + cache_creation + output))
    context_limit=200000  # Sonnet 4.5 context limit

    if [ "$total_tokens" -gt 0 ]; then
        percentage=$((total_tokens * 100 / context_limit))
        context_usage="${percentage}% "
    fi
fi

# Build output style info (only if not default)
style_info=""
if [ "$output_style" != "default" ] && [ "$output_style" != "null" ]; then
    style_info="[$output_style] "
fi

# Assemble the status line with blue directory name
printf "\033[34m%s\033[0m %s%s %s%s\n" \
    "$dir_name" \
    "$git_info" \
    "$model_name" \
    "$style_info" \
    "$context_usage"
