---
description: Convert an existing code review into a polished, shareable HTML artifact with linked source locations and evidence snippets
argument-hint: "[review-file]"
---

Turn an existing review into a shareable HTML file. This is for rendering, not generating reviews — use after findings already exist.

## Input Sources

Preferred order:
1. A user-provided file containing the review text ($@)
2. The most recent assistant message containing the review
3. User-pasted findings in the current prompt

## Workflow

### 1. Determine the review source
If file path given, read it. Otherwise use the latest assistant message with review content. If ambiguous, ask.

### 2. Gather repository metadata
```bash
git remote get-url origin
git rev-parse --short HEAD
git rev-parse HEAD
git branch --show-current
```
Normalize git remotes to browser URLs (e.g., `git@github.com:owner/repo.git` → `https://github.com/owner/repo`). Use commit-based links over branch-based links.

### 3. Parse the review structure
Extract: title/subject, verdict, findings, priority tags like `[P1]`, file locations, reviewer callouts. If loosely structured, preserve text and render cleanly.

### 4. Add source links
For each finding, create links for concrete file locations using commit-based URLs:
`https://github.com/<owner>/<repo>/blob/<commit>/<path>#Lx-Ly`

Link key identifiers (function names, variables) that are central to findings. Don't over-link.

### 5. Add evidence snippets
Include 1-3 compact snippets per finding when they strengthen the argument. Use exact code from current files. Keep short, highlight the most relevant line. Include a GitHub link in each snippet header.

Never fabricate code, filenames, line numbers, PR metadata, or verdicts.

### 6. Render HTML
Produce a standalone, self-contained HTML file with embedded CSS. Use a dark theme with good contrast. Structure:
- Title header with verdict
- Metadata chips (branch, commit, date)
- Findings cards with priority badges, file locations, and optional snippet cards
- Human reviewer callouts section

Use semantic HTML, `<code>`/`<pre>` for code, `<mark>` for highlights.

## File Naming

- PR number known: `pr-<number>-review.html`
- Branch known: `review-<branch>.html`
- Otherwise: `review-<YYYY-MM-DD>.html`

Write to current working directory unless otherwise requested. If the file exists, update it in place.

## Output

When done, respond briefly with the path written and what was included (links, snippets, identifier links).
