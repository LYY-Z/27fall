"""Radian teaching cascade with a simple rotational plant."""
import argparse,csv
from pathlib import Path
import numpy as np
def wrap_error(target,current):
    if not np.all(np.isfinite([target,current])):raise ValueError("finite radian angles required")
    return float((target-current+np.pi)%(2*np.pi)-np.pi)
def main():
    p=argparse.ArgumentParser();p.add_argument("--out-dir",type=Path,required=True);a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    theta=np.deg2rad(-179.);target=np.deg2rad(179.);rate=0.;dt=.002
    with (a.out_dir/"gimbal.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(["time_s","target_rad","angle_rad","error_rad","rate_ref_rad_s","rate_rad_s","torque_Nm"])
        for k in range(1500):
            error=wrap_error(target,theta);rate_ref=np.clip(4*error,-1,1);u=np.clip(3*(rate_ref-rate),-2,2)
            w.writerow([k*dt,target,theta,error,rate_ref,rate,u])
            rate+=dt*(u-.1*rate)/.2;theta=(theta+dt*rate+np.pi)%(2*np.pi)-np.pi
    print(a.out_dir)
if __name__=="__main__":main()
