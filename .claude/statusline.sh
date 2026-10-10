#!/usr/bin/env bash
# Claude Code statusline: dir · branch · model · tokens · 5h free · ctx used

input=$(cat)
j() { jq -r "$1 // empty" <<<"$input"; }

c() { printf '\033[38;2;%sm%s\033[0m' "$1" "$2"; }
sep=$(c "100;100;100" " · ")

dir=$(j .workspace.current_dir)
[ -z "$dir" ] && dir=$(j .cwd)
short=${dir/#$HOME/\~}
# fish-style: abbreviate all but last component
short=$(awk -F/ -v OFS=/ '{ for (i=1;i<NF;i++) $i = ($i ~ /^~?$/) ? $i : substr($i,1,1); print }' <<<"$short")

branch=$(git -C "$dir" branch --show-current 2>/dev/null)
model=$(j .model.display_name)
tokens=$(jq -r '((.context_window.total_input_tokens // 0) + (.context_window.total_output_tokens // 0))
  | if . >= 1000000 then "\(.*10/1000000|floor/10)M" elif . >= 1000 then "\(.*10/1000|floor/10)K" else tostring end' <<<"$input")

five_used=$(j .rate_limits.five_hour.used_percentage)
five_reset=$(j .rate_limits.five_hour.resets_at)
ctx_used=$(j .context_window.used_percentage)

# prompt cache time left: TTL minus time since last assistant message
cache_left=""
tp=$(j .transcript_path)
if [ -n "$tp" ] && [ -r "$tp" ]; then
  cache_left=$(tail -n 60 "$tp" | jq -Rs '
    split("\n") | map(fromjson? | select(.type == "assistant" and .timestamp)) as $a
    | if ($a | length) == 0 then empty else
        ($a | last | .timestamp | sub("\\.[0-9]+"; "") | fromdateiso8601) as $ts
        | ([$a[] | .message.usage.cache_creation // {}
            | if (.ephemeral_1h_input_tokens // 0) > 0 then 3600
              elif (.ephemeral_5m_input_tokens // 0) > 0 then 300 else empty end] | last // 3600) as $ttl
        | ($ttl - (now - $ts)) | floor
      end' 2>/dev/null)
fi

out=$(c "205;133;63" "$short")
[ -n "$branch" ] && out+="$sep$(c "135;206;235" " $branch")"
[ -n "$model" ] && out+="$sep$(c "255;255;255" "✱ $model")"
[ -n "$tokens" ] && [ "$tokens" != "0" ] && out+="$sep$(c "0;255;255" "§ $tokens tokens")"

if [ -n "$five_used" ]; then
  free=$(jq -n --argjson u "$five_used" '100 - $u | round')
  txt="◱ ${free}% free"
  if [ -n "$five_reset" ]; then
    t=$(LC_ALL=C date -r "$five_reset" '+%-I:%M%p' 2>/dev/null || LC_ALL=C date -d "@$five_reset" '+%-I:%M%p')
    txt+=" → $(tr 'APM' 'apm' <<<"$t")"
  fi
  out+="$sep$(c "152;251;152" "$txt")"
fi

if [ -n "$ctx_used" ]; then
  out+="$sep$(c "203;213;224" "◔ $(printf '%.0f' "$ctx_used")% ctx")"
fi

if [ -n "$cache_left" ]; then
  if [ "$cache_left" -le 0 ]; then
    out+="$sep$(c "220;100;100" "◴ cold")"
  else
    col="152;251;152"
    [ "$cache_left" -le 60 ] && col="250;189;47"
    out+="$sep$(c "$col" "◴ $(((cache_left + 59) / 60))m")"
  fi
fi

printf '%s\n' "$out"
