"""X-layout FL/FR/RL/RR; P=coefficient*||wheel speeds||^2 only."""
import argparse,csv
from pathlib import Path
import numpy as np
def scale_wheel_targets(targets,estimated_power,power_limit):
    targets=np.asarray(targets,float)
    if targets.shape!=(4,) or not np.all(np.isfinite(np.r_[targets,estimated_power,power_limit])) or estimated_power<0 or power_limit<0:raise ValueError("four finite speeds and nonnegative power required")
    scale=1. if estimated_power<=power_limit or estimated_power==0 else float(np.sqrt(power_limit/estimated_power))
    return targets*scale,scale
def mecanum_matrix(radius=.1,half_length=.2,half_width=.2):
    if not np.isfinite([radius,half_length,half_width]).all() or min(radius,half_length,half_width)<=0:raise ValueError("positive geometry required")
    d=half_length+half_width
    return np.array([[1,-1,-d],[1,1,d],[1,1,-d],[1,-1,d]])/radius
def main():
    p=argparse.ArgumentParser();p.add_argument("--out-dir",type=Path,required=True);a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    raw=mecanum_matrix()@np.array([1.,.5,1.]);estimated=.2*float(raw@raw);limited,scale=scale_wheel_targets(raw,estimated,25.)
    with (a.out_dir/"mecanum_power.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(["wheel_index","raw_rad_s","limited_rad_s","scale","estimated_W","limited_model_W"])
        for i in range(4):w.writerow([i,raw[i],limited[i],scale,estimated,.2*float(limited@limited)])
    print(a.out_dir)
if __name__=="__main__":main()
