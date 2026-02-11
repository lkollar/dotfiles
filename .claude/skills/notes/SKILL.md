---
name: notes
description: Manage markdown notes in an Obsidian vault. Supports searching, reading, editing, and adding notes directly in files/folders. Designed for vaults synced across machines via Syncthing.
---

# Obsidian Notes Management

Use this skill to work with Obsidian notes as plain markdown files.

## Vault Location (Cross-machine)

Resolve vault path in this order:

1. `OBSIDIAN_VAULT_PATH` env var
2. Current working directory
3. Nearest parent dir containing `.obsidian`
4. Fallback `~/Documents/Notes`

If unresolved, ask user for vault path.

## Core Capabilities

- Search notes by keyword/regex
- Read existing notes
- Create new notes in chosen folders
- Edit/append existing notes
- Organize notes into folders

## How To Operate

Use native tools for markdown files:

- Find note files by name/pattern
- Search note content for terms
- Read target notes
- Edit existing note files
- Write new note files when needed

Prefer `.md` files only unless user asks otherwise.

## Note Conventions

- Use markdown headings and short sections
- Use `[[WikiLinks]]` for internal references
- Use frontmatter only when useful
- Keep titles descriptive and stable

## Safe Editing Rules

- Search before create to avoid duplicates
- Preserve user formatting style in touched notes
- Do not move/delete notes unless asked
- When path unclear, ask one concise question
