"""Teaching Hybrid A*: 72 heading bins, forward/reverse primitives, no analytic expansion.
Grid occupied[row=y,col=x]. Centered conservative rectangle around rear-axle reference.
"""
import argparse,csv,heapq,itertools
from pathlib import Path
import numpy as np
from bicycle_model import bicycle_step,wrap_angle

def footprint_free(pose,occupied,resolution,footprint):
    """SAT between an oriented car rectangle and every potentially overlapping grid cell."""
    x,y,yaw=pose;length,width=footprint
    cx,sx=np.cos(yaw),np.sin(yaw);R=np.array([[cx,-sx],[sx,cx]])
    half=np.array([length/2,width/2])
    corners=np.array([[-1,-1],[-1,1],[1,-1],[1,1]])*half
    corners=corners@R.T+np.array([x,y])
    height,grid_width=occupied.shape
    low=corners.min(axis=0);high=corners.max(axis=0)
    if np.any(low<0) or high[0]>=grid_width*resolution or high[1]>=height*resolution:return False
    ix0,iy0=np.floor(low/resolution).astype(int);ix1,iy1=np.floor(high/resolution).astype(int)
    axes=[np.array([1.,0.]),np.array([0.,1.]),R[:,0],R[:,1]]
    for row in range(iy0,iy1+1):
        for col in range(ix0,ix1+1):
            if not occupied[row,col]:continue
            center=np.array([(col+.5)*resolution,(row+.5)*resolution]);delta=center-np.array([x,y])
            separated=False
            for axis in axes:
                car_radius=half[0]*abs(axis@R[:,0])+half[1]*abs(axis@R[:,1])
                cell_radius=resolution*.5*(abs(axis[0])+abs(axis[1]))
                if abs(delta@axis)>car_radius+cell_radius:
                    separated=True;break
            if not separated:return False
    return True

def plan_hybrid_astar(start,goal,occupied,resolution,wheelbase,steering_values,step_length,footprint):
    start=np.asarray(start,float);goal=np.asarray(goal,float);occupied=np.asarray(occupied,bool);steering_values=np.asarray(steering_values,float)
    if start.shape!=(3,) or goal.shape!=(3,) or occupied.ndim!=2 or not occupied.size or steering_values.ndim!=1 or not steering_values.size or len(footprint)!=2:
        raise ValueError("pose[3], 2D grid, steering vector and two footprint sizes required")
    if not np.all(np.isfinite(np.r_[start,goal,steering_values,resolution,wheelbase,step_length,footprint])) or min(resolution,wheelbase,step_length,*footprint)<=0 or np.any(abs(steering_values)>=np.pi/2):
        raise ValueError("finite geometry, positive scales and valid steering required")
    if not footprint_free(start,occupied,resolution,footprint) or not footprint_free(goal,occupied,resolution,footprint):
        return np.empty((0,3)),"invalid_start_or_goal"
    def key(p):
        return (int(p[0]/resolution),int(p[1]/resolution),int(((p[2]+np.pi)%(2*np.pi))/(2*np.pi)*72))
    def heuristic(p):return float(np.linalg.norm(p[:2]-goal[:2]))
    # Immutable nodes prevent parent pointers from changing when a bucket is improved.
    nodes=[(start,None,np.array([start]),0.)];best={key(start):(0.,0)};counter=itertools.count()
    heap=[(heuristic(start),next(counter),0)]
    samples=max(5,int(np.ceil(step_length/(resolution*.5))))
    expansions=0
    while heap and expansions<50000:
        _,_,index=heapq.heappop(heap);pose,parent,segment,cost=nodes[index]
        if best.get(key(pose),(None,None))[1]!=index:continue
        expansions+=1
        if heuristic(pose)<=max(.25,2*resolution) and abs(wrap_angle(pose[2]-goal[2]))<=np.pi/12:
            parts=[];cursor=index
            while cursor is not None:
                state,previous,part,_=nodes[cursor];parts.append(part);cursor=previous
            return np.vstack(parts[::-1]),"success_with_goal_tolerance"
        for direction in (1.,-1.):
            for steering in steering_values:
                state=np.r_[pose,direction];segment=[];valid=True
                for j in range(samples):
                    state=bicycle_step(state,[0.,steering],wheelbase,step_length/samples)
                    if not footprint_free(state[:3],occupied,resolution,footprint):valid=False;break
                    segment.append(state[:3].copy())
                if not valid:continue
                nxt=state[:3].copy();new_cost=cost+step_length*(1 if direction>0 else 1.2)+.02*abs(steering)
                bucket=key(nxt)
                if new_cost>=best.get(bucket,(float("inf"),None))[0]:continue
                new_index=len(nodes);nodes.append((nxt,index,np.array(segment),new_cost));best[bucket]=(new_cost,new_index)
                heapq.heappush(heap,(new_cost+heuristic(nxt),next(counter),new_index))
    return np.empty((0,3)),"search_budget_exhausted" if heap else "no_path_in_discretized_search"

def main():
    p=argparse.ArgumentParser();p.add_argument("--out-dir",type=Path,required=True);a=p.parse_args();a.out_dir.mkdir(parents=True,exist_ok=True)
    grid=np.zeros((60,80),bool);grid[10:45,38:42]=True
    path,status=plan_hybrid_astar(np.array([1.,1.,0.]),np.array([6.5,4.8,0.]),grid,.1,.5,np.array([-.5,0,.5]),.3,(.7,.35))
    with (a.out_dir/"path.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(["index","x_m","y_m","yaw_rad"])
        for i,row in enumerate(path):w.writerow([i,*row])
    with (a.out_dir/"status.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(["status","samples"]);w.writerow([status,len(path)])
    with (a.out_dir/"map.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f);w.writerow(["row","col","occupied"])
        for row,col in np.argwhere(grid):w.writerow([row,col,1])
    print(status,a.out_dir)
if __name__=="__main__":main()
