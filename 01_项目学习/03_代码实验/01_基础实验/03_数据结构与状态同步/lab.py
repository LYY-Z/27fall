"""Dijkstra与反馈时效判断；教学图和状态，无网络通信。"""
import argparse
import csv
import heapq
import math
from pathlib import Path

def shortest_path(graph, start, goal):
    for edges in graph.values():
        for _, cost in edges:
            if not math.isfinite(cost) or cost < 0:
                raise ValueError('Dijkstra requires finite nonnegative edge weights')
    distances, parent = {start: 0.}, {}
    heap = [(0., start)]
    while heap:
        cost, node = heapq.heappop(heap)
        if cost != distances[node]:
            continue
        if node == goal:
            path = [node]
            while node != start:
                node = parent[node]
                path.append(node)
            return path[::-1], cost
        for neighbor, weight in graph.get(node, []):
            candidate = cost + weight
            if candidate < distances.get(neighbor, math.inf):
                distances[neighbor] = candidate
                parent[neighbor] = node
                heapq.heappush(heap, (candidate, neighbor))
    return [], math.inf

def accept_feedback(current_seq, incoming_seq, age_s, max_age_s):
    if max_age_s < 0 or not math.isfinite(max_age_s):
        raise ValueError('max_age_s must be finite and nonnegative')
    return (incoming_seq > current_seq and math.isfinite(age_s)
            and 0 <= age_s <= max_age_s)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    graph = {'A':[('B',1.),('C',5.)], 'B':[('C',2.)], 'C':[]}
    path, cost = shortest_path(graph, 'A','C')
    print('Shortest path:',path,'cost:',cost)
    print('Unreachable:',shortest_path(graph,'C','A'))
    current_seq = 10
    with (args.out_dir/'feedback.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f)
        w.writerow(['current_sequence','incoming_sequence','age_s','accepted'])
        for incoming, age in [(9,.01),(10,.01),(11,.5),(11,.02),(12,-.01),(12,.01)]:
            accepted=accept_feedback(current_seq,incoming,age,.1)
            w.writerow([current_seq,incoming,age,int(accepted)])
            print('incoming',incoming,'age',age,'accepted',accepted)
            if accepted:
                current_seq=incoming
    with (args.out_dir/'path.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['step','node','total_path_cost'])
        w.writerows((i,node,cost) for i,node in enumerate(path))

if __name__=='__main__':
    main()
