from pathlib import Path
import re
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, KeepTogether, Image
from reportlab.pdfgen.canvas import Canvas


ROOT = Path(r"F:\27fall\申请材料\00_当前申请")
PACKAGES = ROOT / "02_学校提交包"
GENERATE_PS = False
LETTER_DATE_EN = "21 September 2026"
LETTER_DATE_ZH = "2026年9月21日"
AIRS_HEADER_IMAGE = ROOT / "00_申请总览" / "工具" / "airs_header_crop.png"
SZTU_HEADER_IMAGE = ROOT / "00_申请总览" / "工具" / "SZTU_official_header_white_20260907.png"

EN_FONT = "TimesNewRoman"
EN_BOLD = "TimesNewRoman-Bold"
ZH_FONT = "MicrosoftYaHei"


class CJKJustifiedParagraph(Paragraph):
    """Paragraph renderer that distributes extra width between CJK characters.

    ReportLab's normal TA_JUSTIFY implementation distributes word spaces.  A
    Chinese paragraph has no spaces between its characters, so it otherwise
    remains visually left-aligned even when the style requests justification.
    """

    def drawPara(self, debug=0):
        if getattr(self.blPara, "kind", None) != 0:
            return super().drawPara(debug)

        lines = self.blPara.lines
        if not lines:
            return

        style = self.style
        canvas = self.canv
        left = style.leftIndent + style.firstLineIndent
        available = self.width - style.leftIndent - style.rightIndent
        font_name = getattr(self.blPara, "fontName", style.fontName)
        font_size = getattr(self.blPara, "fontSize", style.fontSize)
        ascent = getattr(self.blPara, "ascent", font_size)
        y = self.height - ascent

        canvas.saveState()
        canvas.setFillColor(style.textColor)
        for index, line in enumerate(lines):
            words = line[1]
            text = "".join(getattr(word, "text", word) for word in words)
            last_line = index == len(lines) - 1
            tx = canvas.beginText(left, y)
            tx.setFont(font_name, font_size, style.leading)
            if not last_line and len(text) > 1:
                text_width = pdfmetrics.stringWidth(text, font_name, font_size)
                tx.setCharSpace(max(0, (available - text_width) / (len(text) - 1)))
            tx.textOut(text)
            canvas.drawText(tx)
            y -= style.leading
        canvas.restoreState()


def register_fonts():
    pdfmetrics.registerFont(TTFont(EN_FONT, r"C:\Windows\Fonts\times.ttf"))
    pdfmetrics.registerFont(TTFont(EN_BOLD, r"C:\Windows\Fonts\timesbd.ttf"))
    pdfmetrics.registerFont(TTFont(ZH_FONT, r"C:\Windows\Fonts\msyh.ttc", subfontIndex=0))


def esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def inline_markup(text: str, chinese: bool = False) -> str:
    # Keep the source wording while making Markdown emphasis render as typography.
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = text.replace("\\*", "*")
    text = esc(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__([^_]+)__", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"(?<!_)_([^_]+)_(?!_)", r"<i>\1</i>", text)
    return text


def read_markdown(path: Path):
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").splitlines()


def parse_document(path: Path):
    lines = read_markdown(path)
    blocks = []
    buf = []
    for raw in lines:
        line = raw.strip()
        if not line:
            if buf:
                blocks.append(("p", " ".join(buf)))
                buf = []
            continue
        if line.startswith("# "):
            if buf:
                blocks.append(("p", " ".join(buf)))
                buf = []
            blocks.append(("title", line[2:].strip()))
            continue
        if line.startswith("## "):
            if buf:
                blocks.append(("p", " ".join(buf)))
                buf = []
            blocks.append(("heading", line[3:].strip()))
            continue
        # The source is prose; preserve bullet lines as their own paragraph if any appear.
        if line.startswith("- "):
            if buf:
                blocks.append(("p", " ".join(buf)))
                buf = []
            blocks.append(("bullet", line[2:].strip()))
            continue
        buf.append(line)
    if buf:
        blocks.append(("p", " ".join(buf)))
    return blocks


def lang_is_zh(path: Path) -> bool:
    return "_ZH" in path.stem or "中文" in path.stem or "_中文对照" in path.stem


def first_title(blocks):
    for kind, text in blocks:
        if kind == "title":
            return text
    return "Personal Statement" if blocks else ""


def add_page_decor(canvas: Canvas, doc, chinese=False, kind="ps"):
    canvas.saveState()
    w, h = A4
    # restrained footer for navigation; no decorative rules under titles.
    canvas.setFont(ZH_FONT if chinese else EN_FONT, 8.2)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    if kind == "ps":
        label = "赖咏怡 | 个人陈述" if chinese else "Yongyi Lai | Personal Statement"
    else:
        label = "赖咏怡 | 推荐信" if chinese else "Yongyi Lai | Recommendation Letter"
    canvas.drawString(22 * mm, 12 * mm, label)
    canvas.drawRightString(w - 22 * mm, 12 * mm, str(doc.page))
    canvas.restoreState()


def styles(chinese=False, kind="ps"):
    font = ZH_FONT if chinese else EN_FONT
    bold = font if chinese else EN_BOLD
    leading = 18.5 if chinese else 15.6
    body_size = 11.1 if chinese else 11.0
    sheet = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "DocTitle", parent=sheet["Title"], fontName=bold, fontSize=15.5 if not chinese else 16,
            leading=20, textColor=colors.HexColor("#111827"), alignment=TA_LEFT,
            spaceAfter=10 * mm, keepWithNext=True,
        ),
        "heading": ParagraphStyle(
            "Heading", parent=sheet["Heading2"], fontName=bold, fontSize=12.5,
            leading=16, textColor=colors.HexColor("#111827"), spaceBefore=4 * mm,
            spaceAfter=2 * mm, keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body", parent=sheet["BodyText"], fontName=font, fontSize=body_size,
            leading=leading, textColor=colors.HexColor("#1F2937"), alignment=TA_JUSTIFY,
            spaceAfter=4.5 * mm, firstLineIndent=0,
            wordWrap="CJK" if chinese else None,
        ),
        "bullet": ParagraphStyle(
            "Bullet", parent=sheet["BodyText"], fontName=font, fontSize=body_size,
            leading=leading, leftIndent=5 * mm, firstLineIndent=-4 * mm,
            textColor=colors.HexColor("#1F2937"), alignment=TA_JUSTIFY, spaceAfter=2.5 * mm,
            wordWrap="CJK" if chinese else None,
        ),
        "meta": ParagraphStyle(
            "Meta", parent=sheet["BodyText"], fontName=font, fontSize=9.8,
            leading=13.5, textColor=colors.HexColor("#4B5563"), spaceAfter=5 * mm,
            wordWrap="CJK" if chinese else None,
        ),
        "letterhead": ParagraphStyle(
            "Letterhead", parent=sheet["BodyText"], fontName=bold, fontSize=10.8,
            leading=14, textColor=colors.HexColor("#111827"), spaceAfter=1.5 * mm,
            wordWrap="CJK" if chinese else None,
        ),
    }


