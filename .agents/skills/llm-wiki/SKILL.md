---
name: llm-wiki
description: Set up, migrate, ingest, query, lint, and maintain a layered Markdown or Obsidian knowledge vault with immutable sources, generated wiki synthesis, local AGENTS.md schema, provenance, link validation, and scoped automatic Git commits. Use when the user invokes $llm-wiki or asks to adopt, operate, or health-check an LLM-maintained wiki.
---

# LLM Wiki

Maintain a persistent wiki between preserved evidence and human-authored notes.
Treat the vault's `AGENTS.md` as the local schema; this skill supplies the
reusable workflow.

## Resolve the operation

- `setup`: initialize a vault and its local schema.
- `migrate`: move an existing vault into layers.
- `ingest`: integrate one source or human note.
- `query`: answer from the vault; read-only unless filing is requested.
- `lint`: report vault health; edit only when fixing is requested.

Infer the operation from the request. If genuinely ambiguous, ask one concise
question. Read only the operation reference required:

- Setup or migration: [setup-migrate.md](references/setup-migrate.md)
- Ingest: [ingest.md](references/ingest.md)
- Query or lint: [query-lint.md](references/query-lint.md)
- Any mutation: [git-validation.md](references/git-validation.md)

## Find the vault

For established vaults, use the nearest ancestor `AGENTS.md` containing an
`## LLM Wiki` section. For setup, propose the current directory as root and
confirm before writing. Read the root `index.md` first when present, then search
before creating pages.

On Lukas Kollar's computer, the established personal notes vault is
`/Users/lkollar/Documents/Notes`.

## Enforce invariants

- Let local `AGENTS.md` define paths, domains, metadata, and exceptions.
- If absent during setup, default to `Sources/`, `Wiki/`, human domain folders,
  root `index.md`, `Hubs/`, and `Templates/`.
- Derive editing ownership from paths; never add redundant `owner` metadata.
- Never rewrite human-authored prose without explicit instruction.
- Never edit a committed source body or asset. Re-ingest corrections as a new
  version and mark the old source superseded in the wiki.
- Keep one canonical source copy. Link across domains instead of duplicating.
- Require preview and confirmation for migration, deletion, merge, or
  supersession.
- Do not browse during lint unless requested. Before adding web-derived claims,
  save and ingest the supporting page as a source.
- Preserve unrelated files and worktree changes.
- Never push automatically.

## Communicate

Lead with the outcome. For ingest, show takeaways and planned integration before
writing. For previews, list exact moves, edits, conflicts, and commit scope.
Keep generated prose concise and distinguish verified facts from inference.
