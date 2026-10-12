from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(r"F:\27fall\申请材料\00_当前申请")
PACKAGES = ROOT / "02_学校提交包"
COMMON_CV = PACKAGES / "00_通用CV" / "当前提交版"
RENDERER_PATH = ROOT / "00_申请总览" / "工具" / "build_ps_recommendation_pdfs.py"


PROGRAMS = [
    {
        "folder": "08_CUHKShenzhen_CS",
        "label": "港中深计算机科学",
        "base_pkg": "06_CityUDG_CS",
        "base_ps": "PS_06_CityU-DG_MSc_Computer_Science",
        "ps_en": "PS_08_CUHK-SZ_MSc_Computer_Science_EN.md",
        "ps_zh": "PS_08_CUHK-SZ_MSc_Computer_Science_ZH.md",
        "title_en": "# Personal Statement — MSc in Computer Science, The Chinese University of Hong Kong, Shenzhen",
        "title_zh": "# 个人陈述 — 香港中文大学（深圳）计算机科学理学硕士",
        "rl_title_en": "MSc in Computer Science at The Chinese University of Hong Kong, Shenzhen",
        "rl_short_en": "MSc in Computer Science",
        "rl_title_zh": "香港中文大学（深圳）计算机科学理学硕士项目",
        "rl_short_zh": "计算机科学理学硕士",
        "replacement_en": (
            "The MSc in Computer Science is the right next step because it addresses the computing foundations behind the robot systems I have been building. Its core training in algorithms, artificial intelligence, operating systems and parallel programming, together with electives in machine learning, deep learning, reinforcement learning, computer vision and GPU programming, would help me turn practical robot experience into a more systematic understanding of computation and intelligent software. I am particularly interested in applying these methods to robot perception, motion planning and data-driven control.\n\n"
            "After the degree I intend to work in the Greater Bay Area as a robotics algorithm engineer, combining perception, planning and control with learning-based methods. The programme's project and industry-oriented training would let me study the algorithms behind a complete robot system while testing them under real timing and hardware constraints. My previous work has taken control and navigation modules from software design to working robots; this programme would help me make those algorithms more principled, efficient and transferable across platforms."
        ),
        "replacement_zh": (
            "香港中文大学（深圳）计算机科学理学硕士适合作为我的下一步，因为它能够补足我在机器人系统背后所依赖的计算基础。项目在算法、人工智能、操作系统与并行编程方面的核心训练，以及机器学习、深度学习、强化学习、计算机视觉和 GPU 编程等选修内容，可以帮助我把机器人实践转化为对计算与智能软件更系统的理解。我尤其希望将这些方法用于机器人感知、运动规划和数据驱动控制。\n\n"
            "毕业后，我计划在粤港澳大湾区从事机器人算法工程工作，将感知、规划和控制与基于学习的方法结合起来。项目中的课程实践和行业导向训练，可以让我在完整机器人系统的背景下学习算法，并在真实的时序与硬件约束中检验它们。我过去的工作曾把控制与导航模块从软件设计推进到机器人实机运行；该项目将帮助我让这些算法更加有原则、高效，并能够迁移到不同平台。"
        ),
    },
    {
        "folder": "10_CUHK_HK_Robotics",
        "label": "港中文本部 Robotics",
        "base_pkg": "01_PolyU_IRE",
        "base_ps": "PS_01_PolyU_MSc_Intelligent_Robotics_Engineering",
        "ps_en": "PS_10_CUHK_MSc_Robotics_EN.md",
        "ps_zh": "PS_10_CUHK_MSc_Robotics_ZH.md",
        "title_en": "# Personal Statement — MSc in Robotics, The Chinese University of Hong Kong",
        "title_zh": "# 个人陈述 — 香港中文大学机器人理学硕士",
        "rl_title_en": "MSc in Robotics at The Chinese University of Hong Kong",
        "rl_short_en": "MSc in Robotics",
        "rl_title_zh": "香港中文大学机器人理学硕士项目",
        "rl_short_zh": "机器人理学硕士",
        "replacement_en": (
            "The MSc in Robotics at The Chinese University of Hong Kong is the most direct academic continuation of this preparation. Its foundation in robotic systems, experimental robotics and autonomous mobile robots corresponds to the path I have followed from balance control to navigation and manipulation. The programme's coverage of kinematics, dynamics, sensing, control, path planning, robot learning and embodied intelligence would allow me to connect the separate modules I have implemented into a more principled understanding of complete robotic systems. I am also interested in the hands-on and project-based training, because my strongest learning has come from taking an algorithm from a model to a real platform and analysing what changes in that transition.\n\n"
            "My goal is to work as a robotics algorithm engineer in the Greater Bay Area, focusing on motion control, navigation and learning for mobile and legged robots. I would bring practical experience with real-time control, state estimation, planning and embedded execution, while using the programme to strengthen the theoretical and experimental foundations that I still need for advanced robot design."
        ),
        "replacement_zh": (
            "香港中文大学机器人理学硕士是我现有准备最直接的学术延伸。项目在机器人系统、实验机器人与自主移动机器人方面的基础训练，与我从平衡控制走向导航和操作的实践路径相对应；运动学、动力学、感知、控制、路径规划、机器人学习与具身智能等内容，则能够帮助我把已经实现的不同模块连接成对完整机器人系统更有原则性的理解。我也重视项目中的实践和项目训练，因为我最有效的学习方式，正是把算法从模型推进到真实平台，并分析这一过程中发生了什么变化。\n\n"
            "我的目标是在粤港澳大湾区从事机器人算法工程工作，专注于移动与轮腿机器人的运动控制、导航和学习。我可以带来实时控制、状态估计、规划与嵌入式执行方面的实践经验，并通过该项目进一步夯实高级机器人设计所需的理论与实验基础。"
        ),
    },
    {
        "folder": "11_UM_Robotics_and_Autonomous_Systems",
        "label": "澳门大学 Robotics and Autonomous Systems",
        "base_pkg": "01_PolyU_IRE",
        "base_ps": "PS_01_PolyU_MSc_Intelligent_Robotics_Engineering",
        "ps_en": "PS_11_UM_MSc_Robotics_and_Autonomous_Systems_EN.md",
        "ps_zh": "PS_11_UM_MSc_Robotics_and_Autonomous_Systems_ZH.md",
        "title_en": "# Personal Statement — MSc in Robotics and Autonomous Systems, University of Macau",
        "title_zh": "# 个人陈述 — 澳门大学机器人与自主系统理学硕士",
        "rl_title_en": "MSc in Robotics and Autonomous Systems at the University of Macau",
        "rl_short_en": "MSc in Robotics and Autonomous Systems",
        "rl_title_zh": "澳门大学机器人与自主系统理学硕士项目",
        "rl_short_zh": "机器人与自主系统理学硕士",
        "replacement_en": (
            "The MSc in Robotics and Autonomous Systems at the University of Macau fits the breadth of robotics I now want to consolidate. My projects have covered balance control, legged locomotion, localisation, planning, trajectory tracking, manipulation and edge AI, but these experiences were developed on different platforms. A programme that brings together machine vision, sensor fusion, robot pose estimation, SLAM, nonlinear motion estimation and control, and trajectory planning would help me understand the common principles behind these systems. I am particularly interested in the connection between autonomous perception and control: a planner is only useful when the state estimate is trustworthy and the controller can execute the resulting trajectory under physical constraints.\n\n"
            "After graduation I intend to work as a robotics algorithm engineer in the Greater Bay Area, focusing on autonomous navigation and control for mobile, legged and service robots. I would bring practical hardware experience and a habit of validating complete loops, while using the programme to strengthen my mathematical modelling, sensor-fusion and autonomous-system design skills."
        ),
        "replacement_zh": (
            "澳门大学机器人与自主系统理学硕士适合帮助我整合目前较为分散的机器人实践。我的项目覆盖了平衡控制、腿式运动、定位、规划、轨迹跟踪、机器人操作和边缘 AI，但这些经验是在不同平台上逐步形成的。项目将机器视觉、传感器融合、机器人位姿估计、SLAM、非线性运动估计与控制以及轨迹规划放在同一培养框架中，能够帮助我理解这些系统背后的共同原理。我尤其关注自主感知与控制之间的联系：只有状态估计可靠，控制器能够在物理约束下执行，规划器输出的路径才真正有意义。\n\n"
            "毕业后，我计划在粤港澳大湾区从事机器人算法工程工作，专注于移动、轮腿和服务机器人的自主导航与控制。我可以带来真实硬件经验以及对完整闭环进行验证的习惯，并通过该项目进一步提高数学建模、传感器融合与自主系统设计能力。"
        ),
    },
    {
        "folder": "12_UM_AI",
        "label": "澳门大学 Artificial Intelligence",
        "base_pkg": "03_CityUDG_AI",
        "base_ps": "PS_03_CityU-DG_MSc_Artificial_Intelligence",
        "ps_en": "PS_12_UM_MSc_Artificial_Intelligence_EN.md",
        "ps_zh": "PS_12_UM_MSc_Artificial_Intelligence_ZH.md",
        "title_en": "# Personal Statement — MSc in Artificial Intelligence, University of Macau",
        "title_zh": "# 个人陈述 — 澳门大学人工智能理学硕士",
        "rl_title_en": "MSc in Artificial Intelligence at the University of Macau",
        "rl_short_en": "MSc in Artificial Intelligence",
        "rl_title_zh": "澳门大学人工智能理学硕士项目",
        "rl_short_zh": "人工智能理学硕士",
        "replacement_en": (
            "The MSc in Artificial Intelligence at the University of Macau would help me move from practical deployment to a more systematic understanding of AI methods. I have used computer vision, edge inference and an agent decision chain in a working robot-related application, and I have also seen how perception and decision quality affect control and actuation on real hardware. I now want stronger foundations in machine learning, data science, information processing and intelligent systems so that I can evaluate models, understand their limitations and integrate them responsibly into physical systems.\n\n"
            "My goal is to work as a robotics algorithm engineer, combining perception, planning and control with learning-based methods. The programme would complement my existing hands-on experience with a broader AI foundation, while my background would allow me to test learned components against the timing, uncertainty and safety constraints of real robots."
        ),
        "replacement_zh": (
            "澳门大学人工智能理学硕士能够帮助我从实际部署走向对人工智能方法更系统的理解。我曾在一个可运行的机器人相关应用中使用计算机视觉、边缘推理和 Agent 决策链，也在真实硬件上看到感知与决策质量如何影响控制和执行。现在，我希望在机器学习、数据科学、信息处理和智能系统方面建立更扎实的基础，从而能够评估模型、理解其局限，并以更可靠的方式将其集成到物理系统中。\n\n"
            "我的目标是成为机器人算法工程师，将感知、规划和控制与基于学习的方法结合起来。该项目能够为我已有的动手经验补充更完整的人工智能基础，而我的实践背景也使我能够把学习型模块放回真实机器人的时序、不确定性与安全约束中检验。"
        ),
    },
    {
        "folder": "13_MUST_AI",
        "label": "澳门科技大学 Artificial Intelligence",
        "base_pkg": "03_CityUDG_AI",
        "base_ps": "PS_03_CityU-DG_MSc_Artificial_Intelligence",
        "ps_en": "PS_13_MUST_MSc_Artificial_Intelligence_EN.md",
        "ps_zh": "PS_13_MUST_MSc_Artificial_Intelligence_ZH.md",
        "title_en": "# Personal Statement — MSc in Artificial Intelligence, Macau University of Science and Technology",
        "title_zh": "# 个人陈述 — 澳门科技大学人工智能理学硕士",
        "rl_title_en": "MSc in Artificial Intelligence at Macau University of Science and Technology",
        "rl_short_en": "MSc in Artificial Intelligence",
        "rl_title_zh": "澳门科技大学人工智能理学硕士项目",
        "rl_short_zh": "人工智能理学硕士",
        "replacement_en": (
            "The MSc in Artificial Intelligence at the Macau University of Science and Technology is a practical next step for me because it can strengthen the AI foundation behind the robot systems I have already built. My experience includes edge computer vision, an agent-based decision chain and the integration of AI outputs with a physical actuator, but I want to study the principles of learning, data and intelligent information processing systematically. I am particularly interested in AI methods that can support robot perception, decision-making and adaptation while remaining understandable and testable in real engineering systems.\n\n"
            "After the degree I intend to work in the Greater Bay Area as a robotics algorithm engineer, combining my existing control and embedded experience with stronger AI skills. I would bring a practical understanding of how models behave under hardware and timing constraints, and use the programme to become more capable of designing and evaluating the learning components of a complete robot system."
        ),
        "replacement_zh": (
            "澳门科技大学人工智能理学硕士是我现阶段较为务实的下一步，因为它能够为我已经构建的机器人系统补足人工智能基础。我的经历包括边缘计算机视觉、基于 Agent 的决策链，以及把 AI 输出接入真实执行器；但我希望系统学习学习方法、数据方法和智能信息处理的基本原理。我尤其关注能够支持机器人感知、决策和适应能力的人工智能方法，同时保证这些方法在真实工程系统中可理解、可测试。\n\n"
            "毕业后，我计划在粤港澳大湾区从事机器人算法工程工作，将已有的控制与嵌入式经验同更扎实的 AI 能力结合起来。我可以带来对模型在硬件和时序约束下运行方式的实践理解，并通过该项目提高设计和评估完整机器人系统中学习模块的能力。"
        ),
    },
    {
        "folder": "90_待确认_HKUSTGZ_Robotics",
        "label": "港科广具身智能/机器人方向（项目名称待确认）",
        "base_pkg": "01_PolyU_IRE",
        "base_ps": "PS_01_PolyU_MSc_Intelligent_Robotics_Engineering",
        "ps_en": "PS_90_HKUSTGZ_Embodied_Intelligence_Working_EN.md",
        "ps_zh": "PS_90_HKUSTGZ_Embodied_Intelligence_Working_ZH.md",
        "title_en": "# Personal Statement — MSc in Embodied Intelligence (working title), The Hong Kong University of Science and Technology (Guangzhou)",
        "title_zh": "# 个人陈述 — 香港科技大学（广州）具身智能理学硕士（暂用名称）",
        "rl_title_en": "MSc programme in Embodied Intelligence at HKUST(GZ) (programme title pending)",
        "rl_short_en": "MSc programme in Embodied Intelligence at HKUST(GZ) (programme title pending)",
        "rl_title_zh": "香港科技大学（广州）具身智能理学硕士项目（项目名称待确认）",
        "rl_short_zh": "具身智能理学硕士项目（项目名称待确认）",
        "replacement_en": (
            "A robotics and embodied-intelligence programme at HKUST(GZ) would be a strong fit for the next stage of my preparation, provided that the programme is formally opened as a taught master's programme. My experience has moved from balance control and locomotion to navigation, manipulation and edge AI, and I now want to study how perception, planning, control and learning can be designed as one embodied system. The opportunity to connect mathematical modelling with machine learning, physical interaction and robot-system validation is especially relevant to my goal of developing algorithms that remain reliable outside simulation.\n\n"
            "My goal is to work as a robotics algorithm engineer in the Greater Bay Area, focusing on control, navigation and learning for mobile, legged and humanoid platforms. I would bring experience with real-time control, state estimation, motion planning, embedded execution and hardware validation. Once the programme title, curriculum and application requirements are officially confirmed, I will update this working statement to match the final programme precisely."
        ),
        "replacement_zh": (
            "如果港科大（广州）正式开设具身智能或机器人方向的授课型硕士项目，它将非常契合我下一阶段的准备方向。我的实践经历已经从平衡控制和腿式运动，延伸到导航、机器人操作与边缘 AI；下一步，我希望系统学习如何把感知、规划、控制和学习设计成一个能够在真实环境中工作的具身系统。将数学建模与机器学习、物理交互和机器人系统验证结合起来，正好对应我希望发展的能力：让算法离开仿真后仍然能够稳定运行。\n\n"
            "我的目标是在粤港澳大湾区从事机器人算法工程工作，专注于移动、轮腿和人形机器人平台的控制、导航与学习。我可以带来实时控制、状态估计、运动规划、嵌入式执行与实机验证方面的经验。待项目名称、课程体系和申请要求正式公布后，我会再据此逐项更新本工作版文书，使其与最终项目完全一致。"
        ),
        "pending": True,
    },
]


