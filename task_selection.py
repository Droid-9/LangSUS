from mapdata import bfs_path
from player_state import players
import assign_tasks  # runs task assignment on import, populates players' task_lists

def pick_next_task(player, meetings_held):
    undone = [(i, t) for i, t in enumerate(player.task_list) if not t.done]
    if not undone:
        return None  # all tasks done -> roam

    if player.task_strategy == "delayed_observer" and meetings_held < 1:
        return None  # holding off entirely, round 0 -> roam/observe instead

    scored = []
    for i, t in enumerate(player.task_list):
        if t.done:
            continue
        path = bfs_path((player.x, player.y), t.coord)
        if path is None:
            continue
        scored.append((i, len(path)))

    if not scored:
        return None

    if player.task_strategy == "farthest":
        chosen = max(scored, key=lambda pair: pair[1])
    else:  # "nearest" and activated "delayed_observer" both default to nearest
        chosen = min(scored, key=lambda pair: pair[1])
    return chosen[0]

if __name__ == "__main__":
    print("=== meetings_held = 0 ===")
    for p in players:
        choice = pick_next_task(p, meetings_held=0)
        if choice is None:
            print(f"{p.name} ({p.task_strategy}): ROAM (no task picked)")
        else:
            t = p.task_list[choice]
            print(f"{p.name} ({p.task_strategy}): task #{choice} -> {t.coord} ({t.duration}s)")

    print("\n=== meetings_held = 1 ===")
    for p in players:
        choice = pick_next_task(p, meetings_held=1)
        if choice is None:
            print(f"{p.name} ({p.task_strategy}): ROAM (no task picked)")
        else:
            t = p.task_list[choice]
            print(f"{p.name} ({p.task_strategy}): task #{choice} -> {t.coord} ({t.duration}s)")