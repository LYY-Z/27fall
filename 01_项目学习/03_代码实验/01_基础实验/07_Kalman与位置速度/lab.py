"""线性Kalman、Joseph协方差更新；位置m、速度m/s、加速度m/s^2。"""
import argparse
import csv
from pathlib import Path
import numpy as np

def covariance_matrix(value,size,name):
    value=np.asarray(value,float)
    if not isinstance(size,int) or isinstance(size,bool) or size <= 0:
        raise ValueError("Covariance dimension must be a positive integer")
    if value.shape!=(size,size) or not np.isfinite(value).all() or not np.allclose(value,value.T,atol=1e-10):
        raise ValueError(f'{name} must be finite symmetric shape ({size},{size})')
    if np.linalg.eigvalsh(value).min() < -1e-10:
        raise ValueError(f'{name} must be positive semidefinite')
    return value

def kalman_predict(x,P,A,B,u,Q):
    x,A,B,u=map(lambda v:np.asarray(v,float),(x,A,B,u))
    if x.ndim!=1 or u.ndim!=1 or A.shape!=(len(x),len(x)) or B.shape!=(len(x),len(u)):
        raise ValueError('State/model/input dimensions do not match')
    if not all(np.isfinite(v).all() for v in (x,A,B,u)):
        raise ValueError('Inputs must be finite')
    P=covariance_matrix(P,len(x),'P');Q=covariance_matrix(Q,len(x),'Q')
    return A@x+B@u,A@P@A.T+Q

def kalman_update(x_pred,P_pred,y,H,R):
    x_pred,y,H=map(lambda v:np.asarray(v,float),(x_pred,y,H))
    if x_pred.ndim!=1 or y.ndim!=1 or H.shape!=(len(y),len(x_pred)):
        raise ValueError('Measurement/state dimensions do not match')
    if not all(np.isfinite(v).all() for v in (x_pred,y,H)):
        raise ValueError('Inputs must be finite')
    P_pred=covariance_matrix(P_pred,len(x_pred),'P_pred')
    R=covariance_matrix(R,len(y),'R')
    innovation=y-H@x_pred
    S=H@P_pred@H.T+R
    try:
        K=np.linalg.solve(S,(P_pred@H.T).T).T
    except np.linalg.LinAlgError as error:
        raise ValueError('Innovation covariance is singular; check noise/model') from error
    updated=x_pred+K@innovation
    residual_map=np.eye(len(x_pred))-K@H
    P=residual_map@P_pred@residual_map.T+K@R@K.T
    P=(P+P.T)/2  # 消除浮点反对称小量，不修复错误噪声模型
    return updated,P,innovation,K

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir',type=Path,required=True)
    parser.add_argument('--seed',type=int,default=7)
    parser.add_argument('--measurement-std',type=float,default=.2)
    parser.add_argument('--process-std',type=float,default=.3)
    args=parser.parse_args()
    if not np.isfinite([args.measurement_std,args.process_std]).all() or args.measurement_std<=0 or args.process_std<0:
        parser.error('Measurement std must be positive; process std nonnegative')
    args.out_dir.mkdir(parents=True,exist_ok=True)
    print('Scalar:',kalman_update([10],[[4]],[12],[[1]],[[1]]))
    print('Two-state:',kalman_update([10,2],[[4,1],[1,2]],[12],[[1,0]],[[1]]))
    dt=.05;A=np.array([[1,dt],[0,1.]]);B=np.array([[dt*dt/2],[dt]])
    H=np.array([[1.,0.]]);Q=args.process_std**2*(B@B.T);R=np.array([[args.measurement_std**2]])
    rng=np.random.default_rng(args.seed);truth=np.array([0.,1.]);x=np.zeros(2);P=np.diag([1.,1.])
    with (args.out_dir/'kalman.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['time_s','true_position_m','true_velocity_mps','measurement_m','estimated_position_m','estimated_velocity_mps','innovation_m','gain_position','gain_velocity_per_s','position_variance_m2','velocity_variance_m2ps2','cross_covariance_m2ps'])
        for k in range(1,201):
            u=np.array([.2*np.sin(k*dt)])
            truth=A@truth+B@(u+rng.normal(0,args.process_std,size=1))
            y=H@truth+rng.normal(0,args.measurement_std,size=1)
            pred,Ppred=kalman_predict(x,P,A,B,u,Q)
            x,P,r,K=kalman_update(pred,Ppred,y,H,R)
            w.writerow([k*dt,*truth,y[0],*x,r[0],K[0,0],K[1,0],P[0,0],P[1,1],P[0,1]])
    print('Output:',args.out_dir/'kalman.csv')

if __name__=='__main__':main()
