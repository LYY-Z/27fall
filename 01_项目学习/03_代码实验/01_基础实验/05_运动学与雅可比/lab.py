"""平面二连杆与理想差速/全向运动学，单位m、rad、s。"""
import argparse
import csv
from pathlib import Path
import numpy as np

def validate(q, lengths):
    q,lengths=np.asarray(q,float),np.asarray(lengths,float)
    if q.shape!=(2,) or lengths.shape!=(2,) or np.any(lengths<=0) or not np.isfinite(np.r_[q,lengths]).all():
        raise ValueError('Expected two finite angles and two positive lengths')
    return q,lengths

def two_link_fk(q,lengths):
    q,l=validate(q,lengths)
    return np.array([l[0]*np.cos(q[0])+l[1]*np.cos(q.sum()),l[0]*np.sin(q[0])+l[1]*np.sin(q.sum())])

def two_link_jacobian(q,lengths):
    q,l=validate(q,lengths); s,c=np.sin(q.sum()),np.cos(q.sum())
    return np.array([[-l[0]*np.sin(q[0])-l[1]*s,-l[1]*s],
                     [l[0]*np.cos(q[0])+l[1]*c,l[1]*c]])

def two_link_ik(target,lengths,elbow=1):
    target,l=np.asarray(target,float),np.asarray(lengths,float)
    if target.shape!=(2,) or l.shape!=(2,) or not np.isfinite(target).all() or not np.isfinite(l).all() or np.any(l<=0) or elbow not in (-1,1):
        raise ValueError('Invalid target/lengths/assembly branch')
    radius=np.linalg.norm(target)
    if radius>l.sum()+1e-12 or radius<abs(l[0]-l[1])-1e-12:
        raise ValueError('Target unreachable for these link lengths')
    if radius<1e-12:
        raise ValueError('Coincident target gives nonunique shoulder angle')
    cos2=np.clip((radius**2-l@l)/(2*l[0]*l[1]),-1,1)
    q2=elbow*np.arccos(cos2)
    q1=np.arctan2(target[1],target[0])-np.arctan2(l[1]*np.sin(q2),l[0]+l[1]*np.cos(q2))
    return np.array([q1,q2])

def differential_wheels(v,omega,track):
    if not np.isfinite([v,omega,track]).all() or track<=0:
        raise ValueError('Track must be positive; velocities must be finite')
    return np.array([v-omega*track/2,v+omega*track/2])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir',type=Path,required=True)
    args=parser.parse_args();args.out_dir.mkdir(parents=True,exist_ok=True)
    q=np.array([0.,np.pi/2]);l=np.ones(2)
    J=two_link_jacobian(q,l);qdot=np.array([.1,.2]);dt=.01
    print('FK:',two_link_fk(q,l),'J:',J,'velocity:',J@qdot)
    print('Integrated FK:',two_link_fk(q+qdot*dt,l),'local approximation:',two_link_fk(q,l)+J@qdot*dt)
    print('IK:',two_link_ik([1,1],l))
    print('Wheels left/right m/s:',differential_wheels(1,2,.4))
    rho=.2
    A=np.array([[0,1,rho],[-np.sqrt(3)/2,-.5,rho],[np.sqrt(3)/2,-.5,rho]])
    body=np.array([1.,0,0]); wheels=A@body
    print('Omni wheel m/s:',wheels,'recovered body:',np.linalg.solve(A,wheels))
    with (args.out_dir/'singularity.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['q2_rad','rank','sigma_min','qdot_norm','residual_mps'])
        for q2 in [.5,.1,.01,0]:
            J=two_link_jacobian([0,q2],l);target=np.array([.1,0])
            dq=np.linalg.pinv(J)@target
            w.writerow([q2,np.linalg.matrix_rank(J),np.linalg.svd(J,compute_uv=False)[-1],np.linalg.norm(dq),np.linalg.norm(J@dq-target)])
    try: two_link_ik([3,0],l)
    except ValueError as error:print('Expected unreachable rejection:',error)

if __name__=='__main__':main()
