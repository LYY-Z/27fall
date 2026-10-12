from __future__ import annotations

import sys
from pathlib import Path


TOOL_DIR = Path(__file__).resolve().parent
ROOT = TOOL_DIR.parents[1]
PACKAGES = ROOT / "02_学校提交包"

# Reuse the established recommendation-letter renderer so that the AIRS letters
# share the same typography, margins, footer, letterhead and justification as
# the signed academic-letter PDFs.
sys.path.insert(0, str(TOOL_DIR))
import build_ps_recommendation_pdfs as renderer  # noqa: E402


renderer.LETTER_DATE_EN = "21 September 2026"
renderer.LETTER_DATE_ZH = "2026年9月21日"


def main() -> None:
    renderer.register_fonts()
    generated = 0
    for package in sorted(PACKAGES.iterdir()):
        if not package.is_dir() or package.name == "00_通用CV":
            continue
        source_dir = package / "03_推荐信"
        output_dir = source_dir / "最终版"
        output_dir.mkdir(parents=True, exist_ok=True)
        for source in sorted(source_dir.glob("RL_01_AIRS*.md")):
            output = output_dir / f"{source.stem}.pdf"
            renderer.build_rl(source, output)
            generated += 1
            print(output)
    print(f"Generated {generated} enterprise recommendation PDFs")


if __name__ == "__main__":
    main()
