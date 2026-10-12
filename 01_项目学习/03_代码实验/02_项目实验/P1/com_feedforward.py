"""合成固定双臂轨迹→质量加权CoM→重力矩与反向补偿。"""
import argparse
import csv
from pathlib import Path
import numpy as np

def combined_com(masses,positions):
    masses,positions=np.asarray(masses,float),np.asarray(positions,float)
    if masses.ndim!=1 or positions.shape!=(len(masses),3) or not np.isfinite(masses).all() or not np.isfinite(positions).all() or np.any(masses<0) or masses.sum()<=0:
        raise ValueError('Expected compatible finite positions and nonnegative masses with positive total')
    return (masses[:,None]*positions).sum(axis=0)/masses.sum()

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out-dir',type=Path,required=True)
    args=parser.parse_args();args.out_dir.mkdir(parents=True,exist_ok=True)
    masses=np.array([8.,1.,1.]);g=np.array([0.,0.,-9.81])
    with (args.out_dir/'com.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['time_s','com_x_m','com_y_m','com_z_m','gravity_roll_Nm','gravity_pitch_Nm','feedforward_roll_Nm','feedforward_pitch_Nm'])
        for t in np.linspace(0,10,101):
            arm_x=.3*np.sin(np.pi*t/10)
            positions=np.array([[0,0,.5],[arm_x,.2,.6],[arm_x,-.2,.6]])
            com=combined_com(masses,positions);moment=np.cross(com,masses.sum()*g)
            w.writerow([t,*com,moment[0],moment[1],-moment[0],-moment[1]])
    print('Symmetric forward arms CoM:',combined_com(masses,[[0,0,.5],[.3,.2,.6],[.3,-.2,.6]]))

if __name__=='__main__':main()
