from collections import deque
import json

with open('SKLED.txt', encoding='utf-8') as f:
    lines = [l.rstrip('\n') for l in f]
H, W = len(lines), len(lines[0])

def is_floor(x, y):
    return 0 <= y < H and 0 <= x < W and lines[y][x] in ('.', '#', '0')

# erosion: a floor cell survives only if all 4 neighbors are also floor
# (strips away anything touching a wall -> kills thin 1-cell corridors)
eroded = set()
for y in range(H):
    for x in range(W):
        if is_floor(x, y) and all(is_floor(x+dx, y+dy) for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]):
            eroded.add((x, y))

# connected components of the eroded set = room cores
visited = set()
cores = []
for cell in eroded:
    if cell in visited:
        continue
    comp = []
    q = deque([cell]); visited.add(cell)
    while q:
        cx, cy = q.popleft(); comp.append((cx, cy))
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nb = (cx+dx, cy+dy)
            if nb in eroded and nb not in visited:
                visited.add(nb); q.append(nb)
    cores.append(comp)
cores = [c for c in cores if len(c) >= 3]

# multi-source BFS: grow each core back out to reclaim its boundary cells
owner = {}
q = deque()
for i, r in enumerate(cores):
    for c in r:
        owner[c] = i; q.append(c)
conflict = set()
while q:
    cx, cy = q.popleft()
    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
        nb = (cx+dx, cy+dy)
        if not is_floor(*nb):
            continue
        if nb not in owner:
            owner[nb] = owner[(cx, cy)]; q.append(nb)
        elif owner[nb] != owner[(cx, cy)]:
            conflict.add(nb); conflict.add((cx, cy))

# match each core's bounding box to a known room name
NAME_BY_BBOX = {
    (41,48,1,4): "Weapons", (43,48,6,17): "Navigation", (37,48,19,23): "Shields",
    (30,35,9,12): "Admin", (17,24,9,18): "Electrical", (15,21,7,11): "Security",
    (1,8,1,3): "Upper Engine", (1,5,5,18): "Reactor", (1,9,20,23): "Lower Engine",
    (21,33,1,7): "Cafeteria",
}
room_cells = {name: set() for name in NAME_BY_BBOX.values()}
room_cells["Storage"] = set()
corridor_cells = set()

giant_blob_id = None
for i, r in enumerate(cores):
    xs = [c[0] for c in r]; ys = [c[1] for c in r]
    bbox = (min(xs), max(xs), min(ys), max(ys))
    if len(r) > 200:  # the merged blob - corridors tangled with Storage
        giant_blob_id = i
        continue
    matched = None
    for key, name in NAME_BY_BBOX.items():
        if key[0]<=bbox[0] and key[1]>=bbox[1] and key[2]<=bbox[2] and key[3]>=bbox[3]:
            matched = name; break
    if matched is None:
        best, bestd = None, 1e9
        for key, name in NAME_BY_BBOX.items():
            d = abs(key[0]-bbox[0])+abs(key[1]-bbox[1])+abs(key[2]-bbox[2])+abs(key[3]-bbox[3])
            if d < bestd: bestd, best = d, name
        matched = best
    for c, o in owner.items():
        if o == i and c not in conflict:
            room_cells[matched].add(c)

# carve Storage out of the giant blob manually (it never separates via erosion,
# it's one continuous open area with no 1-cell chokepoint)
for c, o in owner.items():
    if o == giant_blob_id and c not in conflict:
        x, y = c
        if 12 <= x <= 36 and 20 <= y <= 23:
            room_cells["Storage"].add(c)
        else:
            corridor_cells.add(c)

all_room_cells = set()
for cells in room_cells.values():
    all_room_cells |= cells
for y in range(H):
    for x in range(W):
        if is_floor(x, y) and (x, y) not in all_room_cells and (x, y) not in corridor_cells:
            corridor_cells.add((x, y))

# --- validation ---
seen = {}
overlaps = 0
for name, cells in room_cells.items():
    for c in cells:
        if c in seen:
            print(f"OVERLAP: {c} in both {seen[c]} and {name}"); overlaps += 1
        seen[c] = name
print(f"Overlaps: {overlaps}")

tasks = [(x,y) for y,row in enumerate(lines) for x,ch in enumerate(row) if ch == '#']
for t in tasks:
    if t not in seen:
        print(f"UNASSIGNED task: {t}")

out = {name: sorted(cells) for name, cells in room_cells.items()}
out["_corridor"] = sorted(corridor_cells)
with open('rooms_full.json', 'w') as f:
    json.dump(out, f)
print("wrote rooms_full.json")