#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
template="$repo_root/tools/health-companions/template.html"

find "$repo_root/public/column" "$repo_root/public/health/medicine" -type f -name source.md \( -path '*/interpretation/source.md' -o -path '*/practice/source.md' \) -print0 |
while IFS= read -r -d '' source
do
  target="${source%/source.md}/index.html"
  kind="$(basename "$(dirname "$source")")"
  common="$repo_root/tools/health-companions/${kind}-common.md"
  pandoc "$source" "$common" --from=gfm+yaml_metadata_block --to=html5 --standalone --id-prefix=h- --template="$template" --output="$target"
  printf 'built %s\n' "${target#"$repo_root/"}"
done

