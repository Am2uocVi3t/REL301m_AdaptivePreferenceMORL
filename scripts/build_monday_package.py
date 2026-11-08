#!/usr/bin/env python3
"""Build a portable team package from existing artifacts; no models or network."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import textwrap
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/monday-team/REL301m_Team_Review_2026-10-19"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
EVIDENCE = [
    "research/qualification/minecart_pcqn_backbone_v1.json",
    "research/qualification/minecart_pcqn_backbone_v2.json",
    "research/qualification/course_matrix_post_validation_gate_v1.json",
    "research/claims.json",
    "research/experiments/registry.json",
]
PAPER = [
    "main.tex",
    "General/Preamble.tex",
    "Chapters/0. Frontpage.tex",
    "Chapters/Progress.tex",
    "Figures/qualification-results.tex",
    "Figures/research-timeline.tex",
    "Figures/morl-pipeline.tex",
    "Figures/0. General/fpt_logo_red_small.png",
    "Figures/0. General/fpt_logo_gray.png",
    "Figures/0. General/fpt.png",
    "EVIDENCE_INDEX.md",
]

SPEAKER_NOTES = """# Kịch bản trình bày khoảng 4 phút

## 0:00-0:45 | Vấn đề và phạm vi
MORL phải tối ưu nhiều mục tiêu xung đột. Nhóm nghiên cứu cách phân bổ một ngân sách
cố định giữa các preference bằng gap, disagreement, coverage/recency và learning
progress. Đây là một nghiên cứu so sánh có kiểm soát, không tuyên bố conditioning
hay adaptive allocation là ý tưởng mới.

## 0:45-1:45 | Những việc đã thực sự hoàn thành
Mở PDF và phần Kết quả thật trong index.html. Pipeline Q-learning, replay, fixed
protocols, paired controls và provenance đã có. 30 primary jobs và validation audit
đã hoàn tất nhưng Minecart bị zero ore. V1 không đạt all-seeds; v2 dùng PER và cũng
không đạt. Ba selected checkpoints v2 đều 0/160 ở mỗi ore objective.
Source audit pass không đồng nghĩa behavior qualification pass.

## 1:45-2:45 | Demo offline
Mở phần Minh họa. Kéo preference slider từ 0.5 về 0 rồi 1: utility và lựa chọn thay
đổi trên ba reward vector giả định. Nói rõ đây không phải trained policy hay Pareto
front đo được. Chọn tình huống hai seed đạt, một seed không đạt: all-seeds vẫn FAIL.
Chọn cả ba seed đạt để giải thích luật; bảng dữ liệu thật phía trên vẫn giữ nguyên.

## 2:45-3:30 | Review và giới hạn
Claude đã review độc lập một packet artifact và thấy cách báo cáo nhất quán với
lưu ý. Reviewer không có raw tensors để audit lại. Không suy ra allocation benefit,
robustness, PER vô dụng trong mọi bài toán hay hoàn thành so sánh khóa học.
Không dùng hypervolume dương để nói policy đã học được ore.

## 3:30-4:00 | Điều cần giảng viên hướng dẫn
Nhóm nên báo cáo kết quả âm trong scope đã đóng băng, hay cần scope amendment có
version? Evidence explorer có đáp ứng yêu cầu initial demo không? Nhóm chưa triển
khai thay đổi scope, v3 hoặc final-test. Nếu demo không mở được, chiếu video_tom_tat.mp4
và thuyết minh theo kịch bản này; video không tiếng, có chữ tiếng Việt.

## Team tự phân công trước khi trình bày
- Một người dẫn vấn đề và phương pháp.
- Một người thao tác demo và giữ video dự phòng.
- Một người trả lời số liệu, giới hạn và ghi quyết định của giảng viên.
Không tự coi các vai trò này là phân công đã chốt cho từng thành viên.

## Câu trả lời ngắn cho Q&A
- Vì sao vẫn là tiến độ? Có implementation, executed evidence và failure diagnosis;
  chưa có comparative outcome đủ điều kiện.
