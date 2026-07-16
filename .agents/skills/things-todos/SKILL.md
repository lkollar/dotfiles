---
name: things-todos
description: Manage the user's Things 3 to-dos, projects, areas, tags, Today/Inbox/Anytime/Someday lists, deadlines, scheduling, completion, cancellation, and deletion on macOS via AppleScript. Use when the user asks to create, list, update, move, schedule, complete, cancel, delete, or inspect Things tasks.
version: 3.0.0
---

# Things Todos

Manage Things 3 on the current Mac. Prefer the bundled `things` CLI — it
wraps all common actions and returns JSON. Drop to raw AppleScript only for
workflows the CLI doesn't cover.

Reads and most writes go through AppleScript (NSAppleScript). A few operations
AppleScript can't do — clearing a deadline, appending tags/notes, checklist
items, natural-language dates — route through the Things URL scheme, which needs
a one-time auth token (see Auth token below).

## CLI (preferred)

The skill ships a self-contained `uv` script (`things`) which should be on
PATH. First run fetches `pyobjc` via uv, then it's cached. Invoke it as:

```bash
things today
# If `things` isn't on PATH, call the script directly:
#   ~/.local/bin/things today
```

All commands print JSON to stdout. Todos include: `id`, `name`, `status`,
`notes`, `due` (deadline), `when` (scheduled/start date), `tags`, `project`,
`area`. Use the returned `id` for follow-up mutations — they all act by id.

```
# Read
things today | inbox | anytime | upcoming | someday | logbook
things list "<listName>"
things project "<projectName>"
things projects | areas | tags
things search ["<text>"] [--status open|completed|canceled|any] \
                 [--tag T] [--list L | --project P]
#   text is optional; defaults to --status open. Filters compose (AND).
#   e.g. things search --tag email          things search "review" --project "X"

# Create  (WHEN = YYYY-MM-DD or natural language: "today", "tomorrow",
#          "next tuesday", "today@18:00"; NL dates need the auth token)
things add "<name>" [--notes T] [--list L] [--project P] [--area A] \
                       [--tags "a,b"] [--when WHEN] [--deadline WHEN] \
                       [--checklist "a;b;c"]

# Mutate (by id)
things update <id> [--name N] [--notes T] [--tags "a,b"] [--add-tags "c,d"] \
                  [118;1:3u    [--append-notes T] [--prepend-notes T] \
                      [--when WHEN] [--deadline WHEN] [--clear-deadline] \
                      [--checklist "a;b;c"]
things complete <id> | uncomplete <id> | cancel <id> | delete <id>
things schedule <id> <WHEN>           # set scheduled (start) date
things deadline <id> <WHEN>           # set deadline (due date)
things move <id> (--to-list L | --to-area A | --to-project P)

# Auth token (URL-scheme features only) + escape hatch
things set-token <token>              # store in macOS Keychain
things raw '<applescript source>'     # prints stringValue of the result
```

`--tags` replaces; `--add-tags` appends. `--checklist` items are `;`-separated.
URL-scheme flags (`--add-tags`, `--append-notes`, `--prepend-notes`,
`--clear-deadline`, `--checklist`, NL dates) require the auth token.

Typical flow — find then act:

```bash
ID=$(things search "Buy milk" | python3 -c 'import sys,json;print(json.load(sys.stdin)[0]["id"])')
things complete "$ID"
```

## Notes & gotchas

- App name is `Things3`. Built-in lists: `Inbox`, `Today`, `Anytime`,
  `Upcoming`, `Someday`, `Logbook`, `Trash`.
- `due` = deadline; `when` = scheduled/start date. They are different.
- **Mutations act by id, not name** — deleting a project by name can silently
  no-op; deleting by id is reliable. Always resolve to an id first.
- `--tags "a,b"` **replaces** tags and creates tags that don't exist yet
  (existing tags matched case-insensitively, rendered in stored casing). Use
  `--add-tags` to append instead.
- `search` defaults to `--status open`. For `completed`/`canceled`/`any` with no
  `--list`/`--project`, the CLI also queries the **Logbook** (the global `to dos`
  collection excludes it), so logged items are found. Open searches stay fast;
  any/completed searches are slower (they scan the Logbook, ~1500+ items).
- `update` echoes back the full updated todo as JSON; mutations are by id.
- URL-scheme writes are **async** — the CLI waits ~0.7s before re-reading, but a
  busy app may lag. Re-query if you need certainty.
- **Checklist items are write-only**: neither AppleScript nor the URL scheme can
  read them back, so they don't appear in todo JSON.
- `move` to a project errors (301); the CLI uses `set project` under the hood,
  so `move <id> --to-project` works correctly.
- `delete` sends to Trash. Emptying Trash is destructive — the CLI has no such
  command; only do it via `raw 'tell application "Things3" to empty trash'`
  when the user explicitly asks.
- Avoid UI commands (`show`, `edit`, Quick Entry) unless the user wants visible
  UI.

## Auth token

Only the URL-scheme features need a token: `--clear-deadline`, `--add-tags`,
`--append-notes`, `--prepend-notes`, `--checklist`, and natural-language dates.
All reads and basic writes work without it.

**Retrieval is automatic** — the CLI fetches the token itself when a URL-scheme
flag is used, resolving `THINGS_AUTH_TOKEN` env var first, then the macOS
Keychain (service `things-cli-token`, account `$USER`). You never read the
Keychain manually; just run the command.

**If the token is missing**, the CLI exits non-zero with a message and changes
nothing. Don't retry — relay this to the user and have them set it up:

1. Enable **Things ▸ Settings ▸ General ▸ Enable Things URLs**.
2. Click **Manage** and copy the token.
3. Run: `things set-token "<TOKEN>"` (stores it in their Keychain).

Then re-run the original command. A one-time Keychain "allow access" prompt may
appear on first read — that's expected.

## Raw AppleScript fallback

For anything the CLI lacks, use `things raw '...'` or `osascript`. Build the
result as a string and `return` it — `log` prints raw expressions under
`osascript`, not values. Official reference:
https://culturedcode.com/things/support/articles/4562654/

```bash
osascript <<'APPLESCRIPT'
tell application "Things3"
  set out to ""
  repeat with t in to dos of list "Today"
    set out to out & "• " & name of t & linefeed
  end repeat
  return out
end tell
APPLESCRIPT
```

