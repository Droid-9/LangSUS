import math
import random
from vision import visible_players, distance
from mapdata import ALL_FLOOR_CELLS, bfs_path

KILL_RANGE = 1.5         # much tighter than vision_radius - has to be right next to them
WITNESS_RADIUS = 4       # anyone else this close to the VICTIM counts as a witness
KILL_COOLDOWN = 12.5     # seconds

FLEE_MIN_DISTANCE = 6   # impostor must relocate at least this far after a kill


bodies = []   # module-level list of {victim, room, coord, tick, found} - consumed in step 12

def tick_kill_cooldown(impostor, dt):
    """Call every tick regardless of state - cooldown ticks down independent
    of what the impostor is currently doing."""
    if impostor.kill_cooldown_remaining > 0:
        impostor.kill_cooldown_remaining = max(0.0, impostor.kill_cooldown_remaining - dt)

def count_witnesses(victim, all_players, impostor):
    """Other alive players (not the impostor, not the victim) within
    WITNESS_RADIUS of the victim at the moment of the kill."""
    return [p for p in all_players
            if p.alive and p is not impostor and p is not victim
            and distance(p, victim) <= WITNESS_RADIUS]

def attempt_kill(impostor, all_players, tick):
    """Returns the body record dict if a kill happened, else None.
    Does NOT decide who to blame - that's for the discussion phase later,
    this only records the objective facts: who, where, when."""
    if impostor.kill_cooldown_remaining > 0:
        return None

    candidates = [p for p in visible_players(impostor, all_players)
                  if p.role == "crewmate" and distance(impostor, p) <= KILL_RANGE]
    if not candidates:
        return None

    # prefer the target with the FEWEST witnesses - a real impostor wouldn't
    # pick the riskier kill if a safer one is available
    victim = min(candidates, key=lambda c: len(count_witnesses(c, all_players, impostor)))
    witnesses = count_witnesses(victim, all_players, impostor)

    victim.alive = False
    # can_act stays True on purpose - ghost keeps doing tasks

    body = {
        "victim": victim.name,
        "room": victim.current_room,
        "coord": (victim.x, victim.y),
        "tick": tick,
        "found": False,
        "witness_names": [w.name for w in witnesses],  # ground truth, for validating claims later
        "killer": impostor.name,
    }
    bodies.append(body)

    impostor.kill_cooldown_remaining = KILL_COOLDOWN
    return body

def pick_flee_target(impostor, body_coord):
    """Random reachable floor cell at least FLEE_MIN_DISTANCE from the kill site.
    Returns None if nothing suitable is reachable (rare, but simulation.py must check)."""
    bx, by = body_coord
    candidates = [c for c in ALL_FLOOR_CELLS
                  if math.hypot(c[0] - bx, c[1] - by) >= FLEE_MIN_DISTANCE]
    random.shuffle(candidates)
    for c in candidates:
        if bfs_path((impostor.x, impostor.y), c) is not None:
            return c
    return None

if __name__ == "__main__":
    from player_state import players

    red, blue, cyan, white, black, lime = players
    lime.role = "impostor"  # already is, just being explicit

    print("=== Test 1: lone kill, no witnesses ===")
    lime.x, lime.y = 27, 4
    red.x, red.y = 28, 4       # within KILL_RANGE 1.5
    for p in (blue, cyan, white, black):
        p.x, p.y = 1, 1        # far away, not witnesses

    body = attempt_kill(lime, players, tick=10)
    print(f"kill result: {body}")
    print(f"Red alive={red.alive}, can_act={red.can_act}")
    print(f"Lime cooldown now: {lime.kill_cooldown_remaining}s")

    print("\n=== Test 2: immediate second attempt should fail (cooldown) ===")
    blue.x, blue.y = 2, 1  # move blue into range too
    body2 = attempt_kill(lime, players, tick=11)
    print(f"kill result: {body2}  (should be None - cooldown active)")

    print("\n=== Test 3: kill with a witness present ===")
    for p in players:
        p.alive = True
        p.kill_cooldown_remaining = 0.0
    lime.x, lime.y = 21, 4
    cyan.x, cyan.y = 22, 4      # in kill range
    black.x, black.y = 23, 4    # within WITNESS_RADIUS of cyan
    blue.x, blue.y = 1, 1
    white.x, white.y = 1, 1
    red.x, red.y = 1, 1

    body3 = attempt_kill(lime, players, tick=20)
    print(f"kill result: {body3}")