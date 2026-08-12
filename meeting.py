import math
from mapdata import is_floor
from vision import line_of_sight

GRACE_TICKS = 15   # dt=0.2 -> 3.0 sim-seconds before the killer can self-report
BODY_DISCOVERY_RADIUS = 3

def can_discover(player, body, tick):
    if body["found"]:
        return False
    if body.get("killer") == player.name and (tick - body["tick"]) < GRACE_TICKS:
        return False
    if player.name in body["witness_names"]:
        return True
    bx, by = body["coord"]
    dist = math.hypot(player.x - bx, player.y - by)
    if dist > BODY_DISCOVERY_RADIUS:
        return False
    return line_of_sight(player.x, player.y, bx, by)


def report_body(reporter, body, tick):
    body["found"] = True
    body["found_by"] = reporter.name
    body["found_tick"] = tick
    reporter.times_reported += 1
    return body

def check_for_reports(all_players, bodies, tick):
    for body in bodies:
        if body["found"]:
            continue
        for player in all_players:
            if not player.alive:
                continue
            if can_discover(player, body, tick):
                return report_body(player, body, tick)
    return None

def freeze_for_meeting(all_players):
    for p in all_players:
        if p.alive:
            p.state = "idle"
            p.path = []