"""Parent-frame active rotation increments. No hardware or VR client."""
import argparse,csv
from pathlib import Path
import numpy as np
def checked_rotation(r):
    r=np.asarray(r,float)
    if r.shape!=(3,3) or not np.all(np.isfinite(r)) or not np.allclose(r.T@r,np.eye(3),atol=1e-7) or not np.isclose(np.linalg.det(r),1):raise ValueError("proper rotation required")
    return r
def checked_pose(t):
    t=np.asarray(t,float)
    if t.shape!=(4,4) or not np.all(np.isfinite(t)) or not np.allclose(t[3],[0,0,0,1]):raise ValueError("finite homogeneous pose required")
    checked_rotation(t[:3,:3]);return t
def relative_target(T_robot_initial,T_vr_initial,T_vr_now,R_alignment,scale):
    r0=checked_pose(T_robot_initial);v0=checked_pose(T_vr_initial);vn=checked_pose(T_vr_now);align=checked_rotation(R_alignment)
    if not np.isfinite(scale) or scale<=0:raise ValueError("positive position scale required")
    result=np.eye(4);result[:3,3]=r0[:3,3]+scale*align@(vn[:3,3]-v0[:3,3])
    result[:3,:3]=(align@vn[:3,:3]@v0[:3,:3].T@align.T)@r0[:3,:3]
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument("--out-dir",type=Path,required=True);a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    r0=np.eye(4);r0[:3,3]=[.3,0,.4];v0=np.eye(4);v0[:3,3]=[1,2,3];vn=v0.copy();vn[0,3]+=.1;vn[:3,:3]=[[0,-1,0],[1,0,0],[0,0,1]]
    with (a.out_dir/"relative_pose.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(["case","target_x_m","target_y_m","target_z_m","R00","R01","R10","R11"])
        for label,t in [("stationary",v0),("moved_rotated",vn)]:
            out=relative_target(r0,v0,t,np.eye(3),.5);w.writerow([label,*out[:3,3],out[0,0],out[0,1],out[1,0],out[1,1]])
    print(a.out_dir)
if __name__=="__main__":main()
