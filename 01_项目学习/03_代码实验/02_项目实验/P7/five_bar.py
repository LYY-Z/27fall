"""离线五连杆教学例子。几何长度与课程第五课一致，单位统一为米。"""
import argparse
import csv
from pathlib import Path

import numpy as np

# 第五课 MATLAB 的 L1..L5: 150, 250, 250, 150, 108 mm，转换成 m。
LENGTHS = np.array([0.150, 0.250, 0.250, 0.150, 0.108], dtype=float)


def five_bar_fk(q_left, q_right, lengths=LENGTHS, branch=1):
    """输入两主动关节角(rad)，输出闭链交点 B 的平面坐标(m)。

    branch=+1/-1 表示两圆的两个交点。此处按圆交点写成教学代码，
    和课程 MATLAB 的代数分支选择有相同几何约束，但不保证逐行实现相同。
    """
    lengths = np.asarray(lengths, dtype=float)
    if lengths.shape != (5,) or not np.all(np.isfinite(lengths)) or np.any(lengths <= 0):
        raise ValueError("lengths must be five positive finite values in meters")
    if branch not in (-1, 1):
        raise ValueError("branch must be +1 or -1")
    if not np.all(np.isfinite([q_left, q_right])):
        raise ValueError("joint angles must be finite radians")

    l1, l2, l3, l4, l5 = lengths
    O = np.array([0.0, 0.0])
    D = np.array([l5, 0.0])
    A = O + l1 * np.array([np.cos(q_left), np.sin(q_left)])
    C = D + l4 * np.array([np.cos(q_right), np.sin(q_right)])

    center_delta = C - A
    distance = np.linalg.norm(center_delta)
    if distance < 1e-12:
        raise ValueError("circle centers coincide; the intersection is not unique")
    if distance > l2 + l3 or distance < abs(l2 - l3):
        raise ValueError("the two passive-link circles do not intersect")

    # A 到两圆交点连线在 AC 方向上的距离。
    along = (l2**2 - l3**2 + distance**2) / (2.0 * distance)
    height_squared = l2**2 - along**2
    if height_squared < -1e-12:
        raise ValueError("negative circle-intersection discriminant")

    unit = center_delta / distance
    perpendicular = np.array([-unit[1], unit[0]])
    return A + along * unit + branch * np.sqrt(max(0.0, height_squared)) * perpendicular


def virtual_leg(point, base_span):
    """以两固定轴中点为参考点，返回教学虚拟腿长度(m)与方向角(rad)。"""
    point = np.asarray(point, dtype=float)
    if point.shape != (2,) or not np.all(np.isfinite(point)):
        raise ValueError("point must contain two finite coordinates")
    if not np.isfinite(base_span) or base_span <= 0:
        raise ValueError("base_span must be positive and finite")
    relative = point - np.array([base_span / 2.0, 0.0])
    length = np.linalg.norm(relative)
    if length < 1e-10:
        raise ValueError("virtual-leg length is too small")
    return float(length), float(np.arctan2(relative[1], relative[0]))


def five_bar_jacobian(q, lengths=LENGTHS, branch=1, step=1e-6):
    """用中心差分近似当前姿态的 2x2 关节角到输出点位置雅可比。"""
    q = np.asarray(q, dtype=float)
    if q.shape != (2,) or not np.all(np.isfinite(q)):
        raise ValueError("q must contain two finite joint angles in radians")
    if not np.isfinite(step) or step <= 0:
        raise ValueError("step must be positive and finite")
    columns = []
    for index in range(2):
        offset = np.zeros(2)
        offset[index] = step
        plus = five_bar_fk(*(q + offset), lengths=lengths, branch=branch)
        minus = five_bar_fk(*(q - offset), lengths=lengths, branch=branch)
        columns.append((plus - minus) / (2.0 * step))
    return np.column_stack(columns)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    q = np.array([np.pi / 2.0, np.pi / 2.0])
    with (args.out_dir / "geometry.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "branch", "point_x_m", "point_y_m", "virtual_length_m",
            "virtual_angle_rad", "left_link_residual_m",
            "right_link_residual_m", "smallest_singular_value_m_per_rad",
        ])
        for branch in (-1, 1):
            point = five_bar_fk(*q, branch=branch)
            length, angle = virtual_leg(point, LENGTHS[4])
            A = LENGTHS[0] * np.array([np.cos(q[0]), np.sin(q[0])])
            C = np.array([LENGTHS[4], 0.0]) + LENGTHS[3] * np.array([np.cos(q[1]), np.sin(q[1])])
            jacobian = five_bar_jacobian(q, branch=branch)
            sigma_min = np.linalg.svd(jacobian, compute_uv=False)[-1]
            writer.writerow([
                branch, point[0], point[1], length, angle,
                np.linalg.norm(point - A) - LENGTHS[1],
                np.linalg.norm(point - C) - LENGTHS[2],
                sigma_min,
            ])
    print(args.out_dir / "geometry.csv")


if __name__ == "__main__":
    main()
