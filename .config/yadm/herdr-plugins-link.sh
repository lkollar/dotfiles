#!/usr/bin/env bash
# Register local herdr plugins from ~/.config/herdr-plugins with herdr.
# Herdr's registry is per machine (absolute paths + manifest snapshot), so
# it can't be tracked; re-linking after a pull picks up manifest changes.
# Never fails: must not break yadm.

herdr_bin=$(command -v herdr 2>/dev/null)
if [[ -z "$herdr_bin" && -x "$HOME/.local/bin/herdr" ]]; then
    herdr_bin="$HOME/.local/bin/herdr"
fi
[[ -n "$herdr_bin" ]] || exit 0

if ! command -v uv >/dev/null 2>&1; then
    echo "herdr-plugins-link: uv not found; herdr plugins need it, skipping" >&2
    exit 0
fi

to=()
command -v timeout >/dev/null 2>&1 && to=(timeout 20)

shopt -s nullglob
for manifest in "$HOME"/.config/herdr-plugins/*/herdr-plugin.toml; do
    dir=$(dirname "$manifest")
    if ! out=$("${to[@]}" "$herdr_bin" plugin link "$dir" 2>&1); then
        echo "herdr-plugins-link: failed to link $dir" >&2
        printf '%s\n' "$out" | tail -n 3 >&2
    fi
done
exit 0
