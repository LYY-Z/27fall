"""Separate double-integrator teaching model; not a historical robot controller.

Delayed observations are deliberately treated as current to expose a timing fault.
This is NOT a delay-compensating Kalman filter. Runtime has not been verified.
"""
from pathlib import Path
import argparse
import csv
import numpy as np


def run_closed_loop(dt: float, duration: float, seed: int,
                    measurement_delay_steps: int,
                    control_limit: float) -> dict[str, np.ndarray]:
    if not np.isfinite(dt) or not np.isfinite(duration) or dt <= 0 or duration <= 0:
        raise ValueError('dt and duration must be finite and positive')
    if isinstance(measurement_delay_steps, bool) or not isinstance(measurement_delay_steps, int) or measurement_delay_steps < 0:
        raise ValueError('measurement_delay_steps must be a nonnegative integer')
    if not np.isfinite(control_limit) or control_limit <= 0:
        raise ValueError('control_limit must be finite and positive')
    steps = int(np.floor(duration / dt)) + 1
    if steps < 2 or steps > 1_000_000:
        raise ValueError('choose a duration/dt ratio between 1 and 999999')
    rng = np.random.default_rng(seed)
    A = np.array([[1., dt], [0., 1.]])
    B = np.array([.5 * dt * dt, dt])
    H = np.array([[1., 0.]])
    # A random constant acceleration disturbance over each interval.
    sigma_accel = .10
    Q = sigma_accel**2 * np.outer(B, B)
    measurement_variance = .05**2
    R = np.array([[measurement_variance]])
    truth = np.zeros(2)
    estimate = np.zeros(2)
    P = np.diag([.2**2, .3**2])
    applied_previous = 0.
    observation_history = []
    columns = ['time_s', 'true_position_m', 'estimated_position_m',
               'true_velocity_mps', 'estimated_velocity_mps',
               'reference_position_m', 'control_raw_mps2',
               'control_applied_mps2', 'innovation_m']
    data = {name: [] for name in columns}
    eye = np.eye(2)
    for k in range(steps):
        now = k * dt
        if k:
            acceleration_noise = rng.normal(0., sigma_accel)
            truth = A @ truth + B * (applied_previous + acceleration_noise)
            estimate = A @ estimate + B * applied_previous
            P = A @ P @ A.T + Q
        observation_history.append(truth[0] + rng.normal(0., np.sqrt(measurement_variance)))
        old_index = k - measurement_delay_steps
        innovation = np.nan
        if old_index >= 0:
            observed = observation_history[old_index]
            # Fault-injection option: ignores that this observation is from old_index.
            innovation = float(observed - (H @ estimate)[0])
            S = H @ P @ H.T + R
            K = np.linalg.solve(S, H @ P).T
            estimate = estimate + K[:, 0] * innovation
            correction = eye - K @ H
            P = correction @ P @ correction.T + K @ R @ K.T
            P = .5 * (P + P.T)
        reference = 0. if now < 1. else 1.
        # Teaching PD state feedback; these gains were not computed using LQR.
        raw = 4. * (reference - estimate[0]) - 3. * estimate[1]
        applied = float(np.clip(raw, -control_limit, control_limit))
        row = [now, truth[0], estimate[0], truth[1], estimate[1],
               reference, raw, applied, innovation]
        for name, value in zip(columns, row):
            data[name].append(value)
        applied_previous = applied
    return {name: np.asarray(values, dtype=float) for name, values in data.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--dt', type=float, default=.02)
    parser.add_argument('--duration', type=float, default=8.)
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--measurement-delay-steps', type=int, default=0)
    parser.add_argument('--control-limit', type=float, default=1.)
    args = parser.parse_args()
    data = run_closed_loop(args.dt, args.duration, args.seed,
                           args.measurement_delay_steps, args.control_limit)
    output = Path(args.out_dir)
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'closed_loop.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(data.keys())
        writer.writerows(zip(*data.values()))
    metadata = {
        'model': 'teaching double integrator; PD state feedback; scalar position KF',
        'dt_s': args.dt, 'duration_s': args.duration, 'seed': args.seed,
        'delay_steps': args.measurement_delay_steps,
        'delay_s': args.measurement_delay_steps * args.dt,
        'control_limit_mps2': args.control_limit,
        'measurement_std_m': .05, 'acceleration_noise_std_mps2': .10,
        'delay_handling': 'delayed samples incorrectly used as current; fault injection',
    }
    with (output / 'parameters.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['parameter', 'value'])
        writer.writerows(metadata.items())
    print(f'Wrote {len(data["time_s"])} rows to {output / "closed_loop.csv"}')


if __name__ == '__main__':
    main()
