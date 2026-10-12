"""小型线性MPC：输入/输入变化约束，SLSQP教学解，不连接硬件。"""
import argparse
import csv
from pathlib import Path
import numpy as np

def solve_mpc(x0,reference,A,B,Q,R,Q_terminal,u_min,u_max,du_max,u_previous):
    x0,reference,A,B,Q,R,Q_terminal,u_min,u_max,du_max,u_previous=map(
        lambda x:np.asarray(x,float),(x0,reference,A,B,Q,R,Q_terminal,u_min,u_max,du_max,u_previous))
    if x0.ndim!=1 or B.ndim!=2 or reference.ndim!=2:raise ValueError('Invalid array dimensions')
    n,m=B.shape;N=len(reference)-1
    if N<1 or len(x0)!=n or reference.shape!=(N+1,n) or A.shape!=(n,n) or Q.shape!=(n,n) or Q_terminal.shape!=(n,n) or R.shape!=(m,m):
        raise ValueError('Inconsistent horizon/model/cost shapes')
    if any(v.shape!=(m,) for v in (u_min,u_max,du_max,u_previous)) or np.any(u_min>u_max) or np.any(du_max<0):
        raise ValueError('Invalid input/change bounds')
    if not all(np.isfinite(v).all() for v in (x0,reference,A,B,Q,R,Q_terminal,u_min,u_max,du_max,u_previous)):
        raise ValueError('Inputs must be finite')
    for cost in (Q,Q_terminal,R):
        if not np.allclose(cost,cost.T) or np.linalg.eigvalsh(cost).min()<-1e-10:
            raise ValueError('Costs must be symmetric positive semidefinite')
    if np.linalg.eigvalsh(R).min()<=0:raise ValueError('R must be positive definite')
    if np.any(u_previous<u_min) or np.any(u_previous>u_max):
        raise ValueError('Previous input must be feasible for this hold fallback example')
    from scipy.optimize import minimize
    def rollout(U):
        states=np.empty((N+1,n));states[0]=x0
        for k in range(N):states[k+1]=A@states[k]+B@U[k]
        return states
    def objective(flat):
        U=flat.reshape(N,m);states=rollout(U);error=states-reference
        value=sum(error[k]@Q@error[k]+U[k]@R@U[k] for k in range(N))
        return float(value+error[-1]@Q_terminal@error[-1])
    def changes(flat):
        U=flat.reshape(N,m)
        return np.diff(np.vstack([u_previous,U]),axis=0)
    constraints=[{'type':'ineq','fun':lambda flat:(du_max-changes(flat)).ravel()},
                 {'type':'ineq','fun':lambda flat:(du_max+changes(flat)).ravel()}]
    initial=np.tile(u_previous,(N,1)).ravel()
    result=minimize(objective,initial,method='SLSQP',bounds=list(zip(np.tile(u_min,N),np.tile(u_max,N))),
                    constraints=constraints,options={'maxiter':200,'ftol':1e-9})
    U=result.x.reshape(N,m)
    valid=(result.success and np.isfinite(U).all() and np.all(U>=u_min-1e-6) and
           np.all(U<=u_max+1e-6) and np.all(abs(changes(result.x))<=du_max+1e-6))
    if not valid:
        return np.full((N,m),np.nan),np.full((N+1,n),np.nan),'failed: '+str(result.message)
    return U,rollout(U),'optimal_numeric'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir',type=Path,required=True)
    args=parser.parse_args();args.out_dir.mkdir(parents=True,exist_ok=True)
    A=B=np.ones((1,1));Q=np.zeros((1,1));R=np.ones((1,1));terminal=np.array([[4.]])
    U,states,status=solve_mpc([1.],np.zeros((2,1)),A,B,Q,R,terminal,[-.2],[.2],[1.],[0.])
    print('Single-step expected -0.2; result:',U,'states:',states,'status:',status)
    x=np.array([1.]);previous=np.array([0.]);N=10
    with (args.out_dir/'mpc.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['step','state','u_first','input_change','status'])
        for k in range(30):
            U,predicted,status=solve_mpc(x,np.zeros((N+1,1)),A,B,[[4]],[[1]],[[4]],[-.2],[.2],[.1],previous)
            applied=U[0] if status=='optimal_numeric' else previous.copy()
            # 仅这个无状态约束教学模型中，保持上一可行输入是定义的备用动作。
            w.writerow([k,x[0],applied[0],applied[0]-previous[0],status])
            x=A@x+B@applied;previous=applied.copy()

if __name__=='__main__':main()
