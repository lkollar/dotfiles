- In all interactions + commit messages: be extremely concise. Sacrifice grammar for concision.

## Plans

- End each plan with unresolved questions list (if any).
- Keep questions extremely concise. Sacrifice grammar for concision.

## Git Commit Rules

### Core format

- Separate subject/body with one blank line.
- Subject target <= 50 chars (72 absolute max).
- Capitalize subject first word.
- No trailing period in subject.
- Use imperative mood.
- Wrap body at 72 chars.
- Body explains what + why, not how.
- No AI attribution.

### Personal style defaults

- Prefer concise verb-led subjects.
- Prefer these verbs: Add, Fix, Remove, Update, Implement.
- Usually one-line commit if context obvious.
- Add body only when non-obvious tradeoff/context exists.
- Use prefixes only when repo convention expects them
  (`test:`, `feat:`, `fix:`, `gh-12345:`, `[ABC-123]`).

### Body quality guardrails

- Do not list patch/diff items in commit body.
- Do not enumerate files, functions, or mechanical edits.
- Trivial change: subject only.
- Simple non-obvious change: one short body paragraph (context + why).
- Complex or risky change: multiple short paragraphs.
- If why is unclear, tighten commit scope before committing.
