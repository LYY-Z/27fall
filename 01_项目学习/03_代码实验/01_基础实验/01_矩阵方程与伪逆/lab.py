"""教学消元与SVD伪逆；不连接硬件。"""
import argparse
import csv
from pathlib import Path
import numpy as np

def gauss_solve(A, b):
    A = np.array(A, dtype=float, copy=True)
    b = np.array(b, dtype=float, copy=True)
    if A.ndim != 2 or A.shape[0] != A.shape[1] or b.shape != (A.shape[0],):
        raise ValueError('A must be square; b must be a one-dimensional vector')
    if not np.isfinite(A).all() or not np.isfinite(b).all():
        raise ValueError('Inputs must be finite')
    n = len(b)
    if n == 0:
        raise ValueError("A and b must be nonempty")
    threshold = np.finfo(float).eps * max(1., np.max(np.abs(A))) * max(1, n) * 10
    for k in range(n):
        pivot = k + np.argmax(np.abs(A[k:, k]))
        if abs(A[pivot, k]) <= threshold:
            raise ValueError('Singular or numerically singular matrix: use least squares')
        A[[k, pivot]] = A[[pivot, k]]
        b[[k, pivot]] = b[[pivot, k]]
        for i in range(k + 1, n):
            ratio = A[i, k] / A[k, k]
            A[i, k:] -= ratio * A[k, k:]
            b[i] -= ratio * b[k]
    x = np.zeros(n)
    for i in range(n - 1, -1, -1):
        x[i] = (b[i] - A[i, i+1:] @ x[i+1:]) / A[i, i]
    return x

def svd_pseudoinverse(A, tolerance):
    A = np.asarray(A, dtype=float)
    if A.ndim != 2 or min(A.shape) == 0 or not np.isfinite(A).all() or not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError('Expected finite matrix and nonnegative absolute tolerance')
    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    reciprocal = np.zeros_like(s)
    retained = s > tolerance
    reciprocal[retained] = 1 / s[retained]
    return (Vt.T * reciprocal) @ U.T

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--tolerance', type=float, default=1e-10)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, A, b in [('square', [[2,1],[0,1]], [10,4]),
                       ('redundant', [[1,1]], [1]),
                       ('singular', [[1,1],[2,2]], [1,2]),
                       ('weak', [[1,0],[0,.001]], [1,1])]:
        A, b = np.array(A, float), np.array(b, float)
        x = svd_pseudoinverse(A, args.tolerance) @ b
        s = np.linalg.svd(A, compute_uv=False)
        rows.append([name, *x, np.linalg.norm(A @ x-b), np.linalg.norm(x), *s.tolist()])
        print(name, 'x=', x, 'residual=', np.linalg.norm(A @ x-b), 'singular values=', s)
    print('Gaussian solution:', gauss_solve([[2,1],[0,1]], [10,4]))
    try:
        gauss_solve([[1,1],[2,2]], [1,2])
    except ValueError as error:
        print('Expected singular rejection:', error)
    with (args.out_dir/'solutions.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['case','x1','x2','residual_norm','input_norm','sigma1','sigma2_if_present'])
        writer.writerows(rows)

if __name__ == '__main__':
    main()
