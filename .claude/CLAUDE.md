- In all interactions and commit messages, be extremely concise and sacrifice
grammar for the sake of concision.

## Notifications

After making a set of changes to files or satisfying a task, you MUST display a notification to tell me what's been done. Use a brief descriptive message. Here's an example:

```bash
echo '{"message":"Refactored FooBar class into smaller methods"}' | ~/.local/bin/claude_notifier
```

## Plans
- At the end of each plan, give me a list of unresolved questions to answer, if
any. Make the questions extremely concise. Sacrifice grammar for the sake of
concision.

## Git Commit Guidelines

Follow these rules for well-formed git commit messages.

Rules:

### The Seven Rules

- Limit the subject line to 50 characters
- Capitalize the subject line
- Do not end the subject line with a period
- Use the imperative mood in the subject line
- Wrap the body at 72 characters
- Use the body to explain what and why vs. how:
    Do not list or summarize the changes in the commit: give a brief overview
    of what was done and if if the change isn't an obvious one, also the motivation
    (the why).
- Do not mention AI assistance, Claude co-authorship, or similar attributions in commit messages

### Examples

**Good commit message:**

```
Add repository analysis caching

Implement SQLite-based caching for repository analysis results
to improve performance when scanning large numbers of projects.
This reduces scan time from hours to minutes for subsequent runs.

Fixes performance issues identified in issue #123.
```

**Bad commit message:**

```
fixed stuff

- Added feature X
- Fixed bug Y
```