def build_ps(src: Path, out: Path):
    chinese = lang_is_zh(src)
    st = styles(chinese, "ps")
    blocks = parse_document(src)
    doc = BaseDocTemplate(
        str(out), pagesize=A4, leftMargin=22 * mm, rightMargin=22 * mm,
        topMargin=21 * mm, bottomMargin=21 * mm, title=first_title(blocks),
        author="Yongyi Lai",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin + 5 * mm, doc.width,
                  doc.height - 5 * mm, id="normal", leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="ps", frames=[frame],
                                       onPage=lambda c, d: add_page_decor(c, d, chinese, "ps"))])
    story = []
    title_seen = False
    for kind, text in blocks:
        if kind == "title" and not title_seen:
            story.append(Paragraph(inline_markup(text, chinese), st["title"]))
            title_seen = True
        elif kind == "heading":
            story.append(Paragraph(inline_markup(text, chinese), st["heading"]))
        elif kind == "bullet":
            story.append(Paragraph("• " + inline_markup(text, chinese), st["bullet"]))
        else:
            body_cls = CJKJustifiedParagraph if chinese else Paragraph
            story.append(body_cls(inline_markup(text, chinese), st["body"]))
    doc.build(story)


def parse_recommendation(path: Path):
    """Parse letter blocks while preserving the conventional signature block."""
    chinese = lang_is_zh(path)
    lines = read_markdown(path)
    title = ""
    blocks = []
    paragraphs = []
    in_signature = False

    def flush_paragraph():
        nonlocal paragraphs
        if paragraphs:
            blocks.append(("p", " ".join(paragraphs)))
            paragraphs = []

    for raw in lines:
        line = raw.strip()
        if not line:
            flush_paragraph()
            continue
        if line.startswith("# "):
            flush_paragraph()
            title = line[2:].strip()
            continue
        if in_signature:
            blocks.append(("signature", line))
            continue
        # Institution-letterhead placeholders are replaced by the actual institution
        # named in the same letter; the referee still supplies the official letterhead.
        if line in {"[AIRS letterhead]", "[研究院信头]", "深圳市人工智能与机器人研究院", "Shenzhen Institute of Artificial Intelligence and Robotics for Society (AIRS)"}:
            flush_paragraph()
            blocks.append(("letterhead", "深圳市人工智能与机器人研究院（AIRS）" if chinese else "Shenzhen Institute of Artificial Intelligence and Robotics for Society (AIRS)"))
            continue
        if line in {"[School letterhead]", "[University letterhead]", "[学校信头]", "深圳技术大学", "Shenzhen Technology University"}:
            flush_paragraph()
            blocks.append(("letterhead", "深圳技术大学" if chinese else "Shenzhen Technology University"))
            continue
        if line in {"[Date]", "[日期]"} or line.startswith("Date: ") or line.startswith("日期："):
            flush_paragraph()
            blocks.append(("date", f"日期：{LETTER_DATE_ZH}" if chinese else f"Date: {LETTER_DATE_EN}"))
            continue
        if line in {"Sincerely,", "Yours sincerely,", "此致"}:
            flush_paragraph()
            blocks.append(("signoff", line))
            in_signature = True
            continue
        # The Chinese source keeps the salutation and the first sentence adjacent.
        # Split them so the letter reads as a formal letter in the rendered version.
        if chinese and line.startswith("尊敬的招生委员会各位委员："):
            flush_paragraph()
            blocks.append(("salutation", "尊敬的招生委员会各位委员："))
            rest = line[len("尊敬的招生委员会各位委员："):].strip()
            if rest:
                paragraphs.append(rest)
            continue
        if not chinese and line.startswith("Dear "):
            flush_paragraph()
            blocks.append(("salutation", line))
            continue
        paragraphs.append(line)
    flush_paragraph()
    return title, blocks


