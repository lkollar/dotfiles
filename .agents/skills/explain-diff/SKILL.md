---
name: explain-diff-html
description: Use when the user asks for a rich explanation of a code change, diff, branch, or PR. Produces validated offline HTML from structured Markdown.
---

# Explain Diff

Create a rich, interactive explanation of the specified code change.

## Workflow

1. Explore the repo broadly enough to understand the surrounding system, not just
   the edited lines.
2. Write a structured Markdown draft outside the repo:
   `/tmp/YYYY-MM-DD-explanation-<slug>.md`.
3. Use the dialect in `references/markdown-dialect.md`.
4. Render and validate with:

   ```bash
   /Users/lkollar/.agents/skills/explain-diff/scripts/render-explain-diff /tmp/YYYY-MM-DD-explanation-<slug>.md -o /tmp/YYYY-MM-DD-explanation-<slug>.html
   ```

5. Report the final HTML path only after the renderer passes validation.

The renderer creates one self-contained long-page HTML file with inline CSS,
inline JavaScript, a generated table of contents, build-time code highlighting,
inline SVG diagrams, and interactive quiz behavior. Do not hand-author polished
HTML directly unless the renderer itself needs maintenance.

## Required Explanation Structure

Use these top-level sections:

- `Background`: Explain the existing system relevant to this change. Include
  beginner-friendly background when needed, then narrow to the exact subsystem.
- `Intuition`: Explain the core idea behind the change. Use concrete toy data,
  figures, and diagrams to make the essence clear.
- `Code`: Walk through the code changes at a high level. Group changes by
  concept or data flow, not by raw file order.
- `Quiz`: Include five medium-difficulty multiple-choice questions. They should
  test real understanding, not trivia or gotchas.

Keep the output one long page with section headers and a table of contents. Do
not use tabs for the top-level structure.

## Writing Style

- Write clearly, with the clarity and flow of Martin Kleppmann: beginner-friendly
  where needed, technically precise, and connected by smooth transitions.
- Use callouts for key concepts, definitions, and important edge cases.
- Use diagrams liberally, but prefer a small reusable set of diagram families:
  system/data-flow, sequence, before/after, simplified UI mockup, data-shape,
  and state-transition diagrams.
- Prefer Mermaid fenced blocks. The renderer converts Mermaid to inline SVG at
  build time, so the final file has no Mermaid runtime dependency.
- Do not use ASCII diagrams.
- For UI mockups or diagrams Mermaid cannot express well, use simple semantic
  HTML/CSS diagram blocks documented in the dialect reference.

## Code Blocks

Use fenced code blocks with metadata for real code. Prefer filename/path,
language, line numbers, highlighted lines, and separate code notes.

Do not add explanatory comments to copied source unless the block is explicitly
marked as toy/example code. The copied code must stay faithful to the source.

The renderer emits `<pre>`-based code cards with preserved whitespace,
line numbers, highlighted lines, optional filename/path, language labels, copy
buttons, and annotations below the code.

## Validation

Validation is part of the tool. The renderer must fail loudly if:

- the HTML path is not `/tmp/YYYY-MM-DD-explanation-<slug>.html`,
- the final HTML is missing,
- any `http://` or `https://` reference remains,
- CSS or JavaScript is external,
- Mermaid was not rendered to inline SVG,
- code whitespace is not preserved,
- any quiz question does not have exactly one correct answer,
- required sections are missing.

Use this for validation-only checks:

```bash
/Users/lkollar/.agents/skills/explain-diff/scripts/render-explain-diff validate /tmp/YYYY-MM-DD-explanation-<slug>.html --source /tmp/YYYY-MM-DD-explanation-<slug>.md
```
