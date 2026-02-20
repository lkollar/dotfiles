---
allowed-tools: Bash(git diff:*), Bash(git log:*)
description: Perform a comprehensive code review of recent changes
---

## Context

- Current git status: !`git status`
- Recent changes: !`git diff HEAD~1`
- Recent commits: !`git log --oneline -5`
- Current branch: !`git branch --show-current`

## Your task

Perform a comprehensive code review focusing on:

1. **Code Quality**: Check for readability, maintainability, and adherence to best practices
2. **Security**: Look for potential vulnerabilities or security issues
3. **Performance**: Identify potential performance bottlenecks
4. **Testing**: Assess test coverage and quality
5. **Documentation**: Check if code is properly documented

### Software Design Principles

Also evaluate the changes against these design principles (from Ousterhout's *A Philosophy of Software Design*). Flag violations where they apply:

1. **Deep modules**: Modules should have simple interfaces relative to the functionality they provide. Flag shallow classes/functions that add interface complexity without meaningful logic (classitis, thin wrappers).
2. **Information hiding**: Implementation details should stay internal. Flag leakage where multiple modules share knowledge of the same design decision or data format.
3. **No pass-throughs**: Flag pass-through methods (signature mirrors the callee), pass-through variables threaded through many layers, and decorators that don't justify their existence.
4. **Pull complexity down**: Modules should absorb complexity for their callers, not push it outward via excessive config parameters or exceptions. Flag APIs that force callers to handle problems the module could resolve internally.
5. **Define errors out of existence**: Flag unnecessary exceptions and error conditions. Prefer APIs where error cases simply can't arise. Flag over-defensive code handling impossible scenarios.
6. **Together or apart**: Related code belongs together; flag splits that increase interface count without reducing complexity. Conversely, flag unrelated concerns jammed into one module. Flag code duplication that should be unified.
7. **Different layer, different abstraction**: Adjacent layers should operate at different abstraction levels. Flag cases where a layer merely relays data/calls without transforming the abstraction.
8. **Consistency**: Similar things should be done similarly. Flag convention violations, inconsistent naming, and divergent patterns for equivalent operations.
9. **Obviousness**: Code should be readable without deep study. Flag non-obvious code that lacks comments explaining *what* and *why* (not *how*). Flag generic names (data, result, info, tmp) that don't convey precise meaning.
10. **Strategic over tactical**: Flag quick hacks that increase complexity. Each change should leave the design at least as clean as before.

Provide specific, actionable feedback with line-by-line comments where appropriate.