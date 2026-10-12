#!/usr/bin/env python3
"""Four-state AIRS-style ballbot LQR lab.

This is an offline, single-plane teaching simulation. It never imports ROS,
opens hardware, or writes to the original project configuration. Model values
are copied from the checked source snapshot and are not claimed to be measured
or validated physical properties.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import platform
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy
from scipy.linalg import solve_continuous_are, solve_discrete_are
from scipy.signal import cont2discrete


# Snapshot copied from chassis_controller/config/model_params.yaml.
# These are source-configuration values, not independent measurements.
MODEL_PARAMS = {
    "wheel_mass_kg": 2.9,
    "ball_radius_m": 0.11,
    "wheel_inertia_kgm2": 0.014036,
    "body_mass_kg": 18.0214,
    "com_height_m": 0.3784,
    "body_pitch_inertia_x_kgm2": 4.1115,
    "gravity_mps2": 9.81,
}
MODEL_PARAMS_SOURCE = (
    "AIRS/Robot/chassis_controller/config/model_params.yaml "
    "(source snapshot; physical calibration not independently verified)"
)

# Candidate weights copied from lqr_params.yaml. The runtime source script
# later hand-scales some gains; this lab deliberately uses the unscaled LQR K.
Q_SOURCE_DIAGONAL = np.array([200.0, 25.0, 800.0, 8.0])
RU_SOURCE = 0.5
Q_SOURCE = np.diag(Q_SOURCE_DIAGONAL)
R_SOURCE = np.array([[RU_SOURCE]])

STATE_NAMES = ("x", "x_dot", "theta", "theta_dot")
STATE_UNITS = ("m", "m/s", "rad", "rad/s")
NOISE_SIGMA_BASE = np.array([
    0.001,                       # position measurement, m
    0.01,                        # velocity measurement, m/s
    math.radians(0.1),           # pitch measurement, rad
    math.radians(1.0),           # pitch-rate measurement, rad/s
])


def build_continuous_model(params: dict[str, float]) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    """Build x_dot = A x + B tau from the checked four-state model equations."""
    m = params["wheel_mass_kg"]
    radius = params["ball_radius_m"]
    jw = params["wheel_inertia_kgm2"]
    body_mass = params["body_mass_kg"]
    length = params["com_height_m"]
    inertia = params["body_pitch_inertia_x_kgm2"]
    gravity = params["gravity_mps2"]

    values = np.array([m, radius, jw, body_mass, length, inertia, gravity], dtype=float)
    if not np.all(np.isfinite(values)) or min(m, radius, body_mass, length, inertia, gravity) <= 0 or jw < 0:
        raise ValueError("Model parameters must be finite; masses, radius, length, inertia and gravity must be positive; wheel inertia may be zero.")

    a11 = m + jw / radius**2 + body_mass
    a12 = body_mass * length
    a22 = body_mass * length**2 + inertia
    delta = a11 * a22 - a12**2
    if not np.isfinite(delta) or delta <= 0:
        raise ValueError("The coupled inertia determinant must be positive.")

    A = np.zeros((4, 4), dtype=float)
    B = np.zeros((4, 1), dtype=float)
    # State order is [position, velocity, pitch angle, pitch rate].
    A[0, 1] = 1.0
    A[1, 2] = -(body_mass**2 * gravity * length**2) / delta
    A[2, 3] = 1.0
    A[3, 2] = (a11 * body_mass * gravity * length) / delta
    B[1, 0] = a22 / (delta * radius)
    B[3, 0] = -a12 / (delta * radius)
    terms = {"A11": a11, "A12": a12, "A22": a22, "delta": delta}
    return A, B, terms


def make_weight_cases() -> list[tuple[str, np.ndarray, np.ndarray]]:
    """Create one-factor-at-a-time Q/R comparisons around source values."""
    cases: list[tuple[str, np.ndarray, np.ndarray]] = []
    cases.append(("baseline_source_QR", Q_SOURCE.copy(), R_SOURCE.copy()))

    q = Q_SOURCE.copy()
    q[2, 2] *= 4.0
    cases.append(("pitch_weight_x4", q, R_SOURCE.copy()))

    q = Q_SOURCE.copy()
    q[3, 3] *= 4.0
    cases.append(("pitch_rate_weight_x4", q, R_SOURCE.copy()))

    cases.append(("input_cost_x4", Q_SOURCE.copy(), R_SOURCE * 4.0))
    cases.append(("input_cost_x0p25", Q_SOURCE.copy(), R_SOURCE * 0.25))
    return cases


def design_lqr(
    A: np.ndarray,
    B: np.ndarray,
    Ad: np.ndarray,
    Bd: np.ndarray,
    Q: np.ndarray,
    Ru: np.ndarray,
    method: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
    """Return P, K, sampled closed-loop eigenvalues and sampled stability flag."""
    if method == "continuous":
        P = solve_continuous_are(A, B, Q, Ru)
        K = np.linalg.solve(Ru, B.T @ P)
    else:
        P = solve_discrete_are(Ad, Bd, Q, Ru)
        K = np.linalg.solve(Ru + Bd.T @ P @ Bd, Bd.T @ P @ Ad)
    sampled_eigenvalues = np.linalg.eigvals(Ad - Bd @ K)
    sampled_stable = bool(np.max(np.abs(sampled_eigenvalues)) < 1.0)
    return P, K, sampled_eigenvalues, sampled_stable


def scenario_list(initial_pitch_deg: float, target_position_m: float) -> list[dict[str, object]]:
    zero = np.zeros(4, dtype=float)
    return [
        {
            "name": "recover_initial_pitch",
            "initial": np.array([0.0, 0.0, math.radians(initial_pitch_deg), 0.0]),
            "reference": zero.copy(),
            "disturbance_enabled": False,
        },
        {
            "name": "move_to_position",
            "initial": zero.copy(),
            "reference": np.array([target_position_m, 0.0, 0.0, 0.0]),
            "disturbance_enabled": False,
        },
        {
            "name": "move_and_recover_disturbance",
            "initial": zero.copy(),
            "reference": np.array([target_position_m, 0.0, 0.0, 0.0]),
            "disturbance_enabled": True,
        },
    ]


def simulate(
    Ad: np.ndarray,
    Bd: np.ndarray,
    K: np.ndarray,
    initial: np.ndarray,
    reference: np.ndarray,
    dt: float,
    duration: float,
    torque_limit_nm: float | None,
    disturbance_enabled: bool,
    disturbance_nm: float,
    disturbance_start_s: float,
    disturbance_end_s: float,
    measurement_noise_scale: float,
    measurement_delay_steps: int,
    random_seed: int,
    model_angle_limit_rad: float,
) -> dict[str, object]:
    """Sample the controller and use exact ZOH discretization for the plant."""
    step_count = int(round(duration / dt))
    state_history = [initial.astype(float).copy()]
    measurement_history: list[np.ndarray] = []
    records: list[dict[str, float | int]] = []
    raw_commands: list[float] = []
    applied_commands: list[float] = []
    disturbances: list[float] = []
    rng = np.random.default_rng(random_seed)
    status = "completed"

    for k in range(step_count):
        time_s = k * dt
        state = state_history[-1]
        # Create the sensor sample for this instant first, then delay the whole
        # sample (including its noise) by the requested number of periods.
        current_measurement = state + rng.normal(0.0, NOISE_SIGMA_BASE * measurement_noise_scale)
        measurement_history.append(current_measurement)
        delayed_index = max(0, len(measurement_history) - 1 - measurement_delay_steps)
        measured = measurement_history[delayed_index]
        error = measured - reference
        tau_raw = float((-K @ error).reshape(-1)[0])
        if torque_limit_nm is None:
            tau_applied = tau_raw
            saturated = 0
        else:
            tau_applied = float(np.clip(tau_raw, -torque_limit_nm, torque_limit_nm))
            saturated = int(abs(tau_raw - tau_applied) > 1e-12)

        tau_disturbance = (
            disturbance_nm
            if disturbance_enabled and disturbance_start_s <= time_s < disturbance_end_s
            else 0.0
        )
        next_state = Ad @ state + Bd[:, 0] * (tau_applied + tau_disturbance)

        record: dict[str, float | int] = {
            "time_s": time_s,
            "x_true_m": float(state[0]),
            "x_dot_true_mps": float(state[1]),
            "theta_true_rad": float(state[2]),
            "theta_true_deg": math.degrees(float(state[2])),
            "theta_dot_true_radps": float(state[3]),
            "x_measured_m": float(measured[0]),
            "x_dot_measured_mps": float(measured[1]),
            "theta_measured_rad": float(measured[2]),
            "theta_dot_measured_radps": float(measured[3]),
            "x_reference_m": float(reference[0]),
            "tau_raw_nm": tau_raw,
            "tau_applied_nm": tau_applied,
            "tau_disturbance_nm": float(tau_disturbance),
            "saturated": saturated,
        }
        records.append(record)
        raw_commands.append(tau_raw)
        applied_commands.append(tau_applied)
        disturbances.append(float(tau_disturbance))
        state_history.append(next_state)

        if not np.all(np.isfinite(next_state)):
            status = "non_finite_state"
            break
        if abs(float(next_state[2])) > model_angle_limit_rad:
            status = "outside_small_angle_model_range"
            break

    # Include the final state row. No new command is computed after the horizon.
    final_state = state_history[-1]
    final_time = (len(state_history) - 1) * dt
    records.append({
        "time_s": final_time,
        "x_true_m": float(final_state[0]),
        "x_dot_true_mps": float(final_state[1]),
        "theta_true_rad": float(final_state[2]),
        "theta_true_deg": math.degrees(float(final_state[2])),
        "theta_dot_true_radps": float(final_state[3]),
        "x_measured_m": float("nan"),
        "x_dot_measured_mps": float("nan"),
        "theta_measured_rad": float("nan"),
        "theta_dot_measured_radps": float("nan"),
        "x_reference_m": float(reference[0]),
        "tau_raw_nm": float("nan"),
        "tau_applied_nm": float("nan"),
        "tau_disturbance_nm": float("nan"),
        "saturated": 0,
    })

    states = np.asarray(state_history)
    times = np.arange(len(states), dtype=float) * dt
    errors = states - reference.reshape(1, 4)
    within = (
        (np.abs(errors[:, 0]) <= 0.01)
        & (np.abs(errors[:, 1]) <= 0.02)
        & (np.abs(errors[:, 2]) <= math.radians(1.0))
        & (np.abs(errors[:, 3]) <= math.radians(2.0))
    )
    settling_time = float("nan")
    for i in range(len(within)):
        if np.all(within[i:]):
            settling_time = float(times[i])
            break

    raw_array = np.asarray(raw_commands, dtype=float)
    applied_array = np.asarray(applied_commands, dtype=float)
    saturation_fraction = (
        float(np.mean(np.asarray([r["saturated"] for r in records[:-1]], dtype=float)))
        if torque_limit_nm is not None and raw_array.size
        else float("nan")
    )
    metrics = {
        "status": status,
        "max_abs_pitch_deg": float(np.max(np.abs(np.degrees(states[:, 2])))),
        "final_position_error_m": float(reference[0] - states[-1, 0]),
        "final_velocity_error_mps": float(reference[1] - states[-1, 1]),
        "final_pitch_error_deg": float(math.degrees(reference[2] - states[-1, 2])),
        "position_rmse_m": float(np.sqrt(np.mean(errors[:, 0] ** 2))),
        "max_abs_velocity_mps": float(np.max(np.abs(states[:, 1]))),
        "peak_abs_raw_torque_nm": float(np.max(np.abs(raw_array))) if raw_array.size else float("nan"),
        "peak_abs_applied_torque_nm": float(np.max(np.abs(applied_array))) if applied_array.size else float("nan"),
        "saturation_fraction": saturation_fraction,
        "control_effort_nm2s": float(np.sum(applied_array**2) * dt),
        "settling_time_s": settling_time,
    }
    return {
        "times": times,
        "states": states,
        "records": records,
        "raw_commands": raw_array,
        "applied_commands": applied_array,
        "disturbances": np.asarray(disturbances, dtype=float),
        "metrics": metrics,
    }


def write_run_csv(path: Path, records: list[dict[str, float | int]]) -> None:
    fieldnames = list(records[0].keys())
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def plot_scenario(path: Path, scenario_name: str, reference_x: float, all_runs: list[dict[str, object]]) -> None:
    fig, axes = plt.subplots(4, 1, figsize=(11, 12), sharex=True)
    for run in all_runs:
        label = str(run["case_name"])
        result = run["result"]
        times = result["times"]
        states = result["states"]
        axes[0].plot(times, states[:, 0], label=label)
        axes[1].plot(times, states[:, 1], label=label)
        axes[2].plot(times, np.degrees(states[:, 2]), label=label)
        commands = result["applied_commands"]
        if commands.size:
            axes[3].step(times[:-1], commands, where="post", label=label)
    axes[0].axhline(reference_x, color="black", linestyle="--", linewidth=1, label="position target")
    axes[0].set_ylabel("Position (m)")
    axes[1].set_ylabel("Velocity (m/s)")
    axes[2].set_ylabel("Pitch (deg)")
    axes[3].set_ylabel("Applied torque (N m)")
    axes[3].set_xlabel("Time (s)")
    for axis in axes:
        axis.grid(True, alpha=0.3)
        axis.legend(fontsize=8, ncol=2)
    fig.suptitle(f"Four-state LQR comparison: {scenario_name}")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Offline single-plane four-state LQR simulation; writes only to --out-dir."
    )
    parser.add_argument("--out-dir", type=Path, required=True, help="New or empty directory for CSV, PNG and metadata outputs.")
    parser.add_argument("--design", choices=("continuous", "discrete"), default="continuous",
                        help="continuous matches the source analysis path; discrete is an additional sampled-data comparison.")
    parser.add_argument("--dt", type=float, default=0.01, help="Controller/sample period in seconds; default 0.01 s (100 Hz).")
    parser.add_argument("--duration", type=float, default=5.0, help="Simulation horizon in seconds.")
    parser.add_argument("--target-position-m", type=float, default=0.20, help="Position target for move scenarios.")
    parser.add_argument("--initial-pitch-deg", type=float, default=1.5, help="Initial pitch for recovery scenario.")
    parser.add_argument("--torque-limit-nm", type=float, default=5.0, help="Teaching actuator limit; not a verified motor rating.")
    parser.add_argument("--no-saturation", action="store_true", help="Disable torque clipping for the ideal baseline run.")
    parser.add_argument("--disturbance-nm", type=float, default=0.1, help="Synthetic external equivalent torque during the disturbance scenario.")
    parser.add_argument("--disturbance-start-s", type=float, default=1.0)
    parser.add_argument("--disturbance-end-s", type=float, default=1.1)
    parser.add_argument("--noise-scale", type=float, default=0.0,
                        help="Scale of synthetic state-measurement noise; 0 disables noise. Noise levels are teaching values, not sensor measurements.")
    parser.add_argument("--measurement-delay-steps", type=int, default=0,
                        help="Use an older measurement by this many controller periods; 1 means one-period delay.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for repeatable synthetic noise.")
    parser.add_argument("--model-angle-limit-deg", type=float, default=20.0,
                        help="Stop a run outside this near-upright linear-model range; this is not a real robot fall threshold.")
    args = parser.parse_args()
    if args.dt <= 0 or args.duration <= 0 or args.target_position_m < 0:
        parser.error("dt and duration must be positive; target position must be nonnegative for this teaching setup.")
    if args.torque_limit_nm <= 0 or args.noise_scale < 0 or args.measurement_delay_steps < 0:
        parser.error("torque limit must be positive; noise scale and delay steps must be nonnegative.")
    if args.disturbance_end_s < args.disturbance_start_s:
        parser.error("disturbance end must not be earlier than disturbance start.")
    if not (0 < args.model_angle_limit_deg < 45):
        parser.error("model-angle limit must be between 0 and 45 degrees for this small-angle lab.")
    if abs(args.duration / args.dt - round(args.duration / args.dt)) > 1e-8:
        parser.error("duration must be an integer multiple of dt, e.g. 5.0 s with dt=0.01 s.")
    return args


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir.resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        raise SystemExit(f"Output directory is not empty; choose a new run folder: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    A, B, model_terms = build_continuous_model(MODEL_PARAMS)
    Ad, Bd, _, _, _ = cont2discrete(
        (A, B, np.eye(4), np.zeros((4, 1))), args.dt, method="zoh"
    )
    torque_limit = None if args.no_saturation else args.torque_limit_nm
    cases = make_weight_cases()
    scenarios = scenario_list(args.initial_pitch_deg, args.target_position_m)
    summary_rows: list[dict[str, object]] = []
    gains_metadata: dict[str, object] = {}
    plots_by_scenario: dict[str, list[dict[str, object]]] = {str(s["name"]): [] for s in scenarios}

    for case_name, Q, Ru in cases:
        P, K, sampled_eigenvalues, sampled_stable = design_lqr(A, B, Ad, Bd, Q, Ru, args.design)
        continuous_eigenvalues = (
            np.linalg.eigvals(A - B @ K) if args.design == "continuous" else None
        )
        gains_metadata[case_name] = {
            "Q": Q.tolist(),
            "R_u": Ru.tolist(),
            "P": P.tolist(),
            "K": K.tolist(),
            "sampled_closed_loop_eigenvalues_real_imag": [
                [float(value.real), float(value.imag)] for value in sampled_eigenvalues
            ],
            "sampled_closed_loop_stable_without_saturation": sampled_stable,
            "continuous_closed_loop_eigenvalues_real_imag": (
                [[float(value.real), float(value.imag)] for value in continuous_eigenvalues]
                if continuous_eigenvalues is not None
                else None
            ),
        }
        print(f"\n[{case_name}] design={args.design}; K={np.array2string(K, precision=5)}")
        print(f"  sampled linear closed-loop stable without saturation: {sampled_stable}")

        for scenario_index, scenario in enumerate(scenarios):
            result = simulate(
                Ad=Ad, Bd=Bd, K=K,
                initial=np.asarray(scenario["initial"], dtype=float),
                reference=np.asarray(scenario["reference"], dtype=float),
                dt=args.dt, duration=args.duration, torque_limit_nm=torque_limit,
                disturbance_enabled=bool(scenario["disturbance_enabled"]),
                disturbance_nm=args.disturbance_nm,
                disturbance_start_s=args.disturbance_start_s,
                disturbance_end_s=args.disturbance_end_s,
                measurement_noise_scale=args.noise_scale,
                measurement_delay_steps=args.measurement_delay_steps,
                # Keep the same synthetic noise sequence across weight cases
                # for a fairer one-factor-at-a-time comparison.
                random_seed=args.seed + scenario_index,
                model_angle_limit_rad=math.radians(args.model_angle_limit_deg),
            )
            scenario_name = str(scenario["name"])
            csv_name = f"{scenario_name}__{case_name}.csv"
            write_run_csv(out_dir / csv_name, result["records"])
            plots_by_scenario[scenario_name].append({"case_name": case_name, "result": result})
            metrics = result["metrics"]
            summary_rows.append({
                "design": args.design,
                "scenario": scenario_name,
                "weight_case": case_name,
                "status": metrics["status"],
                "max_abs_pitch_deg": metrics["max_abs_pitch_deg"],
                "final_position_error_m": metrics["final_position_error_m"],
                "final_velocity_error_mps": metrics["final_velocity_error_mps"],
                "final_pitch_error_deg": metrics["final_pitch_error_deg"],
                "position_rmse_m": metrics["position_rmse_m"],
                "max_abs_velocity_mps": metrics["max_abs_velocity_mps"],
                "peak_abs_raw_torque_nm": metrics["peak_abs_raw_torque_nm"],
                "peak_abs_applied_torque_nm": metrics["peak_abs_applied_torque_nm"],
                "saturation_fraction": metrics["saturation_fraction"],
                "control_effort_nm2s": metrics["control_effort_nm2s"],
                "settling_time_s": metrics["settling_time_s"],
                "sampled_closed_loop_stable_without_saturation": sampled_stable,
                "csv_file": csv_name,
            })

    for scenario in scenarios:
        name = str(scenario["name"])
        plot_scenario(
            out_dir / f"{name}__comparison.png",
            name,
            float(np.asarray(scenario["reference"])[0]),
            plots_by_scenario[name],
        )

    with (out_dir / "summary.csv").open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    metadata = {
        "model_type": "single-plane four-state continuous inverted-pendulum approximation",
        "state_order": list(STATE_NAMES),
        "state_units": list(STATE_UNITS),
        "input": "equivalent generalized torque tau (N m)",
        "model_parameter_source": MODEL_PARAMS_SOURCE,
        "model_parameters": MODEL_PARAMS,
        "model_terms": model_terms,
        "A_continuous": A.tolist(),
        "B_continuous": B.tolist(),
        "A_sampled_zoh": Ad.tolist(),
        "B_sampled_zoh": Bd.tolist(),
        "design_method": args.design,
        "sample_period_s": args.dt,
        "duration_s": args.duration,
        "torque_limit_nm": torque_limit,
        "measurement_noise_scale": args.noise_scale,
        "measurement_noise_sigma_base": NOISE_SIGMA_BASE.tolist(),
        "measurement_delay_steps": args.measurement_delay_steps,
        "random_seed_base": args.seed,
        "small_angle_stop_limit_deg": args.model_angle_limit_deg,
        "software_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "notes": [
            "Source-config parameter values are not independently measured or physically validated.",
            "This simulation is one-plane and near-upright; it is not a full three-wheel robot simulation.",
            "Continuous LQR with sampled feedback is not the same design as discrete LQR.",
            "Torque clipping, injected disturbance, measurement noise and delay are teaching settings, not measured hardware behavior.",
            "The script never imports ROS, connects hardware, or writes to original project configuration files.",
        ],
        "gain_cases": gains_metadata,
    }
    with (out_dir / "metadata.json").open("w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)

    print(f"\nSaved CSV, plots, summary and metadata under: {out_dir}")
    print("Read summary.csv first, then compare the scenario PNG files and per-run CSV files.")


if __name__ == "__main__":
    main()
