"""四状态连续模型：LQR与明确PD教学对照，非原机完整PID。"""
import argparse
import csv
from pathlib import Path
import numpy as np

TEACHING_PARAMS={'wheel_mass_kg':1.,'ball_radius_m':.12,'wheel_inertia_kgm2':.005,
                 'body_mass_kg':3.,'com_height_m':.3,'body_inertia_kgm2':.2,'gravity_mps2':9.81}

def linear_balance_model(params):
    m=params['wheel_mass_kg'];R=params['ball_radius_m'];J=params['wheel_inertia_kgm2']
    M=params['body_mass_kg'];l=params['com_height_m'];I=params['body_inertia_kgm2'];g=params['gravity_mps2']
    if not np.isfinite([m,R,J,M,l,I,g]).all() or min(m,R,M,l,I,g)<=0 or J<0:
        raise ValueError('Invalid masses, lengths, inertia or gravity')
    a11=m+J/R**2+M;a12=M*l;a22=M*l*l+I;delta=a11*a22-a12*a12
    if delta<=0:raise ValueError('Invalid coupled mass matrix')
    A=np.zeros((4,4));B=np.zeros((4,1))
    A[0,1]=A[2,3]=1;A[1,2]=-M*M*g*l*l/delta;A[3,2]=a11*M*g*l/delta
    B[1,0]=a22/(delta*R);B[3,0]=-a12/(delta*R)
    return A,B

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out-dir',type=Path,required=True)
    parser.add_argument('--torque-limit',type=float,default=5.)
    args=parser.parse_args()
    if not np.isfinite(args.torque_limit) or args.torque_limit<=0:parser.error('Torque limit must be positive')
    from scipy.linalg import solve_continuous_are
    args.out_dir.mkdir(parents=True,exist_ok=True);A,B=linear_balance_model(TEACHING_PARAMS)
    Q=np.diag([1.,1.,50.,5.]);R=np.array([[.5]])
    P=solve_continuous_are(A,B,Q,R);K=np.linalg.solve(R,B.T@P)
    print('Teaching continuous LQR K:',K)
    dt=.002
    for method in ('lqr','pd'):
        x=np.array([0.,0.,.03,0.])
        with (args.out_dir/(method+'.csv')).open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f);w.writerow(['time_s','position_m','velocity_mps','theta_rad','theta_rate_radps','torque_raw_Nm','torque_applied_Nm','status'])
            for k in range(int(5/dt)):
                raw=float((-K@x)[0]) if method=='lqr' else .6*x[0]+x[1]+20*x[2]+5*x[3]
                applied=float(np.clip(raw,-args.torque_limit,args.torque_limit))
                status='model_range_exceeded' if abs(x[2])>.4 else 'within_teaching_range'
                w.writerow([k*dt,*x,raw,applied,status])
                if status=='model_range_exceeded':break
                disturbance=.1 if 1<=k*dt<1.1 else 0.
                x+=dt*(A@x+B[:,0]*(applied+disturbance))

if __name__=='__main__':main()
