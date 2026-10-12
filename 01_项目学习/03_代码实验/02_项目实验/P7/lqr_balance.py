"""按课程第八课建立的四状态、单输入连续 LQR 离线教学脚本。

本脚本是学习用重建，不是课程固件，也没有运行或硬件验证。
"""
import argparse
import csv
from pathlib import Path

import numpy as np
from scipy.linalg import solve_continuous_are


def build_model(m=6.25, h=0.2156, I=None, g=9.8, r=0.07, M=3.7):
    """由课程中的两条耦合方程构造四状态连续模型。

    状态次序 z=[theta, theta_dot, x, x_dot]。
    返回物理方程消元得到的 A、B，以及课程文件当前 B 写法供比较。
    """
    if I is None:
        I = m * h**2
    values = np.array([m, h, I, g, r, M], dtype=float)
    if not np.all(np.isfinite(values)) or np.any(values <= 0):
        raise ValueError("model parameters must be positive and finite")

    delta = (M + m) * (I + m * h**2) - (m * h) ** 2
    if delta <= 0:
        raise ValueError("invalid inertia matrix determinant")

    A = np.array([
        [0.0, 1.0, 0.0, 0.0],
        [(M + m) * m * g * h / delta, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
        [-m**2 * h**2 * g / delta, 0.0, 0.0, 0.0],
    ])

    # 由耦合方程直接消元得到的力矩输入列。
    B_from_equations = np.array([
        [0.0],
        [-m * h / (delta * r)],
        [0.0],
        [(I + m * h**2) / (delta * r)],
    ])

    # wheel_control.m 文件中 B 的第四项，单独保留用于审阅差异。
    source_b4 = 1.0 / ((M + m) * r) - (m**2 * h**2) / ((M + m) * delta * r)
    B_as_written = B_from_equations.copy()
    B_as_written[3, 0] = source_b4
    return A, B_from_equations, B_as_written, delta


def design_lqr(A, B, Q=None, R=None):
    """解连续代数 Riccati 方程，返回 P 和 K，使输入 u=-Kz。"""
    if Q is None:
        Q = np.diag([1.0, 1.0, 1.0, 1.0])
    if R is None:
        R = np.array([[1.0]])
    P = solve_continuous_are(A, B, Q, R)
    K = np.linalg.solve(R, B.T @ P)
    return P, K


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--duration", type=float, default=3.0)
    parser.add_argument("--dt", type=float, default=0.001)
    args = parser.parse_args()
    if args.duration <= 0 or args.dt <= 0:
        raise ValueError("duration and dt must be positive")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    A, B, B_as_written, delta = build_model()
    Q = np.diag([1.0, 1.0, 1.0, 1.0])
    R = np.array([[1.0]])
    P, K = design_lqr(A, B, Q, R)

    with (args.out_dir / "model_coefficients.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["quantity", "row", "column", "equation_derived", "course_file_as_written"])
        writer.writerow(["Delta", "-", "-", delta, delta])
        for row in range(4):
            writer.writerow(["B", row, 0, B[row, 0], B_as_written[row, 0]])

    # 小角度线性模型的离线欧拉演示；不含电机限幅、延迟或硬件动力学。
    state = np.array([0.05, 0.0, 0.0, 0.0])
    sample_count = int(np.ceil(args.duration / args.dt))
    with (args.out_dir / "trajectory.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time_s", "theta_rad", "theta_rate_rad_s", "x_m", "x_rate_m_s", "tau_model_Nm"])
        for index in range(sample_count):
            time = index * args.dt
            tau = float((-K @ state)[0])
            writer.writerow([time, *state, tau])
            derivative = A @ state + B[:, 0] * tau
            state = state + args.dt * derivative

    print(args.out_dir)


if __name__ == "__main__":
    main()
