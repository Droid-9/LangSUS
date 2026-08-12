"""
Shared map-reading utilities. Every file that needs wall/floor checks or
pathfinding should import from here instead of redefining is_floor/bfs_path.
"""
from collections import deque

with open('SKLED.txt', encoding='utf-8') as f:
    GRID = [l.rstrip('\n') for l in f]
H, W = len(GRID), len(GRID[0])

def is_floor(x, y):
    return 0 <= y < H and 0 <= x < W and GRID[y][x] in ('.', '#', '0')

def bfs_path(start, goal):
    """Shortest walkable path from start to goal, inclusive of both ends.
    Returns None if goal is unreachable."""
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
        return None
    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = came_from[cur]
    path.reverse()
    return path

TASK_COORDS = [(x, y) for y, row in enumerate(GRID) for x, ch in enumerate(row) if ch == '#']
SPAWN = next((x, y) for y, row in enumerate(GRID) for x, ch in enumerate(row) if ch == '0')

# --- room lookup, built from rooms_full.json (output of build_rooms.py) ---
import json as _json
with open('rooms_full.json') as _f:
    _ROOM_DATA = _json.load(_f)

CELL_TO_ROOM = {}       # named rooms only, for now
_corridor_cells = set()
for _name, _cells in _ROOM_DATA.items():
    if _name == "_corridor":
        _corridor_cells.update(tuple(c) for c in _cells)
    else:
        for _x, _y in _cells:
            CELL_TO_ROOM[(_x, _y)] = _name

# multi-source BFS: expand outward from every named-room cell simultaneously.
# each corridor cell gets labeled with whichever room reaches it FIRST -
# i.e. whichever named room it's actually nearest to, by real walkable distance.
_q = deque()
_nearest_room = {}
for _cell, _name in CELL_TO_ROOM.items():
    _nearest_room[_cell] = _name
    _q.append(_cell)

while _q:
    _cx, _cy = _q.popleft()
    for _dx, _dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        _nb = (_cx+_dx, _cy+_dy)
        if is_floor(*_nb) and _nb not in _nearest_room:
            _nearest_room[_nb] = _nearest_room[(_cx, _cy)]
            _q.append(_nb)

for _cell in _corridor_cells:
    _room = _nearest_room.get(_cell, "?")
    CELL_TO_ROOM[_cell] = f"Corridor (near {_room})"

def get_room(x, y):
    return CELL_TO_ROOM.get((x, y))

ALL_FLOOR_CELLS = [(x, y) for y in range(H) for x in range(W) if is_floor(x, y)]