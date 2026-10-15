#!/bin/bash
#
# Check that the "branch" field of every submodule in .gitmodules describes
# the commit actually pinned in this repository:
#
#   branch = <tag>     the pinned commit must be exactly that tag
#   branch = <branch>  the pinned commit must be reachable from that branch
#
# Note that `git submodule update --remote` only works with the second form;
# for submodules pinned to a release tag the field is a record of that tag.
#
# The pinned commits are read from the index, so this also checks staged
# submodule updates before they are committed.
#
# Usage: .github/scripts/check-gitmodules.sh [--report-updates]
#   --report-updates  also report newer upstream release tags, and how far
#                     branch-tracked submodules are behind their branch tip

report_updates=false
[[ "${1:-}" == "--report-updates" ]] && report_updates=true

cd "$(git rev-parse --show-toplevel)" || exit 1
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

nerr=0
report=()
error() { report+=("FAIL  $1"); nerr=$((nerr+1)); }
ok()    { report+=("ok    $1"); }
info()  { report+=("      $1"); }

# Every gitlink must have a .gitmodules entry
names=$(git config -f .gitmodules --name-only --get-regexp '^submodule\..*\.path$' \
        | sed -e 's/^submodule\.//' -e 's/\.path$//')
for path in $(git ls-files -s | awk '$1=="160000"{print $4}'); do
  if ! git config -f .gitmodules --get-regexp '^submodule\..*\.path$' | awk '{print $2}' | grep -qx "$path"; then
    error "$path: pinned in the repository but missing from .gitmodules"
  fi
done

for name in $names; do
  path=$(git config -f .gitmodules "submodule.$name.path")
  url=$(git config -f .gitmodules "submodule.$name.url")
  branch=$(git config -f .gitmodules "submodule.$name.branch")
  pin=$(git ls-files -s -- "$path" | awk '$1=="160000"{print $2}')

  if [[ -z "$pin" ]]; then
    error "$path: listed in .gitmodules but not pinned in the repository"
    continue
  fi
  if [[ -z "$branch" ]]; then
    error "$path: no branch field in .gitmodules (pinned at ${pin:0:10})"
    continue
  fi

  if ! refs=$(git ls-remote "$url" "refs/tags/$branch" "refs/tags/$branch^{}" "refs/heads/$branch"); then
    error "$path: cannot read refs from $url"
    continue
  fi
  # For annotated tags, compare against the peeled commit
  tag_sha=$(awk -v r="refs/tags/$branch^{}" '$2==r{print $1}' <<< "$refs")
  [[ -z "$tag_sha" ]] && tag_sha=$(awk -v r="refs/tags/$branch" '$2==r{print $1}' <<< "$refs")
  head_sha=$(awk -v r="refs/heads/$branch" '$2==r{print $1}' <<< "$refs")

  if [[ -n "$tag_sha" ]]; then
    if [[ "$tag_sha" == "$pin" ]]; then
      ok "$path: pinned at tag $branch"
    else
      error "$path: .gitmodules says tag $branch (${tag_sha:0:10}) but the pinned commit is ${pin:0:10}"
    fi
    if $report_updates; then
      # Newest release tag with the same naming scheme, skipping alpha/beta/rc
      prefix=${branch%%[0-9]*}
      latest=$(git ls-remote --tags --refs "$url" | awk '{sub("refs/tags/", "", $2); print $2}' \
               | grep -E "^${prefix}[0-9][0-9.]*$" | sort -V | tail -1)
      [[ -n "$latest" && "$latest" != "$branch" ]] && info "$path: newer release tag available: $latest"
    fi
  elif [[ -n "$head_sha" ]]; then
    # Fetch only the commit graph of the branch to check ancestry
    repo="$tmpdir/$name"
    git init -q --bare "$repo"
    git -C "$repo" remote add origin "$url"
    if ! git -C "$repo" fetch -q --filter=tree:0 origin "+refs/heads/$branch:refs/heads/tip"; then
      error "$path: cannot fetch branch $branch from $url"
      continue
    fi
    if git -C "$repo" merge-base --is-ancestor "$pin" tip 2>/dev/null; then
      ok "$path: pinned commit ${pin:0:10} is on branch $branch"
      if $report_updates; then
        behind=$(git -C "$repo" rev-list --count "$pin..tip")
        [[ "$behind" -gt 0 ]] && info "$path: $behind commits behind the tip of $branch"
      fi
    else
      error "$path: pinned commit ${pin:0:10} is not on branch $branch of $url"
    fi
  else
    error "$path: $branch is neither a tag nor a branch in $url"
  fi
done

printf '%s\n' "${report[@]}"
if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  { echo '```'; printf '%s\n' "${report[@]}"; echo '```'; } >> "$GITHUB_STEP_SUMMARY"
fi

if [[ $nerr -gt 0 ]]; then
  echo
  echo "$nerr problem(s) found: .gitmodules and the pinned submodule commits disagree."
  echo "Either set the branch field to the tag or branch the pinned commit is on,"
  echo "or move the submodule to a commit on the tag or branch named there."
  exit 1
fi
