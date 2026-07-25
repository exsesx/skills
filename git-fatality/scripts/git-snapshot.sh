#!/usr/bin/env bash

set -euo pipefail

export GIT_OPTIONAL_LOCKS=0
export GIT_NO_LAZY_FETCH=1
export GIT_TERMINAL_PROMPT=0
export LC_ALL=C

repo_arg="${1:-.}"

if ! repo_root="$(git -C "$repo_arg" rev-parse --show-toplevel 2>/dev/null)"; then
  printf 'error=not-a-git-repository\n' >&2
  exit 2
fi

git_cmd=(
  git --no-pager
  -c color.ui=false
  -c core.fsmonitor=false
  -c core.untrackedCache=false
  -C "$repo_root"
)

if head_oid="$("${git_cmd[@]}" rev-parse --verify 'HEAD^{commit}' 2>/dev/null)"; then
  head_state="$head_oid"
else
  head_state="(unborn)"
fi

if branch="$("${git_cmd[@]}" symbolic-ref --quiet --short HEAD 2>/dev/null)"; then
  :
else
  branch="(detached)"
fi

upstream="(none)"
if [[ "$branch" != "(detached)" ]]; then
  upstream="$("${git_cmd[@]}" for-each-ref --format='%(upstream:short)' "refs/heads/$branch")"
  if [[ -z "$upstream" ]]; then
    branch_remote="$("${git_cmd[@]}" config --get "branch.$branch.remote" || true)"
    branch_merge="$("${git_cmd[@]}" config --get "branch.$branch.merge" || true)"
    if [[ -n "$branch_remote" && -n "$branch_merge" ]]; then
      merge_name="${branch_merge#refs/heads/}"
      if [[ "$branch_remote" == "." ]]; then
        upstream="$merge_name"
      else
        upstream="$branch_remote/$merge_name"
      fi
    fi
  fi
  [[ -z "$upstream" ]] && upstream="(none)"
fi

remote_heads=()
while IFS= read -r remote; do
  [[ -z "$remote" ]] && continue
  if remote_head="$("${git_cmd[@]}" symbolic-ref --quiet --short "refs/remotes/$remote/HEAD" 2>/dev/null)"; then
    remote_heads+=("$remote_head")
  fi
done < <("${git_cmd[@]}" remote)

if ((${#remote_heads[@]} == 0)); then
  default_remote_heads="(none)"
else
  default_remote_heads="$(IFS=,; printf '%s' "${remote_heads[*]}")"
fi

behind="unknown"
ahead="unknown"
if [[ "$upstream" != "(none)" && "$head_state" != "(unborn)" ]]; then
  if "${git_cmd[@]}" rev-parse --verify "${upstream}^{commit}" >/dev/null 2>&1; then
    read -r behind ahead < <(
      "${git_cmd[@]}" rev-list --left-right --count "${upstream}...HEAD"
    )
  else
    behind="gone"
    ahead="gone"
  fi
fi

resolve_git_path() {
  local path
  path="$("${git_cmd[@]}" rev-parse --git-path "$1")"
  if [[ "$path" != /* ]]; then
    path="$repo_root/$path"
  fi
  printf '%s\n' "$path"
}

operations=()
[[ -f "$(resolve_git_path MERGE_HEAD)" ]] && operations+=(merge)
if [[ -d "$(resolve_git_path rebase-merge)" || -f "$(resolve_git_path rebase-apply/rebasing)" ]]; then
  operations+=(rebase)
elif [[ -d "$(resolve_git_path rebase-apply)" ]]; then
  operations+=(am)
fi
[[ -f "$(resolve_git_path CHERRY_PICK_HEAD)" ]] && operations+=(cherry-pick)
[[ -f "$(resolve_git_path REVERT_HEAD)" ]] && operations+=(revert)
[[ -f "$(resolve_git_path BISECT_LOG)" ]] && operations+=(bisect)

if ((${#operations[@]} == 0)); then
  operation="none"
else
  operation="$(IFS=,; printf '%s' "${operations[*]}")"
fi

staged_snapshot="$({
  printf 'git-fatality-staged-v1\0HEAD\0%s\0DIFF\0' "$head_state"
  "${git_cmd[@]}" diff --cached --raw -z --no-abbrev --no-renames \
    --no-ext-diff --no-textconv --no-relative --ignore-submodules=none \
    -O/dev/null --
  printf 'UNMERGED\0'
  "${git_cmd[@]}" ls-files --unmerged -z
} | "${git_cmd[@]}" hash-object --stdin)"

print_section() {
  local label="$1"
  shift
  printf '%s_begin\n' "$label"
  "$@"
  printf '%s_end\n' "$label"
}

printf 'repo_root=%s\n' "$repo_root"
printf 'branch=%s\n' "$branch"
printf 'head=%s\n' "$head_state"
printf 'upstream=%s\n' "$upstream"
printf 'default_remote_heads=%s\n' "$default_remote_heads"
printf 'behind=%s\n' "$behind"
printf 'ahead=%s\n' "$ahead"
printf 'operation=%s\n' "$operation"
printf 'staged_snapshot=%s\n' "$staged_snapshot"

print_section status_porcelain_v2 "${git_cmd[@]}" status --porcelain=v2 --branch \
  --untracked-files=all --ignore-submodules=none --no-renames
print_section staged_stat "${git_cmd[@]}" diff --cached --stat --no-ext-diff \
  --no-textconv --no-renames --no-relative --ignore-submodules=none \
  -O/dev/null --
print_section unstaged_stat "${git_cmd[@]}" diff --stat --no-ext-diff \
  --no-textconv --no-renames --no-relative --ignore-submodules=none \
  -O/dev/null --
