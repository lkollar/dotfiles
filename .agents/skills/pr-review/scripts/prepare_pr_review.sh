#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  prepare_pr_review.sh [--parse-only] <github-pr-url>

Resolve a GitHub PR URL to a local review checkout.
Reuses a matching local clone from ~/src or ~/github when possible.
Otherwise creates a minimal temp clone in /tmp.

Output:
  repo_host=...
  repo_owner=...
  repo_name=...
  pr_number=...
  source_repo=...
  review_path=...
  checkout_ref=...
  diff_cmd=...
  review_hint=...
EOF
}

die() {
  echo "error=$*" >&2
  exit 1
}

normalize_remote() {
  local url="$1"
  url="${url%.git}"
  url="${url#git@}"
  url="${url#ssh://git@}"
  url="${url#https://}"
  url="${url#http://}"
  url="${url/:/\/}"
  printf '%s\n' "${url,,}"
}

parse_url() {
  local url="$1"
  if [[ "$url" =~ ^https?://([^/]+)/([^/]+)/([^/]+)/pull/([0-9]+)(/.*)?$ ]]; then
    REPO_HOST="${BASH_REMATCH[1]}"
    REPO_OWNER="${BASH_REMATCH[2]}"
    REPO_NAME="${BASH_REMATCH[3]}"
    PR_NUMBER="${BASH_REMATCH[4]}"
    return 0
  fi
  return 1
}

repo_matches() {
  local repo_path="$1"
  local expect="$2"
  local remote

  remote="$(git -C "$repo_path" remote get-url origin 2>/dev/null || true)"
  if [[ -n "$remote" ]] && [[ "$(normalize_remote "$remote")" == "$expect" ]]; then
    return 0
  fi

  remote="$(git -C "$repo_path" remote get-url upstream 2>/dev/null || true)"
  if [[ -n "$remote" ]] && [[ "$(normalize_remote "$remote")" == "$expect" ]]; then
    return 0
  fi

  return 1
}

matching_remote() {
  local repo_path="$1"
  local expect="$2"
  local remote_name remote

  for remote_name in origin upstream; do
    remote="$(git -C "$repo_path" remote get-url "$remote_name" 2>/dev/null || true)"
    if [[ -n "$remote" ]] && [[ "$(normalize_remote "$remote")" == "$expect" ]]; then
      printf '%s\n' "$remote_name"
      return 0
    fi
  done

  return 1
}

candidate_repos() {
  local owner="$1"
  local repo="$2"
  local roots=("$PWD" "$HOME/src" "$HOME/github")
  local root

  for root in "${roots[@]}"; do
    [[ -d "$root" ]] || continue
    printf '%s\n' "$root/$owner/$repo"
    printf '%s\n' "$root/$repo"
  done
}

find_existing_repo() {
  local owner="$1"
  local repo="$2"
  local expect="$3"
  local candidate

  while IFS= read -r candidate; do
    [[ -d "$candidate/.git" ]] || continue
    if repo_matches "$candidate" "$expect"; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done < <(candidate_repos "$owner" "$repo")

  local roots=("$HOME/src" "$HOME/github")
  local root found
  for root in "${roots[@]}"; do
    [[ -d "$root" ]] || continue
    while IFS= read -r found; do
      if repo_matches "$found" "$expect"; then
        printf '%s\n' "$found"
        return 0
      fi
    done < <(find "$root" -maxdepth 3 -type d -name .git -prune 2>/dev/null | sed 's#/.git$##')
  done

  return 1
}

ensure_clone() {
  local remote_url="$1"
  local repo_name="$2"
  local pr_number="$3"
  local clone_root="/tmp/pr-review-${repo_name}-${pr_number}/repo"

  if [[ ! -d "$clone_root/.git" ]]; then
    rm -rf "$clone_root"
    mkdir -p "$(dirname "$clone_root")"
    git clone --filter=blob:none "$remote_url" "$clone_root" >&2
  fi

  printf '%s\n' "$clone_root"
}

default_branch() {
  local repo_path="$1"
  local remote_name="${2:-origin}"
  local ref remote_head

  ref="$(git -C "$repo_path" symbolic-ref "refs/remotes/${remote_name}/HEAD" 2>/dev/null || true)"
  if [[ -n "$ref" ]]; then
    printf '%s\n' "${ref#refs/remotes/${remote_name}/}"
    return 0
  fi

  if git -C "$repo_path" rev-parse --verify "refs/remotes/${remote_name}/main" >/dev/null 2>&1; then
    printf 'main\n'
    return 0
  fi

  if git -C "$repo_path" rev-parse --verify "refs/remotes/${remote_name}/master" >/dev/null 2>&1; then
    printf 'master\n'
    return 0
  fi

  remote_head="$(git -C "$repo_path" ls-remote --symref "$remote_name" HEAD 2>/dev/null | sed -n 's#^ref: refs/heads/\([^[:space:]]*\)[[:space:]]*HEAD$#\1#p' | head -n1)"
  if [[ -n "$remote_head" ]]; then
    printf '%s\n' "$remote_head"
    return 0
  fi

  printf 'main\n'
}

prepare_review_checkout() {
  local repo_path="$1"
  local repo_name="$2"
  local pr_number="$3"
  local remote_name="$4"
  local worktree_root="/tmp/pr-review-${repo_name}-${pr_number}/worktree"
  local head_ref="refs/remotes/${remote_name}/pr/${pr_number}/head"
  local merge_ref="refs/remotes/${remote_name}/pr/${pr_number}/merge"
  local chosen_ref diff_cmd review_hint base_branch

  git -C "$repo_path" fetch "$remote_name" \
    "+refs/pull/${pr_number}/head:${head_ref}" \
    "+refs/pull/${pr_number}/merge:${merge_ref}" >&2 || true

  if git -C "$repo_path" rev-parse --verify "$merge_ref" >/dev/null 2>&1; then
    chosen_ref="$merge_ref"
    diff_cmd="git diff HEAD^1 HEAD"
    review_hint="git diff HEAD^1 HEAD"
  else
    git -C "$repo_path" fetch "$remote_name" \
      "+refs/pull/${pr_number}/head:${head_ref}" >&2
    chosen_ref="$head_ref"
    base_branch="$(default_branch "$repo_path" "$remote_name")"
    git -C "$repo_path" fetch "$remote_name" \
      "+refs/heads/${base_branch}:refs/remotes/${remote_name}/${base_branch}" >&2
    diff_cmd="git diff ${remote_name}/${base_branch}...HEAD"
    review_hint="git diff ${remote_name}/${base_branch}...HEAD"
  fi

  mkdir -p "$(dirname "$worktree_root")"
  if [[ -d "$worktree_root/.git" ]] || [[ -f "$worktree_root/.git" ]]; then
    git -C "$repo_path" worktree remove --force "$worktree_root" >&2 || true
  fi
  rm -rf "$worktree_root"
  git -C "$repo_path" worktree add --detach "$worktree_root" "$chosen_ref" >&2

  printf '%s\n' "$worktree_root"
  printf '%s\n' "$chosen_ref"
  printf '%s\n' "$diff_cmd"
  printf '%s\n' "$review_hint"
}

main() {
  local parse_only=0

  [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]] && { usage; exit 0; }
  if [[ "${1:-}" == "--parse-only" ]]; then
    parse_only=1
    shift
  fi
  [[ $# -eq 1 ]] || { usage >&2; exit 1; }

  local pr_url="$1"
  parse_url "$pr_url" || die "unsupported PR URL: $pr_url"

  if [[ "$parse_only" -eq 1 ]]; then
    printf 'repo_host=%s\n' "$REPO_HOST"
    printf 'repo_owner=%s\n' "$REPO_OWNER"
    printf 'repo_name=%s\n' "$REPO_NAME"
    printf 'pr_number=%s\n' "$PR_NUMBER"
    exit 0
  fi

  local remote_url="https://${REPO_HOST}/${REPO_OWNER}/${REPO_NAME}.git"
  local remote_key
  remote_key="$(normalize_remote "$remote_url")"

  local repo_path
  if ! repo_path="$(find_existing_repo "$REPO_OWNER" "$REPO_NAME" "$remote_key")"; then
    repo_path="$(ensure_clone "$remote_url" "$REPO_NAME" "$PR_NUMBER")"
  fi
  local remote_name
  remote_name="$(matching_remote "$repo_path" "$remote_key")" || die "no matching remote in $repo_path"

  local prepared
  mapfile -t prepared < <(prepare_review_checkout "$repo_path" "$REPO_NAME" "$PR_NUMBER" "$remote_name")

  printf 'repo_host=%s\n' "$REPO_HOST"
  printf 'repo_owner=%s\n' "$REPO_OWNER"
  printf 'repo_name=%s\n' "$REPO_NAME"
  printf 'pr_number=%s\n' "$PR_NUMBER"
  printf 'source_repo=%s\n' "$repo_path"
  printf 'review_path=%s\n' "${prepared[0]}"
  printf 'checkout_ref=%s\n' "${prepared[1]}"
  printf 'diff_cmd=%s\n' "${prepared[2]}"
  printf 'review_hint=%s\n' "${prepared[3]}"
}

main "$@"
