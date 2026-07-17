#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
snapshot_script="$script_dir/git-snapshot.sh"
temp_root="$(mktemp -d "${TMPDIR:-/tmp}/git fatality snapshot.XXXXXX")"
trap 'rm -rf "$temp_root"' EXIT

assert_contains() {
  local haystack="$1"
  local needle="$2"
  if [[ "$haystack" != *"$needle"* ]]; then
    printf 'expected output to contain: %s\n' "$needle" >&2
    exit 1
  fi
}

field() {
  local output="$1"
  local key="$2"
  printf '%s\n' "$output" | sed -n "s/^${key}=//p" | head -n 1
}

remote="$temp_root/remote.git"
repo="$temp_root/repo"
detached="$temp_root/detached"
conflict="$temp_root/conflict"
unborn="$temp_root/unborn"

git init --bare --quiet "$remote"
git init --quiet "$repo"
git -C "$repo" symbolic-ref HEAD refs/heads/main
git -C "$repo" config user.name "Snapshot Test"
git -C "$repo" config user.email "snapshot@example.test"
printf 'base\n' > "$repo/tracked.txt"
git -C "$repo" add tracked.txt
git -C "$repo" commit --quiet -m "initial commit"
git -C "$repo" remote add origin "$remote"
git -C "$repo" push --quiet -u origin main
git -C "$repo" remote set-head origin main

printf 'staged one\n' > "$repo/staged.txt"
git -C "$repo" add staged.txt
printf 'unstaged\n' >> "$repo/tracked.txt"
printf 'untracked one\n' > "$repo/untracked.txt"

first_output="$(bash "$snapshot_script" "$repo")"
assert_contains "$first_output" "branch=main"
assert_contains "$first_output" "upstream=origin/main"
assert_contains "$first_output" "default_remote_heads=origin/main"
assert_contains "$first_output" "behind=0"
assert_contains "$first_output" "ahead=0"
assert_contains "$first_output" "operation=none"
assert_contains "$first_output" "staged.txt"
assert_contains "$first_output" "untracked.txt"

first_staged="$(field "$first_output" staged_snapshot)"
[[ "$first_staged" =~ ^[0-9a-f]{40,64}$ ]]

printf 'untracked two\n' > "$repo/untracked.txt"
second_output="$(bash "$snapshot_script" "$repo")"
second_staged="$(field "$second_output" staged_snapshot)"

[[ "$first_staged" == "$second_staged" ]]

printf 'staged two\n' >> "$repo/staged.txt"
git -C "$repo" add staged.txt
third_output="$(bash "$snapshot_script" "$repo")"
third_staged="$(field "$third_output" staged_snapshot)"
[[ "$second_staged" != "$third_staged" ]]

merge_head="$(git -C "$repo" rev-parse --git-path MERGE_HEAD)"
if [[ "$merge_head" != /* ]]; then
  merge_head="$repo/$merge_head"
fi
git -C "$repo" rev-parse HEAD > "$merge_head"
merge_output="$(bash "$snapshot_script" "$repo")"
assert_contains "$merge_output" "operation=merge"
rm -f "$merge_head"

git -C "$repo" update-ref -d refs/remotes/origin/main
gone_output="$(bash "$snapshot_script" "$repo")"
assert_contains "$gone_output" "upstream=origin/main"
assert_contains "$gone_output" "behind=gone"
assert_contains "$gone_output" "ahead=gone"

git init --quiet "$detached"
git -C "$detached" symbolic-ref HEAD refs/heads/main
git -C "$detached" config user.name "Snapshot Test"
git -C "$detached" config user.email "snapshot@example.test"
printf 'detached\n' > "$detached/file.txt"
git -C "$detached" add file.txt
git -C "$detached" commit --quiet -m "initial commit"
git -C "$detached" checkout --quiet --detach HEAD
detached_output="$(bash "$snapshot_script" "$detached")"
assert_contains "$detached_output" "branch=(detached)"
assert_contains "$detached_output" "upstream=(none)"

git init --quiet "$conflict"
git -C "$conflict" symbolic-ref HEAD refs/heads/main
git -C "$conflict" config user.name "Snapshot Test"
git -C "$conflict" config user.email "snapshot@example.test"
printf 'base\n' > "$conflict/conflict.txt"
git -C "$conflict" add conflict.txt
git -C "$conflict" commit --quiet -m "initial commit"
git -C "$conflict" branch side
printf 'main\n' > "$conflict/conflict.txt"
git -C "$conflict" commit --quiet -am "change on main"
git -C "$conflict" checkout --quiet side
printf 'side\n' > "$conflict/conflict.txt"
git -C "$conflict" commit --quiet -am "change on side"
git -C "$conflict" checkout --quiet main
if git -C "$conflict" merge --no-edit side >/dev/null 2>&1; then
  printf 'expected a merge conflict\n' >&2
  exit 1
fi

conflict_output="$(bash "$snapshot_script" "$conflict")"
assert_contains "$conflict_output" "operation=merge"
conflict_staged="$(field "$conflict_output" staged_snapshot)"

replacement_oid="$(printf 'replacement ours\n' | git -C "$conflict" hash-object -w --stdin)"
printf '100644 %s 2\tconflict.txt\n' "$replacement_oid" | \
  git -C "$conflict" update-index --index-info
changed_conflict_output="$(bash "$snapshot_script" "$conflict")"
changed_conflict_staged="$(field "$changed_conflict_output" staged_snapshot)"
[[ "$conflict_staged" != "$changed_conflict_staged" ]]

git init --quiet "$unborn"
git -C "$unborn" symbolic-ref HEAD refs/heads/main
unborn_output="$(bash "$snapshot_script" "$unborn")"
assert_contains "$unborn_output" "branch=main"
assert_contains "$unborn_output" "head=(unborn)"
assert_contains "$unborn_output" "upstream=(none)"

printf 'git-snapshot tests passed\n'
