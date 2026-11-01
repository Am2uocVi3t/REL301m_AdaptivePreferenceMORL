#!/usr/bin/env python3
"""Render the course report and concise demo guide with embedded Vietnamese fonts."""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/course-report"
SOURCE = ROOT / "paper/course-recovery/REPORT.md"


def configure_fonts() -> None:
    for name, filename in (("Arial", "arial.ttf"), ("Arial-Bold", "arialbd.ttf"), ("Arial-Italic", "ariali.ttf")):
        pdfmetrics.registerFont(TTFont(name, "C:/Windows/Fonts/" + filename))
    pdfmetrics.registerFontFamily(
        "Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic", boldItalic="Arial-Bold"
    )


def inline(value: str) -> str:
    value = html.escape(value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"`(.+?)`", r'<font color="#37576d">\1</font>', value)
    return re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<link href="\2" color="#245e8b">\1</link>', value)


def styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "body": ParagraphStyle("BodyVI", fontName="Arial", fontSize=10, leading=15, spaceAfter=7),
        "small": ParagraphStyle("SmallVI", fontName="Arial", fontSize=8, leading=11, spaceAfter=5),
        "title": ParagraphStyle(
            "TitleVI", fontName="Arial-Bold", fontSize=26, leading=33, textColor=colors.HexColor("#183b52")
        ),
        "h1": ParagraphStyle(
            "H1VI", fontName="Arial-Bold", fontSize=16, leading=22, spaceBefore=14, spaceAfter=9, keepWithNext=True
        ),
        "h2": ParagraphStyle(
            "H2VI", fontName="Arial-Bold", fontSize=12, leading=17, spaceBefore=10, spaceAfter=6, keepWithNext=True
        ),
        "cell": ParagraphStyle("CellVI", fontName="Arial", fontSize=8, leading=11),
        "caption": ParagraphStyle(
            "CaptionVI", parent=base["Normal"], fontName="Arial-Italic", fontSize=8, leading=11, spaceAfter=10
        ),
        "code": ParagraphStyle(
            "CodeVI", fontName="Arial", fontSize=8, leading=11, backColor=colors.HexColor("#f0f4f7"), spaceAfter=6
        ),
    }


def footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#d8e1e7"))
    canvas.line(20 * mm, 17 * mm, A4[0] - 20 * mm, 17 * mm)
    canvas.setFont("Arial", 8)
    canvas.setFillColor(colors.HexColor("#526777"))
    canvas.drawString(20 * mm, 12 * mm, "REL301m | Evidence cutoff: 01/11/2026 | Validation only")
    canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, str(document.page))
    canvas.restoreState()


def table(rows: list[list[str]], width: float, style: dict) -> Table:
    count = len(rows[0])
    weights = [0.23, 0.23, 0.27, 0.27] if count == 4 else [1 / count] * count
    result = Table(
        [[Paragraph(inline(cell), style["cell"]) for cell in row] for row in rows],
        colWidths=[width * weight for weight in weights],
        repeatRows=1,
        hAlign="LEFT",
    )
    result.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6eef3")),
                ("LINEBELOW", (0, 0), (-1, 0), 0.7, colors.HexColor("#9ab0c0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fa")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return result


def markdown_flow(text: str, style: dict, width: float) -> list:
    blocks: list[Any] = []
    paragraph: list[str] = []
    rows: list[list[str]] = []
    code = False
    reference_start: int | None = None

    def flush() -> None:
        if paragraph:
            blocks.append(Paragraph(inline(" ".join(paragraph)), style["body"]))
            paragraph.clear()
        if rows:
            blocks.append(KeepTogether([table(rows, width, style), Spacer(1, 9)]))
            rows.clear()

    for line in text.splitlines():
        if line.startswith("```"):
            flush()
            code = not code
        elif code:
            blocks.append(Paragraph(html.escape(line), style["code"]))
        elif not line.strip():
            flush()
        elif line.startswith("!["):
            flush()
            match = re.fullmatch(r"!\[(.*?)\]\((.*?)\)", line)
            if match is None:
                raise ValueError("Malformed report figure")
            path = ROOT / match[2]
            image = Image(str(path), width=width, height=width * 3 / 8)
            blocks.append(KeepTogether([image, Paragraph(inline(match[1]), style["caption"])]))
        elif line.startswith("|"):
            if paragraph:
                flush()
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if not all(re.fullmatch(r"[-: ]+", cell) for cell in cells):
                rows.append(cells)
        elif line.startswith("#"):
            flush()
            level = len(line) - len(line.lstrip("#"))
            if line.lstrip("# ").startswith("8. Tài liệu tham khảo"):
                reference_start = len(blocks)
            blocks.append(Paragraph(inline(line[level:].strip()), style["h1" if level <= 2 else "h2"]))
        elif line.startswith("- "):
            flush()
            blocks.append(Paragraph("• " + inline(line[2:]), style["body"]))
        else:
            paragraph.append(line.strip())
    flush()
    if reference_start is not None:
        return [*blocks[:reference_start], KeepTogether(blocks[reference_start:])]
    return blocks


def build_report(style: dict) -> None:
    doc = SimpleDocTemplate(
        str(OUT / "REL301m_Course_Report.pdf"),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=19 * mm,
        bottomMargin=23 * mm,
    )
    cover = [
        Spacer(1, 18 * mm),
        Paragraph("REL301m / FALL 2026", style["h2"]),
        Spacer(1, 8 * mm),
        Paragraph("Phân bổ preference<br/>trong Multi-Objective<br/>Reinforcement Learning", style["title"]),
        Spacer(1, 8 * mm),
        Paragraph("Triển khai, bằng chứng validation và giới hạn thực nghiệm", style["h2"]),
        HRFlowable(width="100%", thickness=2, color=colors.HexColor("#245e8b")),
        Spacer(1, 12 * mm),
        table(
            [
                ["Sinh viên", "Mã sinh viên"],
                ["Huynh Quoc Viet", "SE194225"],
                ["Le Nguyen Gia Hung", "SE194127"],
                ["Ngo Hoai Nam", "SE194190"],
            ],
            doc.width,
            style,
        ),
        Spacer(1, 8 * mm),
        Paragraph("Giảng viên: Nam Lưu", style["body"]),
        Paragraph("Ngày lập gói: 01/11/2026 · Môn học bậc đại học", style["body"]),
        Spacer(1, 12 * mm),
        Paragraph(
            "Phạm vi: dữ liệu validation đã phục hồi của 30 job nghiên cứu; demo dùng model mới huấn luyện riêng. "
            "Kết quả âm Minecart được giữ nguyên. Không có final-test claim hoặc kết luận adaptive vượt controls.",
            style["body"],
        ),
        PageBreak(),
    ]
    doc.build(
        cover + markdown_flow(SOURCE.read_text(encoding="utf-8"), style, doc.width),
        onFirstPage=footer,
        onLaterPages=footer,
    )


def build_guide(style: dict) -> None:
    text = (ROOT / "paper/course-recovery/GUIDE_VI.md").read_text(encoding="utf-8")
    doc = SimpleDocTemplate(
        str(OUT / "Huong_dan_Demo.pdf"),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=23 * mm,
    )
    doc.build(markdown_flow(text, style, doc.width), onFirstPage=footer, onLaterPages=footer)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    configure_fonts()
    style = styles()
    build_report(style)
    build_guide(style)
    print(OUT)


if __name__ == "__main__":
    main()