- Có phải thuật toán thích nghi không hiệu quả? Chưa thể kết luận: backbone chung
  chưa đạt qualification trên Minecart.
- Vì sao không chạy thêm ngay? Frozen failure rule đã yêu cầu dừng current-scope
  remediation; cần quyết định giảng viên trước thay đổi scope.
- Demo có phải chạy agent? Không. Đây là evidence explorer và minh họa luật bằng
  dữ liệu giả, không load model hoặc chạy môi trường.
- Có dùng test split không? Không có final-test mới nào được truy cập để làm gói.
"""

CHECKLIST = """# Checklist review trước thứ Hai 19/10/2026

- [ ] Giải nén ZIP vào một thư mục; không mở HTML ngay bên trong ZIP.
- [ ] Mở REL301m_Progress_Report.pdf; kiểm tra tên nhóm, mã số và tên giảng viên.
- [ ] Xác nhận đây là initial progress report, không phải final comparative paper.
- [ ] Mở index.html trong trình duyệt có JavaScript; không cần internet hoặc Python.
- [ ] Thấy 3 seed v2, mỗi ore objective 0/160, all-seeds FAIL.
- [ ] Preference slider đổi lựa chọn A/B/C; cả mục luôn được ghi dữ liệu giả.
- [ ] Tình huống giả không làm thay đổi bảng kết quả thật hoặc scientific gates.
- [ ] Mở video_tom_tat.mp4; video tóm tắt có chữ, không tiếng, không footage policy.
- [ ] Thống nhất ai mở demo, ai thuyết trình, ai trả lời câu hỏi; tập khoảng 4 phút.
- [ ] Mở sẵn PDF và video trên máy mang đến lớp, lưu thêm một bản dự phòng.
- [ ] Hỏi giảng viên về phạm vi tiếp theo và tiêu chuẩn initial demo; không tự chạy v3.

Chưa thể xác nhận thay team: tên nhóm đúng ở bản cuối, thiết bị trình chiếu và yêu cầu
nộp chính thức. Gói này sẵn cho review nội bộ, không tự submit hoặc gửi thay người dùng.
"""

README = """# REL301m - Gói team review cho thứ Hai 19/10/2026

## Mở ngay
1. Giải nén toàn bộ ZIP.
2. Mở **index.html** bằng Chrome, Edge hoặc Firefox (JavaScript bật).
3. Đọc **REL301m_Progress_Report.pdf** (English) và **Huong_dan_nhom.pdf** (tiếng Việt).
4. Dùng **SPEAKER_NOTES_VI.md** để tập 4 phút; tick **TEAM_REVIEW_CHECKLIST.md**.
5. Nếu demo gặp lỗi, mở **video_tom_tat.mp4**: 72 giây, chữ tiếng Việt, không tiếng.

Không cần cài thư viện, chạy Python, internet, API key hoặc research environment.
Demo chỉ đọc snapshot đã đóng gói; không có nút chạy training hoặc gọi Claude.
Video là tóm tắt bằng chứng, không phải screen recording hay footage policy inference.

## Điều đã có / chưa có
- Có: report, bảng qualification thật, minh họa preference và luật gate bằng dữ liệu
  giả, metadata nguồn, Claude review summary và checklist trước buổi trình bày.
- Chưa có: successful policy-control demo, environment rollout, comparative benefit,
  final-test results, final paper hoặc chứng nhận unattended ARIS.
- Minecart v2 failed; matrix v1 và final-test vẫn bị khóa. Không chạy thêm chỉ để demo.

