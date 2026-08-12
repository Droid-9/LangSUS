import math
from mapdata import is_floor

def distance(p1, p2):
    return math.hypot(p1.x - p2.x, p1.y - p2.y)

def line_of_sight(x0, y0, x1, y1):
    """Bresenham's line between two points. Returns False if any cell along
    the way (excluding the two endpoints themselves) is a wall."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0

    while (x, y) != (x1, y1):
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy
        if (x, y) == (x1, y1):
            break
        if not is_floor(x, y):
            return False  # a wall sits between the two points
    return True

def visible_players(observer, all_players):
    """Every other alive player within observer's vision_radius AND with a
    clear (unblocked by walls) line of sight."""
    seen = []
    for other in all_players:
        if other is observer or not other.alive:
            continue
        if distance(observer, other) > observer.vision_radius:
            continue
        if not line_of_sight(observer.x, observer.y, other.x, other.y):
            continue
        seen.append(other)
    return seen

def log_observations(observer, all_players, tick):
    """One entry per currently-visible player: who, where, when. That's it."""
    for other in visible_players(observer, all_players):
        observer.observation_log.append({
            "tick": tick,
            "name": other.name,
            "room": other.current_room,
        })

if __name__ == "__main__":
    from player_state import players

    red, blue, cyan, white, black, lime = players

    # test 1: same open room, should see each other
    red.x, red.y = 27, 4
    blue.x, blue.y = 29, 4
    log_observations(red, players, tick=0)
    print("Test 1 - same room, clear line of sight:")
    print(f"  Red saw: {red.observation_log}")

    # test 2: wall directly between them at a REAL solid wall cell (6,8) -
    # (5,8) and (7,8) are floor on either side, only 2 apart, well within radius
    red.observation_log.clear()
    red.x, red.y = 5, 8
    cyan.x, cyan.y = 7, 8
    log_observations(red, players, tick=1)
    print("\nTest 2 - wall directly between them (should NOT see Cyan):")
    print(f"  Red saw: {red.observation_log}")
    print(f"  (distance was {distance(red, cyan):.1f}, within radius {red.vision_radius}, wall at (6,8) blocks it)")

    # test 3: same distance, no wall in the way - should see each other, proves
    # test 2 was actually the wall's doing, not just a distance fluke
    red.observation_log.clear()
    red.x, red.y = 21, 4   # open floor in Cafeteria
    cyan.x, cyan.y = 23, 4
    log_observations(red, players, tick=2)
    print("\nTest 3 - same distance, open floor, no wall (should see Cyan):")
    print(f"  Red saw: {red.observation_log}")
    print(f"  (distance was {distance(red, cyan):.1f})")