"""教学PID回算与位置-速度级联；未接电机。"""
import argparse
import csv
from pathlib import Path
import numpy as np

OUTER_KP=1.2
INNER_KP=3.0
OUTER_SKIP=5
SPEED_LIMIT=.6
ACCELERATION_LIMIT=2.

def pid_step(error,measured_rate,dt,integral_output,kp,ki,kd,kaw,limits):
    low,high=limits
    if dt<=0 or low>=high or kaw<0 or not np.isfinite([error,measured_rate,dt,integral_output,kp,ki,kd,kaw,low,high]).all():
        raise ValueError('Expected finite inputs, positive dt, ordered limits and nonnegative kaw')
    raw=kp*error+integral_output-kd*measured_rate
    applied=float(np.clip(raw,low,high))
    integral_next=integral_output+(ki*error+kaw*(applied-raw))*dt
    return applied,integral_next,raw

def simulate_cascade(dt,duration,reference,delay_steps):
    if not np.isfinite([dt,duration,reference]).all() or dt<=0 or duration<dt or isinstance(delay_steps,bool) or not isinstance(delay_steps,int) or delay_steps<0:
        raise ValueError('Expected positive time parameters and nonnegative integer delay')
    position=velocity=integral=0.;history=[(position,velocity)]
    rows=[];speed_reference=0.
    for k in range(int(duration/dt)):
        measured_p,measured_v=history[max(0,len(history)-1-delay_steps)]
        if k%OUTER_SKIP==0:
            speed_reference=float(np.clip(OUTER_KP*(reference-measured_p),-SPEED_LIMIT,SPEED_LIMIT))
        applied,integral,raw=pid_step(speed_reference-measured_v,0.,dt,integral,INNER_KP,.5,0.,2.,(-ACCELERATION_LIMIT,ACCELERATION_LIMIT))
        position+=velocity*dt+.5*applied*dt*dt
        velocity+=applied*dt
        history.append((position,velocity))
        rows.append([(k+1)*dt,position,velocity,measured_p,measured_v,speed_reference,raw,applied])
    data=np.asarray(rows)
    names=['time_s','position_m','velocity_mps','measured_position_m','measured_velocity_mps','speed_reference_mps','acceleration_raw_mps2','acceleration_applied_mps2']
    return {name:data[:,i] for i,name in enumerate(names)}

def simulate_windup(kaw):
    dt=.01;velocity=integral=previous_velocity=0.;rows=[]
    for k in range(1000):
        t=k*dt;target=3. if t<5 else 0.
        rate=(velocity-previous_velocity)/dt
        applied,integral,raw=pid_step(target-velocity,rate,dt,integral,4.,2.,.02,kaw,(-1.,1.))
        previous_velocity=velocity
        velocity+=(-velocity+applied)/.5*dt
        rows.append([t,target,velocity,raw,applied,integral])
    return rows

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir',type=Path,required=True)
    parser.add_argument('--delay-steps',type=int,default=0)
    args=parser.parse_args();args.out_dir.mkdir(parents=True,exist_ok=True)
    print('Proportional example:',pid_step(2,0,.1,0,2,0,0,0,(-5,5)))
    print('Saturation example:',pid_step(3,0,.1,0,4,1,0,2,(-5,5)))
    print('Wrapped error deg:',np.degrees((np.radians(179-(-179))+np.pi)%(2*np.pi)-np.pi))
    for name,kaw in [('no_antiwindup',0.),('back_calculation',2.)]:
        with (args.out_dir/(name+'.csv')).open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f);w.writerow(['time_s','reference','velocity','u_raw','u_applied','integral_output']);w.writerows(simulate_windup(kaw))
    data=simulate_cascade(.01,10.,1.,args.delay_steps)
    with (args.out_dir/'cascade.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(data);w.writerows(zip(*data.values()))

if __name__=='__main__':main()
