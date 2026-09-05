# Git and Validation

Use Git as a safety boundary for every mutation.

## Preflight

1. Inspect repository root, branch, status, ignores, and relevant diffs.
2. Record pre-existing changes. Never stage or modify unrelated work.
3. If a planned path overlaps unrelated changes, stop and ask.
4. If Git is absent, only `setup` may initialize it.

## Validate

Before committing:

- parse frontmatter on changed Markdown files;
- check changed links and then vault-wide internal links;
- ensure index entries resolve;
- ensure log headings match `## [YYYY-MM-DD] operation | Title`;
- inspect the final diff;
- confirm committed source bodies/assets were not modified;
- run any local vault checks defined by `AGENTS.md`.

Do not claim Obsidian-rendered validation without opening Obsidian.

## Commit

1. Stage exact operation-owned paths, never `git add .` or `git add -A` in a
   dirty worktree.
2. Inspect the staged diff and staged file list.
3. Commit one atomic operation using the repository's message convention.
4. Confirm status and commit contents.
5. Never push automatically.

If validation or commit fails, leave work uncommitted, explain the state, and
continue fixing when safe. Never discard user changes to recover.
