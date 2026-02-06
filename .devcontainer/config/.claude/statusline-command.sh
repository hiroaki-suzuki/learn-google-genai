#!/bin/bash

# Read JSON input from stdin
input=$(cat)

# Extract information from JSON
cwd=$(echo "$input" | jq -r '.workspace.current_dir')
model=$(echo "$input" | jq -r '.model.display_name')
output_style=$(echo "$input" | jq -r '.output_style.name')
remaining=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
total_tokens=$(echo "$input" | jq -r '.context_window.context_window_size // empty')
cost=$(echo "$input" | jq -r '.cost.total_cost_usd // empty')

# Build status line components
status_parts=()

# Add current directory (basename only for brevity)
dir_name=$(basename "$cwd")
status_parts+=("$(printf '\033[36m%s\033[0m' "$dir_name")")

# Add model name
status_parts+=("$(printf '\033[35m%s\033[0m' "$model")")

# Add output style if not default
if [ "$output_style" != "default" ]; then
    status_parts+=("$(printf '\033[33m%s\033[0m' "$output_style")")
fi

# Add context usage if available
if [ -n "$remaining" ]; then
    remaining_int=${remaining%.*}

    if [ "$remaining_int" -gt 50 ]; then
        color='\033[32m'  # Green
    elif [ "$remaining_int" -gt 20 ]; then
        color='\033[33m'  # Yellow
    else
        color='\033[31m'  # Red
    fi

    # Format total tokens (e.g., 200000 -> 200k)
    total_fmt=""
    if [ -n "$total_tokens" ]; then
        total_fmt=$(awk "BEGIN { t=$total_tokens; if (t>=1000) printf \"%.0fk\", t/1000; else printf \"%d\", t }")
    fi

    # Calculate used tokens from percentage
    used_fmt=""
    if [ -n "$used_pct" ] && [ -n "$total_tokens" ]; then
        used_fmt=$(awk "BEGIN { u=$used_pct * $total_tokens / 100; if (u>=1000) printf \"%.1fk\", u/1000; else printf \"%.0f\", u }")
    fi

    if [ -n "$used_fmt" ] && [ -n "$total_fmt" ]; then
        status_parts+=("$(printf "${color}ctx: %.0f%% (%s/%s)\033[0m" "$remaining" "$used_fmt" "$total_fmt")")
    else
        status_parts+=("$(printf "${color}ctx: %.0f%%\033[0m" "$remaining")")
    fi
fi

# Add session cost
if [ -n "$cost" ]; then
    cost_fmt=$(printf '$%.2f' "$cost")
    status_parts+=("$(printf '\033[33m%s\033[0m' "$cost_fmt")")
fi

# Join all parts with separator
printf "%s" "${status_parts[0]}"
for i in "${status_parts[@]:1}"; do
    printf " | %s" "$i"
done
