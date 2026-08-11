#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
failures=0

resolve_public_url() {
  local url="$1"
  if [[ "$url" == *.html ]]
  then
    printf '%s/public/%s\n' "$repo_root" "${url#/}"
  else
    printf '%s/public/%sindex.html\n' "$repo_root" "${url#/}"
  fi
}

while IFS= read -r manifest
do
  student_slug="$(jq -r '.student.slug' "$manifest")"
  selected="$(jq -r '.selection.selected_originals' "$manifest")"
  interpretations="$(jq -r '.derivatives.interpretations' "$manifest")"
  practices="$(jq -r '.derivatives.practice_guides' "$manifest")"

  if [[ "$selected" -ne 5 || "$interpretations" -ne 5 || "$practices" -ne 5 ]]
  then
    printf 'FAIL manifest counts: %s\n' "$manifest"
    failures=$((failures+1))
  fi

  while IFS=$'\t' read -r original interpretation practice
  do
    for url in "$original" "$interpretation" "$practice"
    do
      target="$(resolve_public_url "$url")"
      if [[ ! -f "$target" ]]
      then
        printf 'FAIL missing page: %s\n' "$url"
        failures=$((failures+1))
      fi
    done
    original_file="$(resolve_public_url "$original")"
    if ! rg -q 'bindi-triad-wrap' "$original_file"
    then
      printf 'FAIL original lacks triad: %s\n' "$original"
      failures=$((failures+1))
    fi

    for companion in "$interpretation" "$practice"
    do
      companion_file="$(resolve_public_url "$companion")"
      if [[ -f "$companion_file" ]]
      then
        rendered_chars="$(pandoc "$companion_file" -t plain | wc -m)"
        if [[ "$rendered_chars" -lt 5000 || "$rendered_chars" -gt 8500 ]]
        then
          printf 'FAIL rendered length %s: %s\n' "$rendered_chars" "$companion"
          failures=$((failures+1))
        else
          printf 'PASS rendered length %s: %s\n' "$rendered_chars" "$companion"
        fi
      fi
    done
  done < <(jq -r '.items[] | [.original,.interpretation,.practice] | @tsv' "$manifest")

  while IFS= read -r source
  do
    chars="$(pandoc "$source" -t plain | wc -m)"
    html="${source%/source.md}/index.html"
    if [[ "$chars" -lt 5000 || "$chars" -gt 6500 ]]
    then
      printf 'FAIL length %s: %s\n' "$chars" "$source"
      failures=$((failures+1))
    else
      printf 'PASS length %s: %s\n' "$chars" "${source#"$repo_root/"}"
    fi
    if rg -q '\$[A-Za-z_]+\$|\$if\(' "$html"
    then
      printf 'FAIL unresolved template variable: %s\n' "$html"
      failures=$((failures+1))
    fi
    if ! rg -q 'class="c-triad"' "$html"
    then
      printf 'FAIL companion lacks triad: %s\n' "$html"
      failures=$((failures+1))
    fi
  done < <(find "$repo_root/public/students/$student_slug" -type f -name source.md \( -path '*/interpretation/source.md' -o -path '*/practice/source.md' \) | sort)
done < <(find "$repo_root/public/students" -mindepth 2 -maxdepth 2 -type f -name companion-manifest.json | sort)

if [[ "$failures" -ne 0 ]]
then
  printf 'Validation failed: %s issue(s)\n' "$failures"
  exit 1
fi

printf 'Validation passed.\n'
