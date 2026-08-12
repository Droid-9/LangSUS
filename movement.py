from mapdata import bfs_path, is_floor, get_room

CREWMATE_MOVE_INTERVAL = 0.4   # seconds per cell
IMPOSTOR_MOVE_INTERVAL = 0.3   # faster - "+1 speed"

def move_interval(player):
    return IMPOSTOR_MOVE_INTERVAL if player.role == "impostor" else CREWMATE_MOVE_INTERVAL

def start_walk(player, target_coord):
    """Compute a path to target_coord and put the player into 'walking' state."""
    path = bfs_path((player.x, player.y), target_coord)
    if path is None or len(path) < 2:
        return False  # already there, or unreachable
    player.path = path[1:]   # drop the starting cell, keep only steps still to take
    player.state = "walking"
    player.task_timer_remaining = move_interval(player)  # reused as per-step countdown
    return True

def tick_movement(player, dt, task_duration=None):
    """
    Advance one player by dt seconds. Call this every simulation tick.
    Returns an event string when something notable happens, else None.
    """
    if player.state == "walking":
        player.task_timer_remaining -= dt
        if player.task_timer_remaining <= 0:
            if not player.path:
                return None
            nx, ny = player.path.pop(0)
            if not is_floor(nx, ny):
                return "blocked"  # shouldn't happen, bfs_path only returns floor cells

            player.x, player.y = nx, ny

            # room tracking - only makes sense once we KNOW the new position
            new_room = get_room(nx, ny)
            if new_room != player.current_room:
                player.previous_room = player.current_room
                player.current_room = new_room

            player.task_timer_remaining = move_interval(player)
            if not player.path:
                if task_duration is not None:
                    player.state = "waiting_at_task"
                    player.task_timer_remaining = task_duration
                    return "arrived_at_task"
                else:
                    player.state = "idle"
                    return "arrived"
        return None

    if player.state == "waiting_at_task":
        player.task_timer_remaining -= dt
        if player.task_timer_remaining <= 0:
            player.state = "idle"
            return "task_done"
        return None

    return None  # idle / roaming: no-op here, handled elsewhere