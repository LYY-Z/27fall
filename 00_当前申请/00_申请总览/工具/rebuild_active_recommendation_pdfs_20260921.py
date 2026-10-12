from pathlib import Path
import sys


TOOL_DIR = Path(__file__).resolve().parent
ROOT = TOOL_DIR.parents[1]
PACKAGES = ROOT / "02_学校提交包"

ACTIVE_PACKAGES = (
    "01_PolyU_IRE",
    "02_CUHKShenzhen_MAIR",
    "03_CityUDG_AI",
    "06_CityUDG_CS",
    "07_CityUHK_P53_CS",
    "08_CUHKShenzhen_CS",
    "10_CUHK_HK_Robotics",
    "11_UM_Robotics_and_Autonomous_Systems",
    "12_UM_AI",
    "13_MUST_AI",
    "12_HKUSTGZ_Embodied_Intelligence",
)

sys.path.insert(0, str(TOOL_DIR))
import build_ps_recommendation_pdfs as renderer  # noqa: E402


renderer.LETTER_DATE_EN = "21 September 2026"
renderer.LETTER_DATE_ZH = "2026年9月21日"


def main() -> None:
    renderer.register_fonts()
    generated = 0
    for package_name in ACTIVE_PACKAGES:
        source_dir = PACKAGES / package_name / "03_推荐信"
        output_dir = source_dir / "最终版"
        output_dir.mkdir(parents=True, exist_ok=True)
        sources = sorted(source_dir.glob("RL_*.md"))
        if len(sources) != 4:
            raise RuntimeError(
                f"{package_name}: expected four recommendation sources, found {len(sources)}"
            )
        for source in sources:
            output = output_dir / f"{source.stem}.pdf"
            renderer.build_rl(source, output)
            generated += 1
            print(output)
    if generated != 44:
        raise RuntimeError(f"Expected 44 recommendation PDFs, generated {generated}")
    print(f"Generated {generated} recommendation PDFs dated 21 September 2026")


if __name__ == "__main__":
    main()
