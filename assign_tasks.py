import json, random
from player_state import Player, Task, players, SPAWN

with open('SKLED.txt', encoding='utf-8') as f:
    lines = [l.rstrip('\n') for l in f]

task_coords = [(x,y) for y,row in enumerate(lines) for x,ch in enumerate(row) if ch == '#']
assert len(task_coords) == 18, "expected 18 task points, map changed?"
assert len(players) == 6, "expected 6 players total"

random.seed(7)
shuffled = task_coords[:]
random.shuffle(shuffled)

DURATIONS = [3, 5, 10]

for i, p in enumerate(players):
    my_coords = shuffled[i*3:(i+1)*3]
    my_durations = DURATIONS[:]
    random.shuffle(my_durations)
    is_fake = (p.role == "impostor")
    p.task_list = [
        Task(coord=c, duration=d, is_fake=is_fake)
        for c, d in zip(my_coords, my_durations)
    ]