#!/usr/bin/env python3
"""Extract review material for Zhang Qiong batch-2 mother articles."""

from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "public" / "students" / "zhang-qiong"
TAIL = re.compile(r"参考|文献|注释|附论|增补|校勘|编者|评分|致谢|补记|版本说明|声明")


class Extractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_h2 = False
        self.in_p = False
        self.h2_buf: list[str] = []
        self.p_buf: list[str] = []
        self.headings: list[str] = []
        self.paragraphs: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "h2":
            self.in_h2 = True
            self.h2_buf = []
        elif tag == "p":
            self.in_p = True
            self.p_buf = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "h2" and self.in_h2:
            self.in_h2 = False
            text = re.sub(r"\s+", " ", "".join(self.h2_buf)).strip()
            if text:
                self.headings.append(text)
        elif tag == "p" and self.in_p:
            self.in_p = False
            text = re.sub(r"\s+", " ", "".join(self.p_buf)).strip()
            if text:
                self.paragraphs.append(text)

    def handle_data(self, data: str) -> None:
        if self.in_h2:
            self.h2_buf.append(data)
        if self.in_p:
            self.p_buf.append(data)


def main() -> None:
    manifest = json.loads((BASE / "companion-manifest.json").read_text())
    for number, item in enumerate((x for x in manifest["items"] if x.get("batch") == 2), 21):
        parser = Extractor()
        parser.feed((BASE / item["slug"] / "index.html").read_text())
        headings = [h for h in parser.headings if not TAIL.search(h)]
        joined = " ".join(parser.paragraphs)
        terms: list[str] = []
        for term in re.findall(r"[“‘]([^”’]{2,16})[”’]", joined):
            term = re.sub(r"\s+", "", term)
            if 2 <= len(term) <= 12 and term not in terms:
                terms.append(term)
        print(f"\n### {number} {item['slug']} | {item['title']}")
        for heading in headings:
            print(f"- {heading}")
        print("QUOTED:", " / ".join(terms[:30]))


if __name__ == "__main__":
    main()
