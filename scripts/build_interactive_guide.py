#!/usr/bin/env python3
"""Author the Vietnamese local-inference guide, not a video handoff."""

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    target = ROOT / "artifacts/presentation-build/interactive-docs/Huong_dan.pdf"
    target.parent.mkdir(parents=True, exist_ok=True)
    fonts = Path("/usr/share/fonts/truetype/dejavu")
    pdfmetrics.registerFont(TTFont("VI", str(fonts / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("VIB", str(fonts / "DejaVuSans-Bold.ttf")))
    body = ParagraphStyle("body", fontName="VI", fontSize=10, leading=15, spaceAfter=10)
    title = ParagraphStyle(
        "title",
        parent=body,
        fontName="VIB",
        fontSize=23,
        leading=29,
        spaceAfter=16,
        textColor=colors.HexColor("#153b4c"),
    )
    heading = ParagraphStyle("heading", parent=body, fontName="VIB", fontSize=13, leading=19, spaceBefore=10)
    story = []

    def p(text: str, style=body) -> None:
        story.append(Paragraph(escape(text), style))

    p("Một model. Nhiều ưu tiên.", title)
    p("REL301m | Hướng dẫn website tương tác | 17/10/2026")
    p("Bạn đang điều khiển gì?", heading)
    p(
        "Hai môi trường chạy thật, cùng một checkpoint đã train và cùng seed đầu. Bên trái "
        "dùng preference mặc định, bên phải nhận preference từ slider. Network nhận state + w "
        "để chọn action, không cập nhật trọng số và không training lại. Đây không phải video."
    )
    p("Cài một lần, chạy offline sau đó", heading)
    p(
        "Giải nén toàn bộ REL301m_Interactive_Demo.zip. Cần Python 3.11 và dependency trong "
        "requirements.txt; README_VI.md có lệnh Linux/macOS và Windows, cùng hướng dẫn Box2D/SWIG. "
        "Cài dependency lần đầu cần internet và có thể cần C++ build tools. Không cần GPU, API key, "
        "Node hoặc model tải thêm. Chỉ runtime Linux/Python 3.11 CPU đã được kiểm tra."
    )
    p(
        "Linux/macOS: python3.11 -m venv .venv; cài swig và requirements bằng Python trong .venv "
        "theo README; chạy bash START_DEMO.sh. Windows: py -3.11 -m venv .venv; cài dependency "
        "rồi chạy START_DEMO.bat. Không cài lại dependency mỗi lần mở demo."
    )
    p(
        "Mở http://127.0.0.1:8765 trong trình duyệt. Không double-click website/index.html: "
        "Python backend phải đang chạy. Ctrl+C dừng server. Nếu cổng bận, dùng --port 8766."
    )
    p("Cách trình diễn chính", heading)
    p("1. Chọn LunarLander. Hai bên ban đầu dùng cùng preference mặc định. Bấm Chạy so sánh.")
    p(
        "2. Kéo slider bên phải. Tổng trọng số tự giữ 100%. Trong chế độ thường, thay đổi là "
        "pending. Bấm Chạy so sánh để reset cả hai về cùng seed và áp dụng preference mới."
    )
    p(
        "3. Quan sát sprite, action, số bước và raw vector return. Đây là inference thật từ model, "
        "không chuyển giữa các video. Tạm dừng, Một bước và Tốc độ phục vụ giải thích từng action."
    )
    p(
        "4. Thử Minecart. Chuyển Sprite nâng cấp / Renderer gốc để đối chiếu. Kết thúc episode "
        "không tự chạy lại; bấm Chạy so sánh nếu muốn reset. Không chạy nhiều tab cùng điều khiển."
    )
    story.append(PageBreak())
    p("Thay ưu tiên, không train lại", title)
    p("Live-mode khác reset như thế nào?", heading)
    p(
        "Bật Đổi preference khi đang chạy để w mới vào network từ tick tiếp theo, giữ nguyên state "
        "hiện tại. Khi tạm dừng, kéo slider không tự chạy physics; Tiếp tục hoặc Một bước mới áp dụng. "
        "Bên trái vẫn giữ w mặc định. Cảnh báo lịch sử khác nhau luôn hiện sau một lần đổi w giữa episode. "
        "Reset nếu muốn so lại từ cùng trạng thái đầu."
    )
    p("Tàu và xe đẹp hơn, engine không đổi", heading)
    p(
        "Lớp Canvas vẽ tàu kim loại, kính, động cơ, địa hình; xe, trạm, mỏ và cargo từ tọa độ "
        "môi trường thật. Đường mờ là vị trí đã đi qua. Không sửa physics, collision, reward hay thêm "
        "cargo giả. Renderer gốc dùng để đối chiếu. Đổi skin không tạo bước environment."
    )
    p("Các giới hạn cần nói đúng", heading)
    p(
        "Một checkpoint cho mỗi môi trường; hai bên cùng môi trường dùng chung đúng một network. "
        "Reference ở đây là preference mặc định, không phải một thuật toán baseline khác. Adaptive "
        "allocation trong training và preference conditioning khi sử dụng là hai việc khác nhau."
    )
    p(
        "Slider không đảm bảo mọi state đều đổi action hoặc policy luôn thành công. Minecart v2 chưa "
        "đạt qualification, có thể đứng yên và zero ore. LunarLander có thể rơi hoặc tiêu tốn nhiên liệu. "
        "Không dùng một lần trình diễn để kết luận ưu thế thuật toán hoặc tỷ lệ thành công."
    )
    p(
        "Reward phạt nhiên liệu là số âm; trọng số cao hơn đặt nặng tránh phạt đó. Đọc từng objective "
        "riêng, không cộng raw rewards khác đơn vị để nói bên nào thắng. Model sử dụng scales đã cố định."
    )
    p(
        "Không có training mới, final-test, checkpoint lock, Claude call hay scheduler. Trace JSON "
        "tải từ giao diện chứa state/preference/action/reward và provenance, chỉ phục vụ trình diễn. "
        "Nếu lỗi/timeout: dừng, không retry bước tự động; xem trạng thái rồi reset hoặc tải lại trang."
    )
    p("Checklist cho teammate trước thứ Hai", heading)
    p(
        "Thử cài và mở app trên laptop trình chiếu; chạy LunarLander và Minecart; thử slider pending, "
        "live-mode, pause, một bước, fullscreen và native renderer; kiểm tra console/lỗi mạng. Giữ "
        "README, hai PDF và ZIP dự phòng. Phân vai người nói, điều khiển và Q&A. Xem VERIFICATION.json "
        "để biết phạm vi kiểm chứng; Windows/macOS không được mặc định đã pass."
    )
    story.append(Spacer(1, 4 * mm))
    p(
        "Báo cáo PDF giữ snapshot nghiên cứu; đoạn demo replay cũ trong báo cáo đã được thay "
        "bằng website của gói này. Dùng hướng dẫn này và README để chạy app. Website không "
        "làm thay đổi qualification thất bại hoặc mở scientific gate."
    )

    def footer(canvas, doc):
        canvas.setFont("VI", 8)
        canvas.drawString(20 * mm, 12 * mm, "REL301m | Interactive inference, không training lại")
        canvas.drawRightString(190 * mm, 12 * mm, str(doc.page))

    SimpleDocTemplate(
        str(target),
        pagesize=(210 * mm, 297 * mm),
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=21 * mm,
        title="REL301m - Website model tương tác",
    ).build(story, onFirstPage=footer, onLaterPages=footer)
    print(target)


if __name__ == "__main__":
    main()
