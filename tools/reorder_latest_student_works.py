from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

LATEST = {
    "hu-min": ["时差的溶解", "蜕变的代谢条件", "无向的发生"],
    "gao-peng": ["惩罚边界归因性基础设施", "侧翼危机"],
    "putao": ["蜕壳余烬"],
    "wang-tao": ["代理性生成"],
    "kong-fanhe": ["修复的暗面"],
}

DIGITS = "零一二三四五六七八九"


def zh_number(n):
    if n < 10:
        return DIGITS[n]
    if n == 10:
        return "十"
    if n < 20:
        return "十" + DIGITS[n % 10]
    tens, ones = divmod(n, 10)
    return DIGITS[tens] + "十" + (DIGITS[ones] if ones else "")


def title_of(card):
    match = re.search(r"<h2>(.*?)</h2>", card, re.S)
    return re.sub(r"<[^>]+>", "", match.group(1)).strip() if match else ""


def renumber(card, number):
    label = "之" + zh_number(number)
    chip = re.search(r'(<span class="chip">)(.*?)(</span>)', card, re.S)
    if not chip:
        return card
    body = chip.group(2)
    if re.match(r"^之[零一二三四五六七八九十]+(?:\s*·|\s|$)", body):
        body = re.sub(r"^之[零一二三四五六七八九十]+", label, body, count=1)
    else:
        body = label + " · " + body
    return card[:chip.start(2)] + body + card[chip.end(2):]


def update(slug, latest_titles):
    path = ROOT / "public" / "students" / slug / "works" / "index.html"
    text = path.read_text(encoding="utf-8")
    starts = [m.start() for m in re.finditer(r'<div class="work">', text)]
    if not starts:
        raise RuntimeError(f"{slug}: no work cards")
    tail_candidates = [
        pos for pos in (
            text.find('<div class="back">', starts[-1]),
            text.find("</div>\n\n\n<script", starts[-1]),
            text.find("</div>\r\n\r\n\r\n<script", starts[-1]),
            text.find("</div>\n\n<footer", starts[-1]),
            text.find("</div>\r\n\r\n<footer", starts[-1]),
        ) if pos >= 0
    ]
    if not tail_candidates:
        raise RuntimeError(f"{slug}: card-list tail not found")
    tail = min(tail_candidates)
    cards = [text[starts[i]:(starts[i + 1] if i + 1 < len(starts) else tail)] for i in range(len(starts))]
    chosen, remaining = [], cards[:]
    for wanted in latest_titles:
        index = next((i for i, card in enumerate(remaining) if wanted in title_of(card)), None)
        if index is None:
            raise RuntimeError(f"{slug}: missing {wanted}")
        chosen.append(remaining.pop(index))
    ordered = chosen + remaining
    ordered = [renumber(card, len(ordered) - i) for i, card in enumerate(ordered)]
    path.write_text(text[:starts[0]] + "".join(ordered) + text[tail:], encoding="utf-8")
    print(slug, len(ordered), [title_of(card) for card in ordered[:len(latest_titles)]])


for student_slug, titles in LATEST.items():
    update(student_slug, titles)
