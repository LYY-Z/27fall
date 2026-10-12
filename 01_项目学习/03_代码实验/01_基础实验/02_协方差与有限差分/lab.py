"""样本协方差与中心差分雅可比：教学数据。"""
import argparse
import csv
from pathlib import Path
import numpy as np

def sample_covariance(samples):
    samples = np.asarray(samples, dtype=float)
    if samples.ndim != 2 or len(samples) < 2 or samples.shape[1] == 0 or not np.isfinite(samples).all():
        raise ValueError('Expected at least two finite row samples')
    centered = samples - samples.mean(axis=0)
    return centered.T @ centered / (len(samples)-1)

def central_jacobian(fun, q, step):
    q = np.asarray(q, dtype=float)
    if q.ndim != 1 or q.size == 0 or step <= 0 or not np.isfinite(q).all() or not np.isfinite(step):
        raise ValueError('Expected finite one-dimensional q and positive step')
    columns = []
    for i in range(len(q)):
        dq = np.zeros_like(q)
        dq[i] = step
        plus, minus = np.asarray(fun(q+dq), float), np.asarray(fun(q-dq), float)
        if plus.ndim != 1 or plus.size == 0 or plus.shape != minus.shape or not np.isfinite(plus).all() or not np.isfinite(minus).all():
            raise ValueError('Function must return a consistent one-dimensional output')
        columns.append((plus-minus)/(2*step))
    return np.column_stack(columns)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    C = sample_covariance([[1,2],[2,4],[3,6]])
    q = np.array([0., np.pi/2])
    def fk(q):
        return np.array([np.cos(q[0])+np.cos(q.sum()), np.sin(q[0])+np.sin(q.sum())])
    exact = np.array([[-1.,-1.],[1.,0.]])
    with (args.out_dir/'finite_difference.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['step_rad','j11_m_per_rad','j12_m_per_rad','j21_m_per_rad','j22_m_per_rad','error_norm'])
        for h in [1e-1,1e-3,1e-5,1e-7,1e-10]:
            J = central_jacobian(fk, q, h)
            writer.writerow([h, *J.ravel(), np.linalg.norm(J-exact)])
            print('step=',h,'J=',J,'error=',np.linalg.norm(J-exact))
    np.savetxt(args.out_dir/'covariance.csv', C, delimiter=',', header='covariance_matrix', comments='')
    print('Sample covariance:', C)

if __name__ == '__main__':
    main()
