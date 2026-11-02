# Dotfiles (yadm)

`$HOME` is a yadm repo (`yadm`, not `git`). Remote: github.com/lkollar/dotfiles.
Tracked files are config for tools: zsh, nvim, claude, codex, herdr, ghostty, etc.

## Commits

Subject: `<tool>: <Change>`

- `<tool>` = app/config the change touches, lowercase: `zsh`, `nvim`,
  `claude`, `codex`, `herdr`, `ghostty`, `agents`, `yadm`, ... Reuse an existing
  prefix: `yadm log --format=%s | grep -o '^[a-z-]*:' | sort -u`.
- Change touches several tools: no prefix, plain imperative subject. Exception:
  if the other tools' edits only support one tool (e.g. ghostty unbinds for
  herdr keys), use that tool's prefix.
- Whole subject <= 50 chars, prefix included. Imperative mood, capital after
  the colon, no trailing period.
- Body (optional): wrap at 72, explain why, not what. Don't list changes.
- No AI attribution: no `Co-Authored-By`, no `Claude-Session`, no "Generated
  with".
- One logical change per commit.

Good: `herdr: Make CMD-b toggle panel`, `claude: Set Sonnet 5 as default model`.
Bad: `Update Herdr pane shortcuts`, `fixed stuff`.

## Workflow

- Commit only when asked. Never push unless asked.
- Working tree often has unrelated edits (apps rewrite their own config). Stage
  only files you changed; check `yadm diff --cached` first.
- Don't rewrite pushed commits. Check `yadm status -sb` for "ahead N".

## Herdr

Track only user-owned files in `.config/herdr-app/`: `keys.json`,
`settings.json`, own layouts, own mods. Never shipped or generated files
(`AGENTS.md`, `*.d.ts`, `frame/`, `icons/`, `data/`, `view.json`, `shared.json`,
`layouts/.state/`, ...). See `.config/herdr-app/AGENTS.md`.
