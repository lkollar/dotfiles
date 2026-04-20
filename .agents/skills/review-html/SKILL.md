---
name: review-html
description: Convert an existing code review into a polished HTML artifact with linked source locations and optional evidence snippets. Use after findings have already been produced by another skill, extension, or manual review.
---

# Review HTML

This skill turns an existing review into a shareable HTML file.

Use this skill **after** the review findings already exist. It is not a review-generation skill.

## When to use

Use this skill when:
- a previous assistant message already contains review findings
- a review exists in a markdown or text file
- a pi extension, another skill, or an external tool generated the review
- the user wants a PR/branch/commit review rendered as polished HTML

## Inputs this skill supports

Preferred sources, in order:
1. A user-provided file containing the review text
2. The most recent assistant message containing the review
3. User-pasted findings in the current prompt

Optional metadata to infer or ask for only if needed:
- PR number
- PR title
- base branch or merge base
- head commit
- desired output filename
- whether to include evidence snippets

## Core behavior

Preserve the review's meaning and verdict. Do **not** silently rewrite findings unless the user explicitly asks for editorial cleanup.

Your job is to:
1. Identify the review source text
2. Detect repository metadata from git when available
3. Convert file locations into GitHub links when possible
4. Link important identifiers in prose when that improves usability
5. Add compact evidence snippets when they strengthen the finding
6. Write a polished HTML file with a predictable name

## File naming

Use these defaults:
- If PR number is known: `pr-<number>-review.html`
- Else if branch is known: `review-<branch>.html`
- Else: `review-<YYYY-MM-DD>.html`

Prefer writing to the current working directory unless the user requests another location.

## Required workflow

### 1) Determine the review source

If the user provided a file path, read that file.
Otherwise, use the latest assistant message that contains the review.
If the review text is ambiguous or unavailable, ask the user for the source.

### 2) Gather repository metadata

When inside a git repository, use bash to gather:

```bash
git remote get-url origin
git rev-parse --short HEAD
git rev-parse HEAD
git branch --show-current
```

If the review references a base commit or merge base, use that if available from the user's prompt or review text.

Normalize Git remotes to browser URLs when possible.
Examples:
- `git@github.com:owner/repo.git` -> `https://github.com/owner/repo`
- `https://github.com/owner/repo.git` -> `https://github.com/owner/repo`

### 3) Parse the review structure

Extract when possible:
- title / review subject
- verdict
- findings
- priority tags like `[P1]`
- file locations
- human reviewer callouts

If the review is only loosely structured, preserve the text and render it cleanly rather than forcing a brittle parser.

### 4) Add source links

For each finding, create links for any concrete file locations.
Use commit-based links when possible:
- `https://github.com/<owner>/<repo>/blob/<commit>/<path>#Lx-Ly`

Prefer linking to the reviewed head commit unless the user requests another revision.

When prose contains code identifiers that are central to the finding, it is acceptable to convert them into links pointing at the most relevant source location.
Examples:
- variables such as `soname_map`
- function calls such as `clear_rpath(path)`
- decision points such as `if replacements:`

Do not over-link every identifier. Only link identifiers that materially help the reader follow the finding.

### 5) Add evidence snippets when useful

For each finding, include 1-3 compact snippets when they strengthen the argument.
A good pattern is:
- setup
- decision point
- impact/result

Rules for snippets:
- Keep them short
- Use exact code taken from the current checked-out files
- Highlight the most relevant token or line when useful
- Include a small `GitHub ↗` link in each snippet header
- Do not fabricate line numbers or code

If a finding does not benefit from snippets, omit them.

### 6) Render polished HTML

Use the template in `templates/review.html` as a starting point when helpful.
The output should include:
- title/header
- metadata chips or summary rows
- overall verdict
- findings cards
- optional snippet cards beneath findings
- human reviewer callouts section

The output must remain readable as a standalone file with no build step.

## HTML conventions

- Use semantic HTML where practical
- Keep CSS self-contained in the file unless the user wants split assets
- Prefer dark theme with clear contrast, but keep it simple
- Preserve code formatting with `<code>` / `<pre>`
- If using highlighting, keep it lightweight with `<mark>`

## Editing behavior

If the target HTML file already exists:
- update it in place if the user is iterating on the same review
- preserve existing useful styling unless the user asks for a redesign

If no file exists yet:
- create a new one

## Evidence standard

Never invent:
- code snippets
- filenames
- line numbers
- PR metadata
- verdicts

If metadata is missing, either omit it or label it clearly as unavailable.

## Output expectations

When done, respond briefly with:
- the path written
- what was included (e.g. links, snippets, identifier links)

## References

See:
- `templates/review.html`
- `references/linking.md`
