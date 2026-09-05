# Ingest

Process one source at a time unless the user explicitly requests a batch.

## Prepare

1. Read the vault index and relevant wiki/human pages.
2. Identify input form:
   - vault file: plan a move into `Sources/`;
   - external file: plan a copy into `Sources/`;
   - URL: capture a local Markdown snapshot with canonical URL and retrieval
     date;
   - pasted text: create a source only when explicitly requested;
   - human note: integrate by link without moving or rewriting it.
3. Detect exact duplicates by content hash and canonical URL. Make no changes or
   commit for an exact duplicate. Treat changed content as a new related version.
4. Choose one primary domain. Never duplicate cross-domain sources.
5. For imported Markdown/web pages, localize meaningful attachments under
   `Sources/assets/<source-slug>/`; omit decorative and tracking assets.

## Preview

Present:

- concise takeaways;
- proposed source path and primary domain;
- pages to create/update;
- provenance links;
- contradictions or superseded claims;
- exact planned changes.

Wait for approval before writing.

## Integrate

1. Normalize the source and attachments before their first commit. After that
   commit, freeze body and assets.
2. Create a dedicated wiki source-summary page only when the source has durable
   independent reuse, unique claims, or context needed across pages.
3. Prefer updating the nearest broader wiki page. Create a topic page only for
   a durable, independently reusable concept.
4. Link consequential, disputed, or time-sensitive claims inline. Put remaining
   provenance in a concise `## Sources` section.
5. Revise synthesis when stronger evidence clearly supersedes it. Otherwise
   preserve both positions under `## Conflicts` and ask the user.
6. Update `Wiki/index.md` and append one log entry:

   `## [YYYY-MM-DD] ingest | Title`

   Briefly list the source, changed pages, and decisions/conflicts.
7. Validate and commit atomically.
