# -*- coding: utf-8 -*-
"""给已生成的 PDF 盖居中页码（wkhtmltopdf 的 --footer-* 在未打补丁的 qt 下被忽略）。"""
import io, sys
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

def stamp(path: Path):
    reader = PdfReader(str(path))
    writer = PdfWriter()
    for i, page in enumerate(reader.pages, 1):
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#6C6553"))
        c.drawCentredString(A4[0] / 2, 30, str(i))
        c.save()
        buf.seek(0)
        page.merge_page(PdfReader(buf).pages[0])
        writer.add_page(page)
    tmp = path.with_suffix(".stamped.pdf")
    with open(tmp, "wb") as fh:
        writer.write(fh)
    tmp.replace(path)
    return len(reader.pages)

if __name__ == "__main__":
    total = 0
    for p in sorted(Path(sys.argv[1]).glob("*/*.pdf")):
        n = stamp(p)
        total += n
        print(f"  {p.parent.name:28s} {n:>3d}页")
    print(f"共 {total} 页已盖页码")
