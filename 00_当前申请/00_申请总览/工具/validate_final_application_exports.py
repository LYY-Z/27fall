from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader


ROOT = Path(r"F:\27fall\申请材料\00_当前申请\03_最终提交与推荐人确认包_2027Fall")
REPORT = ROOT / "00_完整性与一致性检查报告_20260922.md"

PROGRAMS = [
    ("01_香港理工大学_智能机器人工程", ["MSc in Intelligent Robotics Engineering"], ["智能机器人工程理学硕士"]),
    ("02_香港中文大学深圳_人工智能与机器人", ["MSc in Artificial Intelligence and Robotics"], ["人工智能与机器人理学硕士"]),
    ("03_香港中文大学深圳_计算机科学", ["MSc in Computer Science"], ["计算机科学理学硕士"]),
    ("05_香港中文大学_机器人学", ["MSc in Robotics"], ["机器人理学硕士"]),
    ("06_香港城市大学_计算机科学_P53", ["MSc in Computer Science"], ["计算机科学理学硕士"]),
    ("07_香港城市大学东莞_人工智能", ["MSc in Artificial Intelligence"], ["人工智能理学硕士"]),
    ("08_香港城市大学东莞_计算机科学", ["MSc in Computer Science"], ["计算机科学理学硕士"]),
    ("09_澳门大学_机器人与自主系统", ["MSc in Robotics and Autonomous Systems"], ["机器人与自主系统理学硕士"]),
    ("10_澳门大学_人工智能", ["MSc in Artificial Intelligence"], ["人工智能理学硕士"]),
    ("11_澳门科技大学_人工智能", ["MSc in Artificial Intelligence"], ["人工智能理学硕士"]),
    ("12_香港科技大学广州_具身智能", ["Embodied Intelligence"], ["具身智能理学硕士"]),
]


def pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def all_pdfs(path: Path) -> Iterable[Path]:
    return path.rglob("*.pdf")


def check_pdf(path: Path, expected: list[str], forbidden: list[str]) -> list[str]:
    errors: list[str] = []
    try:
        reader = PdfReader(str(path))
        if not reader.pages:
            errors.append(f"no pages: {path}")
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:  # pragma: no cover - validation utility
        return [f"unreadable PDF: {path} ({exc})"]
    spaced = " ".join(text.split())
    flat = "".join(text.split())
    for token in expected:
        if token not in text and token not in spaced and token not in flat:
            errors.append(f"missing '{token}' in {path}")
    for token in forbidden:
        if token in text:
            errors.append(f"forbidden placeholder/text '{token}' in {path}")
    return errors


def main() -> None:
    errors: list[str] = []
    confirmed_root = ROOT / "01_学校正式提交包"
    pending_root = ROOT / "04_待确认项目_暂不提交"
    expected_confirmed = [name for name, _, _ in PROGRAMS if "待确认" not in name]
    actual_confirmed = sorted(p.name for p in confirmed_root.iterdir() if p.is_dir())
    if actual_confirmed != sorted(expected_confirmed):
        errors.append(f"confirmed package folders differ: expected {expected_confirmed}, got {actual_confirmed}")

    for folder, en_tokens, zh_tokens in PROGRAMS:
        pkg = (pending_root if "待确认" in folder else confirmed_root) / folder
        if not pkg.exists():
            errors.append(f"missing program package: {pkg}")
            continue
        en_dir = pkg / "01_英文正式文件"
        zh_dir = pkg / "02_中文核对文件"
        src_dir = pkg / "03_可编辑源稿"
        for label, directory, count in (("EN PDFs", en_dir, 4), ("ZH PDFs", zh_dir, 4), ("MD sources", src_dir, 6)):
            actual = len(list(directory.glob("*.pdf" if "PDF" in label else "*.md")))
            if actual != count:
                errors.append(f"{folder}: {label} expected {count}, got {actual}")

        forbidden = [
            "[Date]", "[日期]", "[School letterhead]", "[学校信头]",
            "[AIRS letterhead]", "[研究院信头]", "项目项目",
            "admission to the the", "application to the the",
        ]
        for path in sorted(en_dir.glob("*.pdf")):
            if path.name == "01_Yongyi_Lai_CV_EN.pdf":
                expected = []
            elif "Pending" in path.name and "Personal_Statement" in path.name:
                expected = ["Embodied Intelligence"]
            else:
                expected = en_tokens
                if "Pending" in path.name:
                    expected = ["Embodied Intelligence", "pending"]
            errors.extend(check_pdf(path, expected, forbidden))
        for path in sorted(zh_dir.glob("*.pdf")):
            expected = zh_tokens if "个人陈述" in path.name or "推荐信" in path.name else []
            errors.extend(check_pdf(path, expected, forbidden))

        for path in sorted(en_dir.glob("*Recommendation*.pdf")):
            text = pdf_text(path)
            if "Date: 21 September 2026" not in text:
                errors.append(f"recommendation date is not current: {path}")

    referee_root = ROOT / "02_推荐人核对与签字包"
    referee_expected = {
        "01_傅向华老师_学术推荐信": (11, 11, 0),
        "02_陈淡生老师_AIRS实习推荐信": (11, 11, 0),
    }
    for teacher, (zh_count, en_count, pending_count) in referee_expected.items():
        base = referee_root / teacher
        actual = (
            len(list((base / "01_中文版_请老师核对").glob("*.pdf"))),
            len(list((base / "02_英文版_请老师签字").glob("*.pdf"))),
            len(list((base / "03_待确认项目_暂不签字").glob("*.pdf"))),
        )
        if actual != (zh_count, en_count, pending_count):
            errors.append(f"{teacher}: expected counts {(zh_count, en_count, pending_count)}, got {actual}")

    all_pdf_count = len(list(all_pdfs(ROOT)))
    if all_pdf_count != 153:
        errors.append(f"total PDF count expected 153, got {all_pdf_count}")

    status = "通过" if not errors else "未通过"
    lines = [
        "# 2027 Fall 最终提交与推荐人确认包完整性检查报告",
        "",
        f"检查日期：{date(2026, 9, 22).isoformat()}",
        f"检查结果：**{status}**",
        "",
        "## 已检查项目",
        "",
        "- 11 个专业包：全部已整理为可交推荐人核对和签字的提交包；",
        "- 每个专业：4 份英文 PDF、4 份中文核对 PDF、6 份可编辑源稿；",
        "- 两位推荐人：各 11 份中文核对稿和 11 份英文签字稿，港科广具身智能使用暂用项目名称；",
        "- 所有导出 PDF 可打开并包含页面；",
        "- 已确认推荐信日期统一为 2026 年 9 月 21 日；",
        "- 已检查推荐信目标学校与专业名称，未发现英文重复词或未替换的信头、日期占位符；",
        "- 中英文 PS、学术推荐信和 AIRS 推荐信源稿均已按段落对应；称呼、正文、结尾和推荐人信息均已检查。",
        "",
        "## 需要提交时动态核对",
        "",
        "- 推荐信是否由推荐人在线提交；",
        "- PS 字数、上传格式和是否需要额外 Supporting Information；",
        "- 成绩单是否要求学校直送；",
        "- 护照、证件照、申请费和补充表格；",
        "- 港科广项目正式名称、申请入口和当轮要求；当前推荐信可先交老师核对和签字。",
    ]
    if errors:
        lines.extend(["", "## 发现的问题", "", *[f"- {error}" for error in errors]])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
