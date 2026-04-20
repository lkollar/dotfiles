---
name: review
description: Perform a comprehensive code review of recent changes using git history and design-focused review criteria. Use when asked to review a branch, recent commit, staged changes, or a working tree diff.
---

# Code Review

Perform focused code reviews of recent changes with emphasis on design quality,
maintainability, correctness, security, performance, testing, and documentation.

## When to Use

Use this skill for requests like:

- "review my changes"
- "do a code review"
- "review this branch / PR / commit"
- "check recent changes for issues"

## Required Context

Work inside a git repository. If the repo state or review target is unclear,
first determine:

- current branch
- working tree status
- review scope: staged changes, unstaged changes, last commit, branch diff, or a specific range

If there is no git repository, tell the user and ask what files or diff should be reviewed.

## Recommended Inspection Commands

Use the smallest set needed for the requested scope:

```bash
git status
git branch --show-current
git log --oneline -5
git diff
git diff --staged
git diff HEAD~1
git diff main...HEAD
```

For file-specific investigation, inspect the changed files directly.

## Review Principles

Review using these principles:

1. **Minimize complexity**
   - Flag change amplification.
   - Flag high cognitive load.
   - Flag hidden assumptions or surprising control flow.

2. **Optimize for readability and obviousness**
   - Prefer clear code over clever code.
   - Check naming precision and consistency.
   - Call out convention violations.

3. **Favor deep modules and clean abstractions**
   - Keep interfaces simple.
   - Identify shallow wrappers and pass-through layers.
   - Flag duplicated abstractions across adjacent layers.

4. **Enforce information hiding**
   - Prevent implementation details leaking across boundaries.
   - Highlight duplicated knowledge across files/modules.

5. **Pull complexity downward**
   - Prefer solving difficult logic once in lower-level modules.
   - Avoid pushing complexity to every caller.

6. **Keep error handling simple and intentional**
   - Reduce unnecessary special cases.
   - Ensure failures preserve consistency.

7. **Design for evolution**
   - Call out tactical shortcuts with maintenance cost.
   - Suggest small strategic refactors when helpful.

8. **Performance and security by design**
   - Identify unsafe defaults, weak boundaries, data leaks, and likely hot-path issues.
   - Recommend measurement before optimization when appropriate.

9. **Tests and documentation as design tools**
   - Check normal path, boundary cases, and failure-path coverage.
   - Prefer comments that explain intent, constraints, and tradeoffs.

## Output Format

Return concise feedback in this structure:

1. **Top risks (highest impact first)**
   - 3-7 bullets max
   - Include severity: `high|medium|low`
   - Include `file:line` when possible
   - State the issue and why it matters

2. **Design assessment**
   - Short notes on abstraction depth, information hiding, and change amplification

3. **Security / performance / testing / docs gaps**
   - Only concrete findings
   - If none, explicitly say: `No significant issues found`

4. **Actionable fixes**
   - Prioritized recommendations
   - Start with the smallest safe next step

## Review Style

- Be specific and evidence-based.
- Prefer concrete examples over generic advice.
- Focus on the highest-value issues.
- Avoid nitpicks unless they indicate a broader design problem.
- If something looks good, say so briefly.
