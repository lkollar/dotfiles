---
name: pr-review
description: Review a pull request from a PR URL. Use when the user gives a GitHub pull request URL and wants a local PR review. Reuse an existing local repo from ~/src or ~/github when possible, otherwise create a minimal temp clone, fetch the PR refs, and invoke the code-review skill on the fetched changes.
---

# PR Review

Turn a GitHub PR URL into a local review workspace, then use `$code-review` on the PR diff.

## Workflow

1. Run `scripts/prepare_pr_review.sh "<pr-url>"`.
2. Read the script output. It prints:
   - `review_path`: directory to review in
   - `source_repo`: reused local clone or temp clone path
   - `checkout_ref`: ref checked out in the review workspace
   - `diff_cmd`: exact diff command for the PR changes
   - `review_hint`: which local git target to pass into review
3. `cd` into `review_path`.
4. Inspect the diff with the printed `diff_cmd`, plus any targeted file reads needed to confirm findings.
5. Invoke `$code-review` against that prepared checkout. Prefer the printed `review_hint`:
   - If it says `git diff HEAD^1 HEAD`, review the merge result diff.
   - If it says `git diff origin/<default>...HEAD`, review the head branch diff vs base.

## Repo Selection

Prefer an existing clone over a fresh clone:

- First check the current repo if already inside the matching project.
- Then check common paths under `~/src` and `~/github`.
- Match by normalized remote URL, not only folder name.
- If a matching clone exists, fetch into it and create a temp `git worktree` for review. Do not disturb the user's main checkout.
- If no clone exists, create a minimal temp clone in `/tmp` with blob filtering.

## Review Rules

- Do not review the PR from the GitHub page alone when a local diff can be prepared.
- Prefer the GitHub merge ref when available because it captures merge-time breakage.
- Fall back to the PR head ref against the default branch when the merge ref is unavailable.
- Keep findings first. Reuse the `code-review` skill's output shape and review lens.
- Mention prep failures precisely: bad URL, repo not reachable, fetch failure, missing refs.

## Commands

Typical flow:

```bash
/Users/lkollar/.codex/skills/pr-review/scripts/prepare_pr_review.sh \
  "https://github.com/OWNER/REPO/pull/123"
cd /tmp/pr-review-REPO-123/worktree
git diff HEAD^1 HEAD
```

If network or fetch is sandbox-blocked, rerun the fetch/clone command with escalation instead of stopping.

## Example Triggers

- "review this PR https://github.com/acme/api/pull/481"
- "do a PR review from this url"
- "pull this PR locally and review it"
