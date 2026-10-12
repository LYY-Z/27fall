"""竖直支撑、两接触分配与虚功：教学参数，无真实接触设备。"""
import argparse
import csv
from pathlib import Path
import numpy as np

def virtual_support(z,z_dot,z_target,z_dot_target,mass,kp,kd,g=9.81):
    if not np.isfinite([z,z_dot,z_target,z_dot_target,mass,kp,kd,g]).all() or mass<=0 or g<=0 or kp<0 or kd<0:
        raise ValueError('Invalid support parameters')
    acceleration=kp*(z_target-z)+kd*(z_dot_target-z_dot)
    return mass*(g+acceleration)

def force_to_torque(J,force):
    J,force=np.asarray(J,float),np.asarray(force,float)
    if J.ndim!=2 or force.shape!=(J.shape[0],) or not np.isfinite(J).all() or not np.isfinite(force).all():
        raise ValueError('Expected finite compatible J and force')
    return J.T@force

def distribute_vertical_force(total,pitch_moment,half_span):
    # 第一接触x=-d，第二x=+d；z向上，y正力矩=d*(f1-f2)。
    if not np.isfinite([total,pitch_moment,half_span]).all() or half_span<=0 or total<0:
        raise ValueError('Expected nonnegative total force and positive span')
    forces=np.array([total/2+pitch_moment/(2*half_span),total/2-pitch_moment/(2*half_span)])
    if np.any(forces<0):raise ValueError('Infeasible: ordinary contacts cannot apply negative normal force')
    return forces

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir',type=Path,required=True)
    args=parser.parse_args();args.out_dir.mkdir(parents=True,exist_ok=True)
    print('Static support:',virtual_support(.5,0,.5,0,2,20,4))
    print('Recovery support:',virtual_support(.45,-.1,.5,0,2,20,4))
    print('Distribution:',distribute_vertical_force(20,2,.2))
    J=np.array([[-1.,-1.],[1.,0.]]);F=np.array([0.,10.]);dq=np.array([.01,.02])
    torque=force_to_torque(J,F);dx=J@dq
    print('Torque N.m:',torque,'endpoint work J:',F@dx,'joint work J:',torque@dq)
    with (args.out_dir/'virtual_work.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['dq1_rad','dq2_rad','dx_m','dz_m','tau1_Nm','tau2_Nm','endpoint_work_J','joint_work_J'])
        w.writerow([*dq,*dx,*torque,F@dx,torque@dq])
    try:distribute_vertical_force(20,6,.2)
    except ValueError as error:print('Expected infeasible rejection:',error)

if __name__=='__main__':main()
