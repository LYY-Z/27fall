"""闭链腿端虚功关系的离线教学核对。单位采用米、N、N·m。"""
import argparse
import csv
from pathlib import Path

import numpy as np

from five_bar import LENGTHS, five_bar_fk, five_bar_jacobian, virtual_leg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    q = np.array([1.4, 1.7])
    point = five_bar_fk(*q, lengths=LENGTHS, branch=1)
    length, angle = virtual_leg(point, LENGTHS[4])
    relative = point - np.array([LENGTHS[4] / 2.0, 0.0])

    # 将笛卡尔速度换成虚拟腿长速度和方向角速度。
    polar_jacobian = np.array([
        [relative[0] / length, relative[1] / length],
        [-relative[1] / length**2, relative[0] / length**2],
    ])
    task_jacobian = polar_jacobian @ five_bar_jacobian(q, lengths=LENGTHS, branch=1)

    # 广义力分别对应腿长方向力 F(N) 和腿角方向力矩 T(N·m)。
    task_force = np.array([20.0, 2.0])
    joint_rate = np.array([0.2, 0.1])
    joint_torque = task_jacobian.T @ task_force
    task_rate = task_jacobian @ joint_rate

    task_power = float(task_force @ task_rate)
    joint_power = float(joint_torque @ joint_rate)
    with (args.out_dir / "virtual_work.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "leg_length_m", "leg_angle_rad",
            "joint1_torque_Nm", "joint2_torque_Nm",
            "length_rate_m_s", "angle_rate_rad_s",
            "task_power_W", "joint_power_W", "difference_W",
        ])
        writer.writerow([
            length, angle, *joint_torque, *task_rate,
            task_power, joint_power, task_power - joint_power,
        ])
    print(args.out_dir / "virtual_work.csv")


if __name__ == "__main__":
    main()
