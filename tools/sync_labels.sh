#!/usr/bin/env bash
# Create or update the GitHub labels in .github/labels.yml.
#
# Usage:
#   tools/sync_labels.sh [--dry-run] [--repo OWNER/REPO] [LABELS_FILE]
#
# The script needs the GitHub CLI (gh). Sign in with "gh auth login" first.
# It reads a simple subset of YAML: a list of items with the keys
# "name", "color", and "description". Each value is on one line.
# It does not delete labels that are not in the file.

set -euo pipefail

dry_run=0
repo_args=()
labels_file=""

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) dry_run=1; shift ;;
    --repo|-R)
      [ $# -ge 2 ] || { echo "error: $1 needs a value" >&2; exit 2; }
      repo_args=(--repo "$2"); shift 2 ;;
    -h|--help) sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "error: unknown option: $1" >&2; exit 2 ;;
    *) labels_file="$1"; shift ;;
  esac
done

if [ -z "$labels_file" ]; then
  labels_file="$(cd "$(dirname "$0")/.." && pwd)/.github/labels.yml"
fi
if [ ! -f "$labels_file" ]; then
  echo "error: $labels_file does not exist" >&2
  exit 1
fi
if [ "$dry_run" -eq 0 ] && ! command -v gh >/dev/null 2>&1; then
  echo "error: the GitHub CLI (gh) is not installed. See https://cli.github.com/" >&2
  exit 1
fi

# Remove the key, the spaces, an optional trailing comment, and the quotes.
value_of() {
  local value="$1"
  value="${value#*:}"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  case "$value" in
    \"*\") value="${value#\"}"; value="${value%\"}" ;;
    \'*\') value="${value#\'}"; value="${value%\'}" ;;
    *) value="${value%%[[:space:]]#*}" ;;
  esac
  printf '%s' "$value"
}

count=0
name=""
color=""
description=""

flush() {
  if [ -z "$name" ]; then
    return
  fi
  if [ -z "$color" ]; then
    echo "error: the label \"$name\" has no color" >&2
    exit 1
  fi
  count=$((count + 1))
  if [ "$dry_run" -eq 1 ]; then
    printf 'gh label create %q --color %q --description %q --force\n' "$name" "$color" "$description"
  else
    gh label create "$name" --color "$color" --description "$description" --force ${repo_args[@]+"${repo_args[@]}"}
  fi
  name=""
  color=""
  description=""
}

while IFS= read -r line || [ -n "$line" ]; do
  line="${line%$'\r'}"
  case "$line" in
    ''|'#'*|[[:space:]]'#'*) continue ;;
  esac
  trimmed="${line#"${line%%[![:space:]]*}"}"
  case "$trimmed" in
    "- name:"*)
      flush
      name="$(value_of "${trimmed#- }")" ;;
    "name:"*) flush; name="$(value_of "$trimmed")" ;;
    "color:"*) color="$(value_of "$trimmed")"; color="${color#\#}" ;;
    "description:"*) description="$(value_of "$trimmed")" ;;
  esac
done < "$labels_file"
flush

echo "$count labels processed from $labels_file" >&2
