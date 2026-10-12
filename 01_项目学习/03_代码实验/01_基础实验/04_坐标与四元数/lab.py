"""Hamilton四元数[w,x,y,z]；主动旋转，右者先作用。"""
import argparse
import csv
from pathlib import Path
import numpy as np

def unit_quaternion(q):
    q = np.asarray(q, dtype=float)
    if q.shape != (4,) or not np.isfinite(q).all():
        raise ValueError('Quaternion must have four finite components [w,x,y,z]')
    length = np.linalg.norm(q)
    if length <= np.finfo(float).tiny:
        raise ValueError('Zero quaternion cannot represent an orientation')
    return q/length

def quat_multiply(q2, q1):
    q2, q1 = np.asarray(q2,float), np.asarray(q1,float)
    if q2.shape != (4,) or q1.shape != (4,) or not np.isfinite(q2).all() or not np.isfinite(q1).all():
        raise ValueError('Expected [w,x,y,z] shape (4,)')
    w2,v2,w1,v1 = q2[0],q2[1:],q1[0],q1[1:]
    return np.r_[w2*w1-v2@v1, w2*v1+w1*v2+np.cross(v2,v1)]

def rotate_vector(q, p):
    q = unit_quaternion(q)
    p = np.asarray(p,float)
    if p.shape != (3,) or not np.isfinite(p).all():
        raise ValueError('Vector must have three finite components')
    conjugate = q * np.array([1.,-1.,-1.,-1.])
    return quat_multiply(quat_multiply(q,np.r_[0.,p]),conjugate)[1:]

def slerp(q0, q1, u):
    if not np.isfinite(u) or not 0 <= u <= 1:
        raise ValueError('Interpolation fraction must be in [0,1]')
    q0,q1 = unit_quaternion(q0),unit_quaternion(q1)
    dot = float(q0@q1)
    if dot < 0:
        q1=-q1; dot=-dot
    dot=np.clip(dot,-1.,1.)
    if dot > .9995:
        return unit_quaternion((1-u)*q0+u*q1)
    alpha=np.arccos(dot)
    q=(np.sin((1-u)*alpha)*q0+np.sin(u*alpha)*q1)/np.sin(alpha)
    return unit_quaternion(q)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out-dir',type=Path,required=True)
    args=p.parse_args(); args.out_dir.mkdir(parents=True,exist_ok=True)
    q0=np.array([1.,0,0,0]); q1=np.array([np.cos(np.pi/4),0,0,np.sin(np.pi/4)])
    print('Rotated x:',rotate_vector(q1,[1,0,0]))
    print('Negative quaternion:',rotate_vector(-q1,[1,0,0]))
    print('Physical difference deg:',np.degrees(2*np.arccos(np.clip(abs(q0@q1),0,1))))
    with (args.out_dir/'slerp.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['fraction','qw','qx','qy','qz','rotated_x','rotated_y','rotated_z','physical_angle_rad'])
        for u in np.linspace(0,1,11):
            q=slerp(q0,-q1,float(u)); v=rotate_vector(q,[1,0,0])
            angle=2*np.arccos(np.clip(abs(q0@q),0,1))
            w.writerow([u,*q,*v,angle])
    try: unit_quaternion([0,0,0,0])
    except ValueError as error: print('Expected rejection:',error)

if __name__=='__main__': main()
