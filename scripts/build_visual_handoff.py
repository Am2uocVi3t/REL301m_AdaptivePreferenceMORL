#!/usr/bin/env python3
"""Build a small visual handoff: two PDFs, native-sprite replays and local player."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/monday-visual"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name in ("LunarLander", "Minecart"):
        receipt = json.loads((ROOT / f"outputs/visual-demo/{name}.complete.json").read_text())
        for filename, expected in receipt["outputs"].items():
            source = ROOT / "outputs/visual-demo" / filename
            if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
                raise ValueError("Unverified replay bytes")
        shutil.copyfile(ROOT / f"outputs/visual-demo/{name}.mp4", OUT / f"{name}.mp4")
        shutil.copyfile(ROOT / f"outputs/visual-demo/{name}-frame-120.jpg", OUT / f"{name}-poster.jpg")
    shutil.copyfile(ROOT / "demo/visual/index.html", OUT / "index.html")
    shutil.copyfile(ROOT / "paper/REL301m/main.pdf", OUT / "REL301m_Progress_Report.pdf")
    font_root = Path("/usr/share/fonts/truetype/dejavu")
    pdfmetrics.registerFont(TTFont("VI", str(font_root / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("VIB", str(font_root / "DejaVuSans-Bold.ttf")))
    body = ParagraphStyle(
        "body", fontName="VI", fontSize=9.5, leading=14, spaceAfter=9, textColor=colors.HexColor("#24334a")
    )
    title = ParagraphStyle("title", parent=body, fontName="VIB", fontSize=22, leading=28, spaceAfter=16)
    heading = ParagraphStyle("heading", parent=body, fontName="VIB", fontSize=13, leading=18, spaceBefore=8)
    story = []

    def p(text: str, style=body) -> None:
        story.append(Paragraph(escape(text), style))

    p("Hướng dẫn demo bằng sprite thật", title)
    p("REL301m | Team review trước thứ Hai 19/10/2026 | Snapshot 17/10/2026")
    p("Mở và trình chiếu", heading)
    p(
        "Đọc báo cáo PDF trước. Mở index.html, chọn LunarLander hoặc Minecart rồi bấm Play. "
        "Video có thanh tua, tốc độ và fullscreen theo trình duyệt. Có thể mở thẳng hai MP4 "
        "bằng VLC hoặc trình phát video, không cần Python, API key hay internet."
    )
    p("Demo này có gì khác?", heading)
    p(
        "Đây là sprite do môi trường MO-Gymnasium thực sự render, hành động từ checkpoint "
        "đã lưu. Hai khung chạy cạnh nhau: checkpoint đầu và checkpoint cuối ngân sách training. "
        "Mỗi khung hiện bước, hành động và cumulative raw vector return. Không còn dùng slider "
        "với reward giả làm demo chính."
    )
    story.append(Image(str(ROOT / "outputs/visual-demo/LunarLander-frame-120.jpg"), width=150 * mm, height=93.75 * mm))
    p("LunarLander: xem từ bắt đầu đến kết thúc", heading)
    p(
        "Checkpoint 50k và 500k của adaptive-PCQN seed 20262001; cùng environment seed 20000 "
        "và preference validation index 8 (đếm từ 0), gần trọng số đều nhất. Episode đầu kết thúc ở bước 86 "
        "với landing component -100; episode cuối kết thúc ở bước 359 với +100. "
        "Chỉ minh họa hai trajectory đã chọn trước, không phải tỷ lệ thành công hoặc bằng chứng ưu thế."
    )
    story.append(PageBreak())
    p("Minecart và cách nói đúng", title)
    story.append(Image(str(ROOT / "outputs/visual-demo/Minecart-frame-120.jpg"), width=150 * mm, height=93.75 * mm))
    p("Minecart: cảnh thất bại cũng là nội dung demo", heading)
    p(
        "Checkpoint 100k và 1M của Uniform-PCQN PER v2 seed 20264011; environment seed 670000. "
        "Cùng preference validation gần trọng số đều nhất. Cả hai episode chạm giới hạn 1.000 bước, "
        "ore returns bằng 0; xe không thu được quặng. Video không dựng một cảnh khai thác thành công "
        "để thay thế policy thật. Qualification độc lập đã thất bại trên cả ba seed."
    )
    p("Training khác inference thế nào?", heading)
    p(
        "Training: agent thu transition, replay và cập nhật network. Inference: giữ nguyên network, "
        "đưa state cùng preference w vào để chọn hành động. Hai khung đều là inference từ hai giai đoạn "
        "training đã lưu, không phải cảnh training trực tiếp và không phải MORL so với non-MORL. "
        "Không chạy training mới để dựng video; không truy cập final test hoặc khóa checkpoint."
    )
    p("Kịch bản khoảng 4 phút", heading)
    p(
        "0:00-0:45 nêu câu hỏi phân bổ ngân sách giữa preferences. 0:45-1:30 phát LunarLander và "
        "giải thích state + w → action. 1:30-2:15 mở Minecart: zero ore, không kết luận chỉ tăng training "
        "là đủ. 2:15-3:15 trình bày qualification và giới hạn trong báo cáo. 3:15-4:00 xin giảng viên "
        "hướng dẫn báo cáo kết quả âm hay scope amendment có version."
    )
    p("Team kiểm tra trước giờ học", heading)
    p(
        "Xác nhận tên/mã số và tên giảng viên trong báo cáo; thử MP4 offline và fullscreen trên laptop "
        "trình chiếu; phân công người nói/demo/Q&A. MP4 đã được decode và xem frame tại môi trường dựng. "
        "Chưa xác minh phát trong trình duyệt của laptop team. Chưa có comparative claim; matrix/final-test "
        "vẫn bị chặn. Không có phí Claude mới, không bật scheduler; ARIS unattended chưa sẵn sàng."
    )

    def footer(canvas, doc):
        canvas.setFont("VI", 8)
        canvas.drawString(20 * mm, 12 * mm, "REL301m | Native-sprite replay, không phải benchmark")
        canvas.drawRightString(190 * mm, 12 * mm, str(doc.page))

    SimpleDocTemplate(
        str(OUT / "Huong_dan_nhom.pdf"),
        pagesize=(210 * mm, 297 * mm),
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=17 * mm,
        bottomMargin=21 * mm,
        title="REL301m - Hướng dẫn demo trực quan",
    ).build(story, onFirstPage=footer, onLaterPages=footer)
    manifest = {
        "purpose": "presentation only",
        "files": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(OUT.iterdir())
            if path.is_file() and path.name != "MANIFEST.json"
        },
    }
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    with zipfile.ZipFile(OUT.with_suffix(".zip"), "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename in [*manifest["files"], "MANIFEST.json"]:
            archive.write(OUT / filename, f"REL301m/{filename}")
    print(str(OUT))


if __name__ == "__main__":
    main()
