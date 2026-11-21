---
name: delete-comment
description: Audit and remove source comments in any repository. Use for /delete-comment, comment cleanup, or a comment lint ratchet.
---

Audit the requested scope, or first-party source across the repository if no
scope is given. Prefer the repository's comment inventory. Otherwise use
language-aware tooling where available and verify any text-search candidates
against the source. Read surrounding code and group adjacent lines that explain
one point.

- Tautology. Delete text that repeats visible code.
- Stale. Delete claims that no longer describe the implementation.
- Excuse. Delete text that rationalizes a concrete flaw. If issue filing is
  authorized, reuse an existing issue or file one with the impact and acceptance
  criteria. Otherwise report the follow-up.
- Decision Record. Move non-obvious rationale and consequences to the repository's
  ADR location. Reuse an existing record where it fits.

Preserve tool directives, required notices, and vendored source. Preserve
behavior, including whitespace that separates tokens or affects parsing.
Follow the repository's lint conventions and remove obsolete baseline entries.
If asked to add a ratchet, reject new comments while allowing exact existing
occurrences by file and text, including duplicate counts.

Run the applicable checks. Report the classifications by source location, ADRs
and issue links, standalone lines removed, and inline comments removed.
