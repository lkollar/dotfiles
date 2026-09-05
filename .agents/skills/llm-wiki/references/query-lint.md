# Query and Lint

## Query

1. Read `index.md`, `Wiki/index.md`, then relevant pages and sources.
2. Search broadly enough to catch cross-domain links and conflicting claims.
3. Answer with vault links as citations. Distinguish source-backed claims,
   human-note evidence, and inference.
4. Stay read-only and do not log ordinary queries.
5. When explicitly asked to file durable synthesis, preview the target page and
   provenance, then update/create it, update the index, append a `file` log
   entry, validate, and commit.

## Lint

Report:

- broken Markdown and Obsidian links;
- orphan wiki pages;
- missing or weak provenance;
- schema/frontmatter/path violations;
- duplicate or near-duplicate concepts;
- unresolved conflicts;
- likely stale time-sensitive claims;
- important repeated concepts lacking a page.

Stay local by default. Suggest web research targets without browsing. Never
change files unless the user asks to fix.

For fixes:

1. Preview exact changes.
2. Require separate confirmation for deletion, merge, or supersession.
3. Update indexes and append one `lint` log entry.
4. Validate and commit atomically.