def build_rl(src: Path, out: Path):
    chinese = lang_is_zh(src)
    st = styles(chinese, "rl")
    title, blocks = parse_recommendation(src)
    doc = BaseDocTemplate(
        str(out), pagesize=A4, leftMargin=23 * mm, rightMargin=23 * mm,
        topMargin=20 * mm, bottomMargin=21 * mm,
        title=title or "Recommendation Letter", author="Yongyi Lai",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin + 5 * mm, doc.width,
                  doc.height - 5 * mm, id="normal", leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="rl", frames=[frame],
                                       onPage=lambda c, d: add_page_decor(c, d, chinese, "rl"))])
    story = []
    # Use source-derived institutional headers where available. These are headers only;
    # no signature, seal, referee approval, or official submission status is fabricated.
    use_airs_header = "AIRS" in src.name and AIRS_HEADER_IMAGE.exists()
    use_sztu_header = "Academic" in src.name and SZTU_HEADER_IMAGE.exists()
    header_image = AIRS_HEADER_IMAGE if use_airs_header else SZTU_HEADER_IMAGE if use_sztu_header else None
    if header_image is not None:
        # ReportLab otherwise treats raster pixel dimensions as points. Set the
        # height explicitly to preserve the original header aspect ratio.
        aspect_ratio = (200 / 1105) if use_airs_header else (160 / 715)
        header = Image(str(header_image), width=doc.width, height=doc.width * aspect_ratio)
        header.hAlign = "LEFT"
        story.append(header)
        story.append(Spacer(1, 5 * mm))
    # Formal letter layout: keep the recommender’s text unchanged, apply hierarchy only.
    story.append(Paragraph(inline_markup(title or ("推荐信" if chinese else "Recommendation Letter"), chinese), st["title"]))
    for kind, text in blocks:
        if kind == "letterhead":
            if header_image is not None:
                continue
            story.append(Paragraph(inline_markup(text, chinese), st["letterhead"]))
            continue
        if kind == "date":
            story.append(Paragraph(inline_markup(text, chinese), st["meta"]))
            story.append(Spacer(1, 2 * mm))
            continue
        if kind == "salutation":
            story.append(Paragraph(inline_markup(text, chinese), st["body"]))
            continue
        if kind == "signoff":
            story.append(Spacer(1, 3 * mm))
            story.append(Paragraph(inline_markup(text, chinese), st["body"]))
            story.append(Spacer(1, 6 * mm))
            continue
        if kind == "signature":
            story.append(Paragraph(inline_markup(text, chinese), st["meta"]))
            continue
        if kind == "p":
            body_cls = CJKJustifiedParagraph if chinese else Paragraph
            story.append(body_cls(inline_markup(text, chinese), st["body"]))
        elif kind == "heading":
            story.append(Paragraph(inline_markup(text, chinese), st["heading"]))
        elif kind == "bullet":
            story.append(Paragraph("• " + inline_markup(text, chinese), st["bullet"]))
    # Signature line is a document feature, not a fabricated signature.
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("推荐人签名：____________________" if chinese else "Referee signature: ____________________", st["meta"]))
    doc.build(story)


def output_path(out_dir: Path, src: Path) -> Path:
    return out_dir / (src.stem + ".pdf")


def main():
    register_fonts()
    count = 0
    for pkg in sorted(PACKAGES.iterdir()):
        if not pkg.is_dir() or pkg.name == "00_通用CV":
            continue
        ps_dir = pkg / "02_PS"
        rl_dir = pkg / "03_推荐信"
        ps_out = ps_dir / "最终PDF_修正版"
        rl_out = rl_dir / "最终PDF_修正版"
        ps_out.mkdir(parents=True, exist_ok=True)
        rl_out.mkdir(parents=True, exist_ok=True)
        if GENERATE_PS:
            for src in sorted(ps_dir.glob("*.md")):
                out = output_path(ps_out, src)
                build_ps(src, out)
                count += 1
        for src in sorted(rl_dir.glob("*.md")):
            rl_out = rl_dir / "最终PDF_信头修正版_2026-09-08_V3"
            rl_out.mkdir(parents=True, exist_ok=True)
            out = output_path(rl_out, src)
            build_rl(src, out)
            count += 1
    print(f"Generated {count} PDFs")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
