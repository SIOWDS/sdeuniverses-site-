#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
manifest="$repo_root/public/health/companion-manifest.json"
failures=0

resolve_public_url(){ local url="$1"; printf '%s/public/%sindex.html\n' "$repo_root" "${url#/}"; }

for key in selected_originals interpretations practice_guides
do
  expected="$(jq -r ".counts.$key" "$manifest")"
  if [[ "$expected" -ne 10 ]]; then printf 'FAIL count %s=%s\n' "$key" "$expected"; failures=$((failures+1)); fi
done

while IFS=$'\t' read -r original interpretation practice
do
  for url in "$original" "$interpretation" "$practice"; do
    file="$(resolve_public_url "$url")"
    if [[ ! -f "$file" ]]; then printf 'FAIL missing %s\n' "$url"; failures=$((failures+1)); fi
  done
  original_file="$(resolve_public_url "$original")"
  if ! rg -q 'bindi-triad-wrap' "$original_file"; then printf 'FAIL original triad %s\n' "$original"; failures=$((failures+1)); fi
  for url in "$interpretation" "$practice"; do
    file="$(resolve_public_url "$url")"
    if [[ -f "$file" ]]; then
      chars="$(pandoc "$file" -t plain | wc -m)"
      if [[ "$chars" -lt 5000 || "$chars" -gt 8500 ]]; then printf 'FAIL length %s %s\n' "$chars" "$url"; failures=$((failures+1)); else printf 'PASS length %s %s\n' "$chars" "$url"; fi
      if rg -q '\$[A-Za-z_]+\$|\$if\(' "$file"; then printf 'FAIL template %s\n' "$url"; failures=$((failures+1)); fi
    fi
  done
done < <(jq -r '.items[] | [.original,.interpretation,.practice] | @tsv' "$manifest")

if [[ "$failures" -ne 0 ]]; then printf 'Validation failed: %s issue(s)\n' "$failures"; exit 1; fi
printf 'Validation passed.\n'