def copy_cv(dst: Path) -> None:
    cv_dir = dst / "01_CV"
    cv_dir.mkdir(parents=True, exist_ok=True)
    for name in ("CV_Robotics_Algorithms_Final_EN.pdf", "CV_Robotics_Algorithms_Final_ZH.pdf"):
        shutil.copy2(COMMON_CV / name, cv_dir / name)


def replace_ps_tail(text: str, title: str, replacement: str) -> str:
    parts = text.replace("\r\n", "\n").split("\n\n")
    parts[0] = title
    # The current PS templates end with two programme-specific paragraphs.
    parts = parts[:-2] + replacement.split("\n\n")
    return "\n\n".join(parts).rstrip() + "\n"


def write_ps(program: dict, dst: Path) -> None:
    base = PACKAGES / program["base_pkg"] / "02_PS"
    src_en = base / f"{program['base_ps']}_EN.md"
    src_zh = base / f"{program['base_ps']}_ZH.md"
    out = dst / "02_PS"
    out.mkdir(parents=True, exist_ok=True)
    en = replace_ps_tail(src_en.read_text(encoding="utf-8-sig"), program["title_en"], program["replacement_en"])
    zh = replace_ps_tail(src_zh.read_text(encoding="utf-8-sig"), program["title_zh"], program["replacement_zh"])
    # Replace the one programme-specific sentence retained from each base template.
    body_replacements = {
        "10_CUHK_HK_Robotics": (
            ("That is why I am applying to the MSc in Intelligent Robotics Engineering.", "That is why I am applying to the MSc in Robotics at The Chinese University of Hong Kong."),
            ("这就是我申请智能机器人工程理学硕士的原因。", "这就是我申请香港中文大学机器人理学硕士的原因。"),
        ),
        "11_UM_Robotics_and_Autonomous_Systems": (
            ("That is why I am applying to the MSc in Intelligent Robotics Engineering.", "That is why I am applying to the MSc in Robotics and Autonomous Systems at the University of Macau."),
            ("这就是我申请智能机器人工程理学硕士的原因。", "这就是我申请澳门大学机器人与自主系统理学硕士的原因。"),
        ),
        "90_待确认_HKUSTGZ_Robotics": (
            ("That is why I am applying to the MSc in Intelligent Robotics Engineering.", "That is why I am preparing an application for the robotics and embodied-intelligence taught master's programme at HKUST(GZ), subject to the official programme announcement."),
            ("这就是我申请智能机器人工程理学硕士的原因。", "因此，我正在为港科大（广州）机器人或具身智能方向的授课型硕士项目准备材料，具体名称以学校正式公告为准。"),
        ),
    }
    if program["folder"] in body_replacements:
        en_old, zh_old = body_replacements[program["folder"]]
        en = en.replace(*en_old)
        zh = zh.replace(*zh_old)
    # The PolyU Chinese template contains an extra heading and course-specific
    # paragraph.  Remove that old section so the new robotics PS remains
    # paragraph-for-paragraph aligned with its English counterpart.
    if program["folder"] in {"10_CUHK_HK_Robotics", "11_UM_Robotics_and_Autonomous_Systems", "90_待确认_HKUSTGZ_Robotics"}:
        marker = "\n\n这些经历与项目的核心课程直接对应。"
        if marker in zh:
            zh = zh.split(marker, 1)[0] + "\n\n" + program["replacement_zh"] + "\n"
    (out / program["ps_en"]).write_bytes(en.encode("utf-8"))
    (out / program["ps_zh"]).write_bytes(zh.encode("utf-8"))


