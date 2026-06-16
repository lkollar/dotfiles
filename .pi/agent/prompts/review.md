---
description: Perform a comprehensive code review of recent changes using git history and design-focused review criteria
argument-hint: "[staged|unstaged|branch <name>|commit|range]"
---

Perform a focused code review of recent changes with emphasis on design quality,
maintainability, correctness, security, performance, testing, and documentation.

## Scope

$@

If no scope is given, review `git diff` (unstaged changes). Determine:

- current branch
- working tree status
- review scope: staged changes, unstaged changes, last commit, branch diff, or a specific range

If there is no git repository, ask what files or diff should be reviewed.

## Inspection Commands

```bash
git status
git branch --show-current
git log --oneline -5
git diff
git diff --staged
git diff HEAD~1
git diff main...HEAD
```

Use the smallest set needed. Inspect changed files directly for detail.

## Review Principles

1. **Minimize complexity** — Flag change amplification, high cognitive load, hidden assumptions, surprising control flow.
2. **Optimize for readability and obviousness** — Prefer clear over clever. Check naming precision and consistency. Call out convention violations.
3. **Favor deep modules and clean abstractions** — Keep interfaces simple. Flag shallow wrappers, pass-through layers, duplicated abstractions.
4. **Enforce information hiding** — Flag implementation details leaking across boundaries. Highlight duplicated knowledge across files/modules.
5. **Pull complexity downward** — Solve difficult logic once in lower-level modules. Avoid pushing complexity to every caller.
6. **Keep error handling simple and intentional** — Reduce unnecessary special cases. Ensure failures preserve consistency.
7. **Design for evolution** — Call out tactical shortcuts with maintenance cost. Suggest small strategic refactors when helpful.
8. **Performance and security by design** — Identify unsafe defaults, weak boundaries, data leaks, and likely hot-path issues. Recommend measurement before optimization.
9. **Tests and documentation as design tools** — Check normal path, boundary cases, and failure-path coverage. Prefer comments that explain intent, constraints, and tradeoffs.

## Output Format

1. **Change summary** — 2-5 bullets on what changed, main user-visible/developer-visible behavior changes, key files/subsystems touched.

2. **Top risks (highest impact first)** — 3-7 bullets max. Include severity (`high|medium|low`), `file:line` when possible, and why it matters.

3. **Design assessment** — Short notes on abstraction depth, information hiding, and change amplification.

4. **Security / performance / testing / docs gaps** — Only concrete findings. If none, say: `No significant issues found`.

5. **Actionable fixes** — Prioritized recommendations. Start with the smallest safe next step.

## Style

- Start by explaining what changed before judging it.
- Be specific and evidence-based.
- Prefer concrete examples over generic advice.
- Focus on the highest-value issues.
- Avoid nitpicks unless they indicate a broader design problem.
- If something looks good, say so briefly.
- If the intent of a change is unclear, say that explicitly rather than guessing.
