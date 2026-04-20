# Linking Guidelines

Use these conventions when turning review text into HTML.

## Repository URL normalization

Convert common git remotes to browser URLs.

Examples:
- `git@github.com:owner/repo.git` -> `https://github.com/owner/repo`
- `https://github.com/owner/repo.git` -> `https://github.com/owner/repo`
- `https://github.com/owner/repo` -> unchanged

If the remote is not a known browsable host, keep file locations as plain text.

## Commit selection

Prefer this order:
1. Explicit commit/hash from the user
2. Reviewed head commit from the review context
3. Current `HEAD`

Use commit-based links instead of branch-based links when possible.

## Line linking

For concrete references:
- single line: `#L123`
- line range: `#L123-L126`

Keep ranges short and targeted.

## Identifier linking

Link only identifiers that directly help explain the finding.
Good candidates:
- the variable or function named in the finding title
- the branch condition that causes the bug
- the cleanup call or state mutation that creates the regression

Avoid turning every code token into a link. The page should remain readable.

## Snippet design

A useful snippet block contains:
- short explanation in the header
- a GitHub link to the exact location
- 3-10 lines of code
- optional highlighted token with `<mark>`

Typical snippet roles:
- setup: where state is introduced
- decision point: where logic branches
- impact: where the wrong mutation or output happens

## Trust boundary

Never fabricate links or line numbers. If you cannot resolve a location confidently, leave it as plain text.
