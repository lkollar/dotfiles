# Setup and Migration

## Setup

1. Confirm the proposed vault root.
2. Inspect existing `AGENTS.md`, `index.md`, frontmatter, links, folders, Git
   state, and ignored files.
3. If Git is absent, initialize it. For a populated vault, create one local
   baseline commit containing the vault, excluding ignored/cache/system files.
4. Add or update one bounded `## LLM Wiki` section in `AGENTS.md`; preserve all
   unrelated instructions.
5. Create `Sources/`, `Wiki/`, `Wiki/index.md`, and `Wiki/log.md` only as needed.
   Use the templates in `assets/`, adapting domains and local conventions.
6. Update root navigation and validate.
7. Commit setup atomically. Do not push.

Do not silently impose default domains. Infer stable domains from the existing
vault and record them in `AGENTS.md`.

## Migration preview

Migration is always two-phase. First inspect and report; write only after user
approval.

Classify by content and provenance, treating metadata only as a hint:

- External/imported evidence -> mirrored `Sources/<domain>/`.
- LLM-generated synthesis -> mirrored `Wiki/<domain>/`.
- Human notes -> existing domain folders, unchanged.
- Root index, hubs, templates, schema, ADRs -> local support paths.

Preview:

- exact source and destination paths;
- frontmatter changes, including removal of `owner`;
- links and indexes requiring updates;
- ambiguous classifications;
- expected Git commit scope.

## Apply migration

1. Recheck worktree state against the preview.
2. Move only approved files.
3. Remove `owner` throughout the approved vault scope; retain `type` and concise
   topic tags. Never add `status` unless local schema explicitly requires it.
4. Update all Markdown and Obsidian links affected by moves.
5. Create/update wiki index and append one migration log entry.
6. Validate and commit atomically.

Do not delete empty legacy folders unless requested. Preview any page deletion,
merge, or supersession separately.
