"""SI kinematic bicycle. Position reference: rear axle center. Forward Euler."""
import argparse,csv
from pathlib import Path
import numpy as np
def wrap_angle(angle):return (angle+np.pi)%(2*np.pi)-np.pi
def bicycle_step(state,control,wheelbase,dt):
    s=np.asarray(state,float);u=np.asarray(control,float)
    if s.shape!=(4,) or u.shape!=(2,) or not np.all(np.isfinite(np.r_[s,u,wheelbase,dt])) or wheelbase<=0 or dt<=0 or abs(u[1])>=np.pi/2:
        raise ValueError("finite SI state[4], control[2], positive L/dt and |steering|<pi/2 required")
    x,y,yaw,speed=s;accel,steering=u
    result=s+dt*np.array([speed*np.cos(yaw),speed*np.sin(yaw),speed*np.tan(steering)/wheelbase,accel])
    result[2]=wrap_angle(result[2]);return result
def main():
    p=argparse.ArgumentParser();p.add_argument("--out-dir",type=Path,required=True);a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    with (a.out_dir/"bicycle.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(["case","time_s","x_m","y_m","yaw_rad","speed_m_s","accel_m_s2","steering_rad"])
        for case,steering in [("straight",0.),("circle",np.arctan(.5))]:
            state=np.array([0.,0.,0.,1.]);dt=.02
            for k in range(200):
                w.writerow([case,k*dt,*state,0,steering]);state=bicycle_step(state,[0,steering],.5,dt)
    print(a.out_dir)
if __name__=="__main__":main()
