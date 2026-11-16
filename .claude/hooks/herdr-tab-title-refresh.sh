#!/usr/bin/env bash
# SessionStart: poke the lkk.auto-tab-title herdr plugin so /clear and
# /resume on an idle pane reset the tab title immediately. Herdr emits no
# plugin-hookable event for a session switch without a status change.
#
# Waits (detached) until herdr-agent-state.sh has reported the new session
# for this pane, then invokes the plugin's refresh action. Never blocks or
# fails Claude.

[[ "${HERDR_ENV:-}" == 1 && -n "${HERDR_PANE_ID:-}" ]] || exit 0
herdr_bin=$(command -v herdr 2>/dev/null) || exit 0

session=""
if command -v jq >/dev/null 2>&1; then
    session=$(jq -r '.session_id // empty' 2>/dev/null)
else
    cat >/dev/null
fi

(
    for _ in $(seq 1 20); do
        [[ -z "$session" ]] && { sleep 1; break; }
        cur=$("$herdr_bin" pane get "$HERDR_PANE_ID" 2>/dev/null |
            jq -r '.result.pane.agent_session.value // empty' 2>/dev/null)
        [[ "$cur" == "$session" ]] && break
        sleep 0.25
    done
    "$herdr_bin" plugin action invoke lkk.auto-tab-title.refresh
) </dev/null >/dev/null 2>&1 &
disown 2>/dev/null
exit 0
