#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the main sitemap plus one independent sitemap per formal subsite.

The ownership map and public counters live in ``public/sites/site-data.json``.
The same file is consumed by the Worker, so routing, canonical URLs, visible
statistics and sitemap ownership cannot silently drift apart.

This script reads tracked paths from Git rather than walking only the current
checkout. That keeps it correct in the repository's sparse maintenance clones.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
CATALOG_PATH = PUBLIC / "sites" / "site-data.json"
SKIP = re.compile(r"^/(admin|diag|check)(/|$)|/test(/|$)")


def load_catalog() -> dict:
    with CATALOG_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)
    assert data.get("main_host") == "sdeuniverses.com"
    assert set(data.get("subsites", {})) >= {"liter", "lang", "edu", "health"}
    return data


def tracked_public_files() -> list[str]:
    done = subprocess.run(
        ["git", "ls-files", "public"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    paths = set(filter(None, done.stdout.splitlines()))
    for dirpath, _dirnames, filenames in os.walk(PUBLIC):
        for filename in filenames:
            paths.add((Path(dirpath) / filename).relative_to(ROOT).as_posix())
    return sorted(paths)


def index_url(path: str) -> str | None:
    if not path.endswith("/index.html") and path != "public/index.html":
        return None
    rel = path[len("public/") :]
    if rel == "index.html":
        return "/"
    return "/" + rel[: -len("index.html")]


def owner_for(url: str, catalog: dict) -> str | None:
    for key, site in catalog["subsites"].items():
        ownership = site.get("ownership", {})
        if any(url.startswith(prefix) for prefix in ownership.get("path_prefixes", [])):
            return key
        for book_id in ownership.get("book_ids", []):
            if re.match(rf"^/books/m/{re.escape(str(book_id))}(/|$)", url):
                return key
    return None


def collect(catalog: dict) -> tuple[set[str], dict[str, set[str]]]:
    main_urls = {"/"}
    subsite_urls = {key: {"/"} for key in catalog["subsites"]}

    for path in tracked_public_files():
        url = index_url(path)
        if not url:
            continue

        local_match = re.match(r"^public/sites/([^/]+)/(.*)index\.html$", path)
        if local_match:
            key, rest = local_match.groups()
            if key in subsite_urls:
                local_url = "/" + rest
                if not SKIP.search(local_url):
                    subsite_urls[key].add(local_url)
            continue

        if SKIP.search(url):
            continue
        owner = owner_for(url, catalog)
        if owner:
            subsite_urls[owner].add(url)
        else:
            main_urls.add(url)

    return main_urls, subsite_urls


def sitemap_xml(host: str, urls: set[str]) -> str:
    assert len(urls) < 50000, f"{host} exceeds the 50,000 URL sitemap limit"
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url in sorted(urls):
        lines.append(f"  <url><loc>{escape('https://' + host + url)}</loc></url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def robots_txt(host: str) -> str:
    return (
        f"# {host}\n"
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin/\n"
        "Disallow: /diag\n"
        "Disallow: /check\n\n"
        f"Sitemap: https://{host}/sitemap.xml\n"
    )


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    catalog = load_catalog()
    main_urls, subsite_urls = collect(catalog)
    assert len(main_urls) > 2000, f"main sitemap unexpectedly small: {len(main_urls)}"

    main_host = catalog["main_host"]
    write_text(PUBLIC / "sitemap.xml", sitemap_xml(main_host, main_urls))
    write_text(PUBLIC / "robots.txt", robots_txt(main_host))
    print(f"{main_host}: {len(main_urls)} URLs")

    for key, urls in subsite_urls.items():
        host = catalog["subsites"][key]["host"]
        assert len(urls) > 3, f"{host} sitemap unexpectedly small: {len(urls)}"
        base = PUBLIC / "sites" / key
        write_text(base / "sitemap.xml", sitemap_xml(host, urls))
        write_text(base / "robots.txt", robots_txt(host))
        print(f"{host}: {len(urls)} URLs")


if __name__ == "__main__":
    main()
