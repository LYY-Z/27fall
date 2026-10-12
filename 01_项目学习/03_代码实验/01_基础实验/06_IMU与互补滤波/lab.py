"""局部roll互补滤波与比力变换，教学仿真；rad、m/s^2、s。"""
import argparse
import csv
from pathlib import Path
import numpy as np

def world_acceleration(specific_force_body,R_world_body,bias_body,gravity_world):
    f,R,b,g=map(lambda x:np.asarray(x,float),(specific_force_body,R_world_body,bias_body,gravity_world))
    if f.shape!=(3,) or R.shape!=(3,3) or b.shape!=(3,) or g.shape!=(3,):
        raise ValueError('Expected f,b,g shape (3,) and R shape (3,3)')
    if not all(np.isfinite(x).all() for x in (f,R,b,g)):
        raise ValueError('Inputs must be finite')
    if not np.allclose(R.T@R,np.eye(3),atol=1e-6) or not np.isclose(np.linalg.det(R),1.,atol=1e-6):
        raise ValueError('R must be a proper rotation from body to world')
    return R@(f-b)+g

def complementary_step(theta,gyro,theta_acc,dt,alpha):
    if not np.isfinite([theta,gyro,theta_acc,dt,alpha]).all() or dt<=0 or not 0<=alpha<=1:
        raise ValueError('Expected finite inputs, positive dt and alpha in [0,1]')
    prediction=theta+gyro*dt
    # 本演示roll保持在局部小角度范围；一般周期角需wrap创新。
    return alpha*prediction+(1-alpha)*theta_acc

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir',type=Path,required=True)
    parser.add_argument('--seed',type=int,default=7)
    parser.add_argument('--alpha',type=float,default=.98)
    parser.add_argument('--gyro-bias',type=float,default=.01)
    args=parser.parse_args();args.out_dir.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(args.seed);dt=.01
    print('Stationary world acceleration:',world_acceleration([0,0,9.81],np.eye(3),np.zeros(3),[0,0,-9.81]))
    print('One complementary step:',complementary_step(.1,.2,.09,.01,.98))
    theta=gyro_only=0.
    with (args.out_dir/'imu.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['time_s','true_roll_rad','gyro_radps','acc_roll_rad','gyro_integral_rad','complementary_rad','acc_polluted','gyro_sample_time_s'])
        # Initial state at t=0: no interval has been integrated or measured yet.
        w.writerow([0.,0.,float('nan'),float('nan'),gyro_only,theta,0,float('nan')])
        for k in range(1,int(round(20/dt))+1):
            start=(k-1)*dt
            t=k*dt
            # A start-time rate is held over [start,t] for Euler prediction.
            rate=.1*np.cos(.5*start)
            gyro=rate+args.gyro_bias+rng.normal(0,.005)
            truth=.2*np.sin(.5*t)
            polluted=5<=t<7
            # End-time observation corrects the prediction at the SAME end time.
            acc_angle=truth+rng.normal(0,.02)+(.2 if polluted else 0)
            gyro_only+=gyro*dt
            theta=complementary_step(theta,gyro,acc_angle,dt,args.alpha)
            w.writerow([t,truth,gyro,acc_angle,gyro_only,theta,int(polluted),start])
    print('Output:',args.out_dir/'imu.csv')

if __name__=='__main__':main()
