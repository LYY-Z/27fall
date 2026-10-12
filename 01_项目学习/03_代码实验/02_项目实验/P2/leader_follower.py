"""Planar two-link teaching model; follower is not the hardware SDK controller."""
import argparse,csv
from pathlib import Path
import numpy as np
def gravity_torque_two_link(q,lengths,masses,g=9.81):
    q=np.asarray(q,float);lengths=np.asarray(lengths,float);masses=np.asarray(masses,float)
    if any(v.shape!=(2,) for v in (q,lengths,masses)) or not np.all(np.isfinite(np.r_[q,lengths,masses,g])) or np.any(lengths<=0) or np.any(masses<=0) or g<=0:raise ValueError("finite two-link inputs with positive lengths/masses/g required")
    a,b=q;l1,l2=lengths;m1,m2=masses
    second=m2*l2*.5*np.cos(a+b)
    return g*np.array([(m1*l1*.5+m2*l1)*np.cos(a)+second,second])
def main():
    p=argparse.ArgumentParser();p.add_argument("--out-dir",type=Path,required=True);a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    q=np.zeros(2);dq=np.zeros(2);dt=.002;lengths=np.ones(2);masses=np.ones(2)
    with (a.out_dir/"leader_follower.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(["time_s","leader_q1_rad","leader_q2_rad","follower_q1_rad","follower_q2_rad","gravity1_Nm","gravity2_Nm","tau1_Nm","tau2_Nm"])
        for k in range(1500):
            t=k*dt;ref=np.array([.3*np.sin(t),.2*np.sin(t)]);refdot=np.array([.3*np.cos(t),.2*np.cos(t)])
            gravity=gravity_torque_two_link(q,lengths,masses);tau=gravity+20*(ref-q)+5*(refdot-dq);tau=np.clip(tau,-30,30)
            w.writerow([t,*ref,*q,*gravity,*tau])
            # Teaching unit inertia, no inter-link inertial coupling.
            ddq=tau-gravity-.2*dq;dq+=ddq*dt;q+=dq*dt
    with (a.out_dir/"differential.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(["v_m_s","yaw_rate_rad_s","right_rad_s","left_rad_s"]);w.writerow([.5,1.,7.,3.])
    print(a.out_dir)
if __name__=="__main__":main()
