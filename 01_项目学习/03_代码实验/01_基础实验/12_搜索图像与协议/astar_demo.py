"""四邻域栅格A*，坐标(row,col)，bool True为占据。"""
import argparse
import csv
import heapq
from pathlib import Path
import numpy as np

def astar_grid(occupied,start,goal):
    occupied=np.asarray(occupied,dtype=bool)
    if occupied.ndim!=2:raise ValueError('Expected 2D occupancy map')
    H,W=occupied.shape
    for cell in (start,goal):
        if len(cell)!=2 or not all(isinstance(v,(int,np.integer)) for v in cell):
            raise ValueError('Cells must be integer (row,col)')
        if not (0<=cell[0]<H and 0<=cell[1]<W) or occupied[tuple(cell)]:
            raise ValueError('Start and goal must be inside free cells')
    start,goal=tuple(start),tuple(goal)
    def heuristic(cell):return abs(cell[0]-goal[0])+abs(cell[1]-goal[1])
    heap=[(heuristic(start),0,start)];distance={start:0};parent={}
    while heap:
        _,g,node=heapq.heappop(heap)
        if g!=distance[node]:continue
        if node==goal:
            path=[node]
            while node!=start:node=parent[node];path.append(node)
            return path[::-1]
        for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
            neighbor=(node[0]+dr,node[1]+dc)
            r,c=neighbor
            if 0<=r<H and 0<=c<W and not occupied[r,c]:
                candidate=g+1
                if candidate<distance.get(neighbor,float('inf')):
                    distance[neighbor]=candidate;parent[neighbor]=node
                    heapq.heappush(heap,(candidate+heuristic(neighbor),candidate,neighbor))
    return []

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out-dir',type=Path,required=True)
    args=parser.parse_args();args.out_dir.mkdir(parents=True,exist_ok=True)
    grid=np.zeros((3,3),bool);path=astar_grid(grid,(0,0),(2,2))
    print('Path:',path,'steps:',len(path)-1)
    with (args.out_dir/'astar.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['step','row','col']);w.writerows((i,*cell) for i,cell in enumerate(path))
    grid[1,:]=True
    print('Unreachable path:',astar_grid(grid,(0,0),(2,2)))

if __name__=='__main__':main()
