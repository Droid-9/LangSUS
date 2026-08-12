import json, random
from collections import deque

with open('SKLED.txt', encoding='utf-8') as f:
    lines = [l.rstrip('\n') for l in f]
H, W = len(lines), len(lines[0])

def is_floor(x, y):
    return 0 <= y < H and 0 <= x < W and lines[y][x] in ('.', '#', '0')

def bfs_path(start, goal):
    if start == goal:
        return [start]
    q = deque([start])
    came_from = {start: None}
    while q:
        cx, cy = q.popleft()
        if (cx, cy) == goal:
            break
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nb = (cx+dx, cy+dy)
            if is_floor(*nb) and nb not in came_from:
                came_from[nb] = (cx, cy)
                q.append(nb)
    if goal not in came_from:
        return None  # unreachable
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = came_from[cur]
    path.reverse()
    return path

tasks = [(x,y) for y,row in enumerate(lines) for x,ch in enumerate(row) if ch == '#']

SPAWN = (27, 4)
random.seed(42)  # same seed = same 6 targets you already have in paths.json
targets = random.sample(tasks, 6)
players = ["Red","Blue","Cyan","White","Black","Lime"]

assignment = dict(zip(players, targets))
paths = {}
for name, target in assignment.items():
    path = bfs_path(SPAWN, target)
    if path is None:
        print(f"UNREACHABLE: {name} -> {target}")
    else:
        paths[name] = path

with open('paths.json', 'w') as f:
    json.dump({"paths": paths, "targets": {k: list(v) for k,v in assignment.items()}}, f)
print("wrote paths.json")