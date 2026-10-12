"""Teaching normalized wheel-speed model, not real RPM/current parameters."""
import argparse,csv
from pathlib import Path
import numpy as np
TIME_CONSTANT=.15
def sliding_speed_control(error,rate,gain,boundary):
    """rate is measured normalized speed v, not an error derivative.

    Plant: TIME_CONSTANT * v_dot = u - v - load, constant reference.
    Surface s = reference - v = error. Apply u = v + tau*k*sat(s/phi).
    Then error_dot = -k*sat(error/phi) + load/tau before saturation.
    """
    if not np.all(np.isfinite([error,rate,gain,boundary])) or gain<=0 or boundary<=0:raise ValueError("finite error/rate and positive gain/boundary")
    return float(rate+TIME_CONSTANT*gain*np.clip(error/boundary,-1,1))
def main():
    p=argparse.ArgumentParser();p.add_argument("--out-dir",type=Path,required=True);a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    with (a.out_dir/"launcher.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(["controller","time_s","speed_normalized","target","error","output","load"])
        for controller in ("PI","boundary_SMC"):
            speed=0.;integral=0.;dt=.002
            for k in range(1500):
                t=k*dt;error=1-speed
                if controller=="PI":
                    candidate=np.clip(integral+error*dt,-1,1);raw=4*error+3*candidate
                    if abs(raw)<5 or raw*error<0:integral=candidate
                    u=np.clip(4*error+3*integral,-5,5)
                else:u=np.clip(sliding_speed_control(error,speed,5,.2),-5,5)
                load=.6 if 1<=t<1.2 else 0
                w.writerow([controller,t,speed,1,error,u,load]);speed+=dt*(u-speed-load)/TIME_CONSTANT
    print(a.out_dir)
if __name__=="__main__":main()
