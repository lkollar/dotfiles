---
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git branch:*)
description: Perform a comprehensive code review of recent changes
---

## Context

- Current git status: !`git status`
- Recent changes: !`git diff HEAD~1`
- Recent commits: !`git log --oneline -5`
- Current branch: !`git branch --show-current`

## Your task

Review the recent changes using these general software design principles:

1. **Minimize complexity**
   - Flag change amplification (same change required in many places).
   - Flag high cognitive load (too much context needed to understand code).
   - Flag unknown unknowns (unclear behavior, hidden assumptions, surprising flow).

2. **Optimize for readability and obviousness**
   - Prefer code that is easy to read over clever code that is easy to write.
   - Check naming precision and consistency.
   - Call out violations of project conventions.

3. **Favor deep modules and clean abstractions**
   - Interfaces should stay simple while implementations absorb complexity.
   - Identify shallow wrappers, pass-through methods, and pass-through variables.
   - Check whether adjacent layers duplicate the same abstraction.

4. **Enforce information hiding**
   - Ensure implementation details do not leak across module boundaries.
   - Highlight duplicated knowledge across files/modules.
   - Suggest merging or extraction when it reduces interface surface.

5. **Pull complexity downward**
   - Prefer solving hard logic once in lower-level modules.
   - Avoid pushing complexity to every caller through extra flags/config.
   - Ensure defaults handle common cases without special setup.

6. **Keep error handling simple and intentional**
   - Reduce unnecessary exception paths and special cases.
   - Prefer masking/aggregating low-level errors when details are not needed upstream.
   - Ensure failures preserve system consistency.

7. **Design for evolution, not just immediate correctness**
   - Call out tactical shortcuts that increase long-term maintenance cost.
   - Suggest small strategic refactors when they simplify future change.
   - If design choices look weak, propose at least one alternative design direction.

8. **Performance and security by design**
   - Identify security risks from weak boundaries, unsafe defaults, or data leaks.
   - Identify likely hot-path costs and unnecessary special-case branching.
   - Recommend measurement-driven optimization (measure first, then tune).

9. **Tests and documentation as design tools**
   - Verify tests cover normal path, boundary cases, and failure paths.
   - Check that comments explain non-obvious intent, constraints, and cross-module decisions.
   - Reject comments that restate code.

## Output format

Return concise review feedback in this structure:

1. **Top risks (highest impact first)**
   - 3-7 bullets with severity (`high|medium|low`), file:line, issue, and why it matters.

2. **Design assessment**
   - Short notes on abstraction depth, information hiding, and change amplification.

3. **Security/performance/testing/docs gaps**
   - Only concrete findings. If none, explicitly say "No significant issues found" for that category.

4. **Actionable fixes**
   - Specific recommendations, prioritized, with smallest safe next step first.

Be specific. Prefer concrete examples over generic advice.
