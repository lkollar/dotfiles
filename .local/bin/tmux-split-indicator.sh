#!/bin/bash
# tmux-split-indicator.sh
# Displays a split indicator based on the current tmux window layout
# Returns: │ for vertical split, ─ for horizontal split, ▦ for combination

layout="$1"

# If no layout provided, get it from tmux
if [ -z "$layout" ]; then
    layout=$(tmux display-message -p '#{window_layout}')
fi

# Count panes by counting layout identifiers (numbers followed by dimensions)
pane_count=$(tmux display-message -p '#{window_panes}')

# Single pane - no split
if [ "$pane_count" -eq 1 ]; then
    echo ""
    exit 0
fi

# Count container types
horizontal_containers=$(echo "$layout" | tr -cd '{' | wc -c)
vertical_containers=$(echo "$layout" | tr -cd '[' | wc -c)

# Two panes - simple split
if [ "$pane_count" -eq 2 ]; then
    if [ "$horizontal_containers" -gt 0 ] && [ "$vertical_containers" -eq 0 ]; then
        # Only horizontal containers = vertical split (panes side by side)
        echo "│"
    elif [ "$vertical_containers" -gt 0 ] && [ "$horizontal_containers" -eq 0 ]; then
        # Only vertical containers = horizontal split (panes stacked)
        echo "─"
    else
        # Should not happen with 2 panes, but handle it
        echo "▦"
    fi
# Three or more panes or mixed orientation
else
    if [ "$horizontal_containers" -gt 0 ] && [ "$vertical_containers" -gt 0 ]; then
        # Mixed orientation
        echo "▦"
    elif [ "$horizontal_containers" -gt 0 ]; then
        # Multiple vertical splits
        echo "│"
    elif [ "$vertical_containers" -gt 0 ]; then
        # Multiple horizontal splits
        echo "─"
    else
        # Fallback
        echo "▦"
    fi
fi
