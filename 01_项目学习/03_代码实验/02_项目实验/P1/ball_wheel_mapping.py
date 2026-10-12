"""复现AIRS球角速度到轮轴角速度的几何；无硬件。"""
import argparse
import csv
from pathlib import Path
import numpy as np

def ball_wheel_matrix(ball_radius,wheel_radius,latitude_deg):
    if not np.isfinite([ball_radius,wheel_radius,latitude_deg]).all() or min(ball_radius,wheel_radius)<=0:
        raise ValueError('Radii must be finite positive and latitude finite')
    theta=np.radians(latitude_deg);azimuth=np.array([0,2*np.pi/3,4*np.pi/3])
    matrix=-(ball_radius/wheel_radius)*np.column_stack([np.sin(theta)*np.cos(azimuth),np.sin(theta)*np.sin(azimuth),-np.cos(theta)*np.ones(3)])
    if np.linalg.matrix_rank(matrix)<3:raise ValueError('Degenerate contact geometry cannot provide three-axis mapping')
    return matrix

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out-dir',type=Path,required=True)
    parser.add_argument('--latitude-deg',type=float,default=45.)
    args=parser.parse_args();args.out_dir.mkdir(parents=True,exist_ok=True)
    A=ball_wheel_matrix(.12,.06,args.latitude_deg)
    with (args.out_dir/'ball_wheels.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['ball_wx_radps','ball_wy_radps','ball_wz_radps','wheel1_radps','wheel2_radps','wheel3_radps','reconstruction_error_radps'])
        for omega in np.eye(3):
            wheels=A@omega;restored=np.linalg.solve(A,wheels)
            print('Ball:',omega,'wheels:',wheels,'recovered:',restored)
            w.writerow([*omega,*wheels,np.linalg.norm(restored-omega)])

if __name__=='__main__':main()
