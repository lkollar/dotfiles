---
name: code-review
description: Use when the user asks for a code review, PR review, review of recent changes, or design-quality review of a diff or commit range. Focus on concrete bugs, regressions, design risks, security/perf issues, and missing tests in recent git changes.
---

# Code Review

Review recent code changes with findings first. Default to local git context unless the user gives a specific diff, commit, PR, or file set.

## Gather Context

Start with the smallest context that answers the request:

- `git status --short` for changed files
- `git diff --stat` for scope
- `git diff HEAD~1` for the latest commit when the user says "recent changes"
- `git log --oneline -5` for recent history
- `git branch --show-current` for branch context

If the user names a specific target, prefer that over default git heuristics.

Read the changed files directly before concluding. Use `rg`, `sed`, `git diff`, and targeted file reads to confirm each finding.

## Review Lens

Review against these principles:

- Minimize complexity: flag change amplification, high cognitive load, hidden assumptions.
- Optimize for readability: check naming, consistency, and obviousness.
- Favor deep modules: flag shallow wrappers and duplicated abstractions.
- Enforce information hiding: note leaked implementation details and duplicated knowledge.
- Pull complexity downward: avoid pushing flags and setup burden to callers.
- Keep error handling simple: flag fragile branching and inconsistent failure behavior.
- Design for evolution: call out tactical shortcuts that raise future cost.
- Check security and performance: focus on unsafe boundaries, leaks, and likely hot paths.
- Check tests and docs: look for missing coverage on normal, edge, and failure paths; reject comments that only restate code.

Prefer concrete, user-visible risk over style nitpicks. If something is only a taste issue, omit it.

## Output

Findings come first, ordered by severity. Use file references with lines when possible.

Structure the response like this:

1. Top risks
   - 3-7 bullets max
   - include severity `high|medium|low`, file:line, issue, and why it matters

2. Design assessment
   - short notes on abstraction depth, information hiding, and change amplification

3. Security/performance/testing/docs gaps
   - only concrete findings
   - if none, say `No significant issues found`

4. Actionable fixes
   - prioritized
   - smallest safe next step first

If there are no findings, say so explicitly, then note residual risk or testing gaps briefly.

## Standards

- Be specific. Name the exact branch of logic or API usage that is risky.
- Prefer verified observations from code over speculative guesses.
- Mention open questions only when they block confidence.
- Suggest alternatives when design is weak, not just criticism.
- Keep summaries brief; findings are the main deliverable.

## Example Triggers

- "review recent changes"
- "do a code review"
- "review this diff"
- "audit the last commit"
- "review this PR locally"
- "look for design issues in these changes"
