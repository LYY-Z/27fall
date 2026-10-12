"""Teaching velocity IK: damping plus component speed limits, NOT a constrained QP."""
import argparse,csv
from pathlib import Path
import numpy as np
def fk(q,lengths):
    a,b=q;l1,l2=lengths
    return np.array([l1*np.cos(a)+l2*np.cos(a+b),l1*np.sin(a)+l2*np.sin(a+b)])
def jacobian(q,lengths):
    a,b=q;l1,l2=lengths
    return np.array([[-l1*np.sin(a)-l2*np.sin(a+b),-l2*np.sin(a+b)],[l1*np.cos(a)+l2*np.cos(a+b),l2*np.cos(a+b)]])
def damped_step(q,target,lengths,damping,dt,speed_limit):
    q=np.asarray(q,float);target=np.asarray(target,float);lengths=np.asarray(lengths,float)
    if q.shape!=(2,) or target.shape!=(2,) or lengths.shape!=(2,) or not np.all(np.isfinite(np.r_[q,target,lengths,damping,dt,speed_limit])) or np.any(lengths<=0) or min(damping,dt,speed_limit)<=0:raise ValueError("finite 2D inputs and positive parameters required")
    j=jacobian(q,lengths);v=2*(target-fk(q,lengths))
    rate=j.T@np.linalg.solve(j@j.T+damping*damping*np.eye(2),v)
    rate=np.clip(rate,-speed_limit,speed_limit)
    return q+dt*rate
def main():
    p=argparse.ArgumentParser();p.add_argument("--out-dir",type=Path,required=True);a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    with (a.out_dir/"damped_ik.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(["lambda","time_s","q1_rad","q2_rad","foot_x_m","foot_y_m","error_m","sigma_min"])
        for damping in (.01,.1):
            q=np.array([0.,.01]);lengths=np.array([1.,1.]);target=np.array([1.5,.4]);dt=.01
            for k in range(400):
                x=fk(q,lengths);w.writerow([damping,k*dt,*q,*x,np.linalg.norm(target-x),np.linalg.svd(jacobian(q,lengths),compute_uv=False)[-1]])
                q=damped_step(q,target,lengths,damping,dt,1.)
    print(a.out_dir)
if __name__=="__main__":main()
