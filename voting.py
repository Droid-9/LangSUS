from collections import Counter
from mapdata import SPAWN, get_room
from kill import KILL_COOLDOWN

def tally_votes(discussion_results):
    votes = [r["vote"] for r in discussion_results.values() if r["valid"]]
    counts = Counter(v for v in votes if v is not None)
    skips = sum(1 for v in votes if v is None)

    if not counts:
        return None, counts

    top_name, top_count = counts.most_common(1)[0]
    tied = [n for n, c in counts.items() if c == top_count]
    if len(tied) > 1 or skips >= top_count:
        return None, counts
    return top_name, counts

def check_task_win(all_players):
    real_tasks = [t for p in all_players for t in p.task_list if not t.is_fake]
    if real_tasks and all(t.done for t in real_tasks):
        return "crew", "all_tasks_complete"
    return None, None

def check_win_condition(all_players):
    task_winner, task_reason = check_task_win(all_players)
    if task_winner:
        return task_winner, task_reason

    alive_crew = sum(1 for p in all_players if p.alive and p.role == "crewmate")
    alive_impostors = sum(1 for p in all_players if p.alive and p.role == "impostor")

    if alive_impostors == 0:
        return "crew", "impostor_ejected"
    if alive_impostors >= alive_crew:
        return "impostor", "headcount"

    return None, None

def resolve_meeting(all_players, discussion_results, tick):
    ejected_name, vote_counts = tally_votes(discussion_results)
    ejected_player = None

    if ejected_name:
        ejected_player = next(p for p in all_players if p.name == ejected_name)
        ejected_player.alive = False

    winner, reason = check_win_condition(all_players)

    if winner is None:
        for p in all_players:
            if not p.alive:
                continue
            p.x, p.y = SPAWN
            p.current_room = get_room(*SPAWN)
            p.previous_room = None
            p.current_task_index = None
            p.state = "idle"
            p.path = []
            if p.role == "impostor":
                p.kill_cooldown_remaining = KILL_COOLDOWN

    return {"ejected": ejected_name, "vote_counts": dict(vote_counts), "winner": winner, "reason": reason}