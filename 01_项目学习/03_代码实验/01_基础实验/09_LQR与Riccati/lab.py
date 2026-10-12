"""离散LQR与Riccati教学计算，双积分模型；需要NumPy/SciPy。"""
import argparse
import csv
from pathlib import Path
import numpy as np

def double_integrator_matrices(dt):
    if not np.isfinite(dt) or dt<=0:
        raise ValueError('dt must be finite and positive')
    return np.array([[1.,dt],[0,1.]]),np.array([[dt*dt/2],[dt]])

def scalar_riccati_step(A,B,Q,R,P):
    if not np.isfinite([A,B,Q,R,P]).all() or Q<0 or R<=0 or P<0:
        raise ValueError('Expected finite scalars with Q/P nonnegative and R positive')
    return Q+A*A*P-(A*B*P)**2/(R+B*B*P)

def discrete_lqr(A,B,Q,R):
    A,B,Q,R=map(lambda x:np.asarray(x,float),(A,B,Q,R))
    if A.ndim!=2 or A.shape[0]!=A.shape[1] or B.ndim!=2 or B.shape[0]!=A.shape[0]:
        raise ValueError('Invalid state/input matrix shapes')
    n,m=B.shape
    if Q.shape!=(n,n) or R.shape!=(m,m) or not all(np.isfinite(x).all() for x in (A,B,Q,R)):
        raise ValueError('Invalid cost shapes or nonfinite data')
    if not np.allclose(Q,Q.T) or not np.allclose(R,R.T) or np.linalg.eigvalsh(Q).min()<-1e-10 or np.linalg.eigvalsh(R).min()<=0:
        raise ValueError('Q must be symmetric semidefinite; R symmetric positive definite')
    try:
        from scipy.linalg import solve_discrete_are
    except ImportError as error:
        raise RuntimeError('SciPy is required for DARE; install it in the teaching environment') from error
    P=solve_discrete_are(A,B,Q,R)
    K=np.linalg.solve(R+B.T@P@B,B.T@P@A)
    return P,K

def evaluate_gain_polynomial(coefficients,length):
    coefficients=np.asarray(coefficients,float)
    if coefficients.ndim!=2 or coefficients.shape[1]!=4 or not np.isfinite(coefficients).all() or not np.isfinite(length) or length<=0:
        raise ValueError('Expected finite (k,4) coefficients and positive length in m')
    return ((coefficients[:,0]*length+coefficients[:,1])*length+coefficients[:,2])*length+coefficients[:,3]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir',type=Path,required=True)
    parser.add_argument('--dt',type=float,default=.1)
    parser.add_argument('--control-limit',type=float,default=2.)
    args=parser.parse_args()
    if not np.isfinite(args.control_limit) or args.control_limit<=0:parser.error('Control limit must be positive')
    A,B=double_integrator_matrices(args.dt);Q=np.diag([10.,1.]);R=np.array([[.1]])
    P,K=discrete_lqr(A,B,Q,R)
    args.out_dir.mkdir(parents=True,exist_ok=True)
    np.savetxt(args.out_dir/'P.csv',P,delimiter=',',header='value_function_matrix',comments='')
    np.savetxt(args.out_dir/'K.csv',K,delimiter=',',header='position_gain,velocity_gain',comments='')
    print('A:',A,'B:',B,'P:',P,'K:',K,'closed-loop eigenvalues:',np.linalg.eigvals(A-B@K))
    with (args.out_dir/'scalar_riccati.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['remaining_horizon','P','first_gain']);p=0.
        w.writerow([0,p,''])
        for i in range(1,21):
            first_gain=p/(1+p);p=scalar_riccati_step(1,1,1,1,p)
            w.writerow([i,p,first_gain])
    x=np.array([1.,0.])
    with (args.out_dir/'lqr.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['time_s','position_error_m','velocity_mps','u_raw_mps2','u_applied_mps2','state_cost','input_cost'])
        for k in range(int(10/args.dt)):
            raw=float((-K@x)[0]);applied=float(np.clip(raw,-args.control_limit,args.control_limit))
            w.writerow([k*args.dt,*x,raw,applied,float(x@Q@x),float(R[0,0]*applied**2)])
            x=A@x+B[:,0]*applied
    print('Teaching polynomial example:',evaluate_gain_polynomial([[2,-1,.5,.1]],.2))

if __name__=='__main__':main()