def replace_target(text: str, program: dict) -> str:
    replacements = {
        "MSc in Computer Science at City University of Hong Kong (Dongguan)": program["rl_title_en"],
        "MSc in Computer Science, City University of Hong Kong (Dongguan)": program["rl_title_en"],
        "MSc in Artificial Intelligence at City University of Hong Kong (Dongguan)": program["rl_title_en"],
        "MSc in Artificial Intelligence, City University of Hong Kong (Dongguan)": program["rl_title_en"],
        "MSc in Artificial Intelligence and Robotics at The Chinese University of Hong Kong, Shenzhen": program["rl_title_en"],
        "MSc in Artificial Intelligence and Robotics at The Chinese University of Hong Kong, Shenzhen": program["rl_title_en"],
        "MSc in Intelligent Robotics Engineering at The Hong Kong Polytechnic University": program["rl_title_en"],
        "MSc in Intelligent Robotics Engineering": program["rl_short_en"],
        "MSc in Artificial Intelligence and Robotics": program["rl_short_en"],
        "MSc in Computer Science": program["rl_short_en"],
        "MSc in Artificial Intelligence": program["rl_short_en"],
        "香港中文大学（深圳）人工智能与机器人理学硕士项目": program["rl_title_zh"],
        "人工智能与机器人理学硕士": program["rl_short_zh"],
        "香港城市大学（东莞）计算机科学理学硕士": program["rl_title_zh"],
        "计算机科学理学硕士": program["rl_short_zh"],
        "香港城市大学（东莞）人工智能理学硕士": program["rl_title_zh"],
        "人工智能理学硕士": program["rl_short_zh"],
        "香港理工大学智能机器人工程理学硕士": program["rl_title_zh"],
        "智能机器人工程理学硕士": program["rl_short_zh"],
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # The generic AI replacement can otherwise re-match the prefix of
    # "Artificial Intelligence for Science"; normalise that specific title.
    text = text.replace(
        "MSc in Artificial Intelligence for Science for Science",
        "MSc in Artificial Intelligence for Science",
    )
    text = text.replace("项目项目", "项目")
    return text


def write_recommendations(program: dict, dst: Path) -> None:
    base = PACKAGES / program["base_pkg"] / "03_推荐信"
    out = dst / "03_推荐信"
    out.mkdir(parents=True, exist_ok=True)
    for prefix in ("RL_01_AIRS", "RL_02_Academic"):
        for lang in ("EN", "ZH"):
            source = next(base.glob(f"{prefix}_*_{lang}.md"))
            target = out / f"{prefix}_{program['folder']}_{lang}.md"
            text = replace_target(source.read_text(encoding="utf-8-sig"), program)
            target.write_bytes(text.encode("utf-8"))


def write_readme(program: dict, dst: Path) -> None:
    readme = f"""# {program['label']}提交包\n\n本目录包含当前通用 CV、该项目专属个人陈述，以及 AIRS 企业推荐信和深圳技术大学学术推荐信的中英文版本。\n\n- `01_CV/`：当前通用 CV；\n- `02_PS/`：该项目专属 PS 的英文主稿与中文对照；\n- `03_推荐信/`：两位推荐人的英文稿与中文对照。\n\n英文材料用于正式提交；中文材料用于申请人和推荐人核对。推荐信提交前须由推荐人确认事实、项目名称、日期、信头和签名，并按申请系统要求由推荐人在线提交或确认。\n\n项目名称按截至 2026 年 9 月 21 日可查到的官方名称整理；若申请系统显示名称、批次或材料要求不同，以系统当轮页面为准。\n"""
    if program.get("pending"):
        readme += "\n## 待确认事项\n\n这是工作版材料，不是最终上传版。项目正式名称、学费、学制、课程、申请费、截止时间、推荐信要求和是否面试均需等待学校正式申请入口确认；确认后应逐项替换标题和项目匹配段落。\n"
    (dst / "README.md").write_bytes(readme.encode("utf-8"))
    (dst / "00_提交包说明.md").write_bytes(readme.encode("utf-8"))


def main() -> None:
    for p in PROGRAMS:
        dst = PACKAGES / p["folder"]
        dst.mkdir(parents=True, exist_ok=True)
        copy_cv(dst)
        write_ps(p, dst)
        write_recommendations(p, dst)
        write_readme(p, dst)
        print(dst)


if __name__ == "__main__":
    main()