## Sửa báo cáo nếu cần
Nguồn LaTeX và BibTeX nằm trong **source/**. Nếu đã có LaTeX tương thích:
`cd source/paper/REL301m` rồi `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`.
Xem PDF đã build nếu máy không có font/package của template. Không cần build để review.
Không có paper PDFs của bên thứ ba hoặc checkpoint trong ZIP.

## Gửi nhận xét cho nhóm
Ghi rõ trang/section, câu đang hiểu khác, số liệu cần kiểm tra hoặc yêu cầu của giảng
viên. Tự xác nhận phân vai và thiết bị; không mặc định có yêu cầu nộp đã được kiểm tra.
Xem **EVIDENCE_INDEX.md** và **MANIFEST.json** để biết nguồn và SHA-256 các file.
"""


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def brief(path: Path) -> None:
    pdfmetrics.registerFont(TTFont("DV", str(FONT_DIR / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DV-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("VI", fontName="DV", fontSize=10, leading=15, spaceAfter=8, alignment=TA_LEFT))
    styles.add(
        ParagraphStyle(
            "VIH",
            fontName="DV-Bold",
            fontSize=15,
            leading=21,
            spaceBefore=13,
            spaceAfter=8,
            textColor=colors.HexColor("#c34d17"),
        )
    )
    styles.add(ParagraphStyle("VIT", fontName="DV-Bold", fontSize=23, leading=29, spaceAfter=16))
    story = []

    def p(text: str, kind: str = "VI") -> None:
        story.append(Paragraph(escape(text), styles[kind]))

    p("Chuẩn bị cùng team", "VIT")
    p("REL301m | Thứ Hai 19/10/2026 | Bằng chứng đến 17/10/2026")
    p("Thông điệp cần thống nhất", "VIH")
    p(
        "Nhóm đã triển khai pipeline và có thí nghiệm, audit, failure diagnosis. "
        "Minecart v2 không đạt qualification; chưa có kết luận adaptive allocation tốt hơn controls."
    )
    p("Ba số liệu nên nhớ", "VIH")
    p(
        "V2: 3 seed, 30 checkpoint, 4.800 episode validation. Mọi selected checkpoint "
        "có 0/160 episode dương cho từng ore objective. Ngưỡng là 8/160 và 2 giá trị dương "
        "phân biệt cho mỗi objective, tất cả seed phải đạt."
    )
    p(
        "Source audit pass khác qualification fail. 4.710.905 bước independent audit "
        "được ghi riêng với training-validation, dù hai số trùng nhau."
    )
    p("Demo thực sự làm gì?", "VIH")
    p(
        "Mở index.html: xem kết quả thật và nguồn. Preference slider và tình huống "
        "all-seeds là dữ liệu giả để giải thích luật; không phải learned policy, "
        "Pareto front hay environment rollout. Video 72 giây là tóm tắt không tiếng."
    )
    p("Claude review nói gì?", "VIH")
    p(
        "Packet nhất quán với caveat về wording gate lịch sử; reviewer không audit lại "
        "raw tensors vì không có trong packet. Negative v2 đã có trong experiment registry. "
        "Review không nâng claim và không mở test. Chỉ một paid invocation đã hoàn tất, "
        "CLI cost $0.0954889; paid policy đã tắt, unattended chưa sẵn sàng."
    )
    story.append(PageBreak())
    p("Tập trình bày trong 4 phút", "VIT")
    for title, text in [
        (
            "0:00-0:45 | Vấn đề",
            "MORL có nhiều mục tiêu; nhóm so sánh cách phân bổ ngân sách "
            "giữa preferences. Không nói conditioning hoặc adaptive allocation là ý tưởng hoàn toàn mới.",
        ),
        (
            "0:45-1:45 | Bằng chứng",
            "Mở PDF và bảng v2. Giải thích 0/160, all-seeds fail, "
            "source audit và khóa final-test. Không biến khác biệt seed v1/v2 thành causal estimate của PER.",
        ),
        (
            "1:45-2:45 | Demo",
            "Kéo slider giả định về 0 rồi 1. Chọn hai seed đạt, một seed fail; "
            "sau đó chọn cả ba đạt để minh họa. Bảng kết quả thật vẫn không thay đổi.",
        ),
        (
            "2:45-3:30 | Giới hạn",
            "Chưa có comparative benefit hoặc generalization claim. "
            "Review chỉ kiểm tra packet. Báo cả chi phí lần seed11 gián đoạn, không chỉ ba runs hoàn tất.",
        ),
        (
            "3:30-4:00 | Xin hướng dẫn",
            "Báo cáo kết quả âm theo scope đã đóng băng hay cần scope "
            "amendment có version? Evidence explorer có đáp ứng checkpoint demo không?",
        ),
    ]:
        p(title, "VIH")
        p(text)
    p("Team cần kiểm tra trước buổi học", "VIH")
    p(
        "Tên/mã số/giảng viên trong PDF; mở thử HTML và video sau khi ngắt mạng; phân vai "
        "thuyết trình/demo/Q&A; xác nhận thiết bị và yêu cầu nộp. Không tự chạy training, v3, "
        "paid review mới hoặc final-test. Checklist và kịch bản đầy đủ nằm cạnh PDF này."
    )

    def furniture(canvas, doc):
        canvas.setFont("DV", 8)
        canvas.setFillColor(colors.HexColor("#50616b"))
        canvas.drawString(20 * mm, 13 * mm, "REL301m | Team review, không phải final paper")
        canvas.drawRightString(190 * mm, 13 * mm, str(doc.page))

    doc = SimpleDocTemplate(
        str(path),
        pagesize=(210 * mm, 297 * mm),
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=22 * mm,
        title="REL301m - Hướng dẫn team review",
    )
    doc.build(story, onFirstPage=furniture, onLaterPages=furniture)


def video(directory: Path, target: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(str(FONT_DIR / "DejaVuSans.ttf"), 31)
    title_font = ImageFont.truetype(str(FONT_DIR / "DejaVuSans-Bold.ttf"), 49)
    small = ImageFont.truetype(str(FONT_DIR / "DejaVuSans.ttf"), 20)
    scenes = [
        (
            "Một pipeline đã chạy.\nMột gate chưa vượt qua.",
            [
                "REL301m: Preference Allocation in MORL",
                "Báo cáo tiến độ ngày 19/10/2026.",
                "Snapshot bằng chứng: 17/10/2026.",
            ],
        ),
        (
            "Câu hỏi nghiên cứu",
            [
                "Phân bổ ngân sách giữa các preference như thế nào?",
                "Gap, disagreement, coverage/recency, learning progress.",
                "So sánh với uniform và compute-matched random controls.",
            ],
        ),
        (
            "Minecart v2: qualification FAIL",
            [
                "3 seed x 10 checkpoint = 30 checkpoint; 4.800 episode.",
                "Selected checkpoints: 0/160 dương ở cả hai ore objectives.",
                "Ngưỡng: 8/160 và 2 giá trị dương phân biệt, mọi seed.",
            ],
        ),
        (
            "Demo có thể trình bày gì?",
            [
                "Bảng qualification thật và nguồn artifact.",
                "Preference slider + luật all-seeds bằng dữ liệu giả.",
                "Không load policy, không rollout, không tạo kết quả mới.",
            ],
        ),
        (
            "Independent review và giới hạn",
            [
                "Claude: packet nhất quán, có caveat về wording lịch sử.",
                "Raw tensors không có trong packet để audit lại.",
                "Chưa chứng minh allocation benefit hoặc publication-ready.",
            ],
        ),
        (
            "Điều cần giảng viên hướng dẫn",
            [
                "Báo cáo negative result hay scope amendment có version?",
                "Evidence explorer có đáp ứng yêu cầu initial demo không?",
                "Training/v3, checkpoint lock và final-test vẫn bị khóa.",
            ],
        ),
    ]
    for index, (title, lines) in enumerate(scenes):
        image = Image.new("RGB", (1280, 720), "#ffffff")
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 18, 720), fill="#c34d17")
        draw.text((68, 39), f"REL301m  /  {index + 1:02d}  /  TEAM REVIEW", font=small, fill="#c34d17")
        y = 96
        for title_line in title.splitlines():
            draw.text((68, y), title_line, font=title_font, fill="#172b36")
            y += 68
        y = max(y + 30, 270)
        for line in lines:
            for wrapped in textwrap.wrap(line, width=65):
                draw.text((70, y), wrapped, font=font, fill="#334e5b")
                y += 47
            y += 17
        if y > 635:
            raise ValueError("Video caption exceeds safe area")
        draw.line((68, 650, 1212, 650), fill="#d9e0e4", width=2)
        draw.text(
            (68, 672),
            "Tóm tắt từ artifact, không phải ghi hình agent. Không tiếng; có chữ tiếng Việt.",
            font=small,
            fill="#50616b",
        )
        image.save(directory / f"frame-{index:02d}.png")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-framerate",
            "1/12",
            "-i",
            str(directory / "frame-%02d.png"),
            "-c:v",
            "libx264",
            "-r",
            "24",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(target),
        ],
        check=True,
        timeout=120,
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    def copy(source: Path, destination: str) -> None:
        target = OUT / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        paths.append(target)

    def text(destination: str, content: str) -> None:
        target = OUT / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        paths.append(target)

    for name in ["index.html", "style.css", "app.js"]:
        copy(ROOT / "demo/monday" / name, name)
    v2 = load(EVIDENCE[1])
    if v2["passed"] is not False or len(v2["seed_decisions"]) != 3:
        raise ValueError("Unexpected qualification; update demo interpretation before packaging")
    text("data.js", "window.DEMO_DATA = " + json.dumps({"v2": v2}, ensure_ascii=False) + ";\n")
    copy(ROOT / "paper/REL301m/main.pdf", "REL301m_Progress_Report.pdf")
    for source in EVIDENCE:
        copy(ROOT / source, "evidence/" + Path(source).name)
    for source in PAPER:
        copy(ROOT / "paper/REL301m" / source, "source/paper/REL301m/" + source)
    copy(ROOT / "research/literature/library.bib", "source/research/literature/library.bib")
    result = load("research/qualification/aris_single_batch_result_v1.json")
    summary = {
        "batch_id": result["batch_id"],
        "provider_invocations": result["provider_invocations"],
        "actual_model": result["actual_model"],
        "review_verdict": result["review_verdict"],
        "cli_cost_usd": result["cost_metadata"]["actual_cost_usd"],
        "cost_basis": "provider CLI list estimate, not Console billing",
        "review_independence": "cross-family",
        "raw_tensors_reviewed": False,
        "scientific_acceptance": False,
        "unattended_ready": False,
    }
    text("evidence/review_summary.json", json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    text("README.md", README)
    text("SPEAKER_NOTES_VI.md", SPEAKER_NOTES)
    text("TEAM_REVIEW_CHECKLIST.md", CHECKLIST)
    text(
        "EVIDENCE_INDEX.md",
        "# Bằng chứng trong gói\n\n"
        + "\n".join(f"- `{Path(source).name}`: bản sao từ `{source}` trong repository." for source in EVIDENCE)
        + "\n\nMetadata có thể trỏ đến đường dẫn raw artifact trong full repo. "
        "Gói không sao chép tensor, checkpoint hoặc paper PDF bên thứ ba. "
        "Bảng v2 hiển thị selected-checkpoint counts; các minh họa luôn dùng dữ liệu giả.\n",
    )
    brief(OUT / "Huong_dan_nhom.pdf")
    paths.append(OUT / "Huong_dan_nhom.pdf")
    video(ROOT / "outputs/monday-team/video-frames", OUT / "video_tom_tat.mp4")
    paths.append(OUT / "video_tom_tat.mp4")
    manifest = {
        "kind": "REL301m_internal_team_review_package",
        "checkpoint": "2026-10-19",
        "evidence_cutoff": "2026-10-17",
        "new_training_or_test_access": False,
        "video_type": "72-second captioned summary; not live policy footage; no audio",
        "files": {str(path.relative_to(OUT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(paths)},
    }
    text("MANIFEST.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    archive = OUT.with_suffix(".zip")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as package:
        for path in paths:
            package.write(path, arcname=str(Path(OUT.name) / path.relative_to(OUT)))
    print(json.dumps({"directory": str(OUT), "zip": str(archive), "files": len(paths)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
