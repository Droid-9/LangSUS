import random
from mapdata import ALL_FLOOR_CELLS
from player_state import players
import assign_tasks  # noqa: F401 - imported for its side effect (deals tasks to players on import)
from task_selection import pick_next_task
from movement import start_walk, tick_movement
from vision import log_observations, visible_players, distance
from kill import attempt_kill, tick_kill_cooldown, KILL_COOLDOWN, KILL_RANGE, bodies
from meeting import check_for_reports, freeze_for_meeting
from discussion import run_discussion
from voting import resolve_meeting, check_win_condition, check_task_win
from kill import attempt_kill, tick_kill_cooldown, KILL_COOLDOWN, KILL_RANGE, bodies, pick_flee_target


def decide_next_action(player, meetings_held, all_players):
    if player.role == "impostor":
        visible_crewmates = [p for p in visible_players(player, all_players)
                              if p.role == "crewmate" and p.alive]
        if visible_crewmates:
            target = min(visible_crewmates, key=lambda c: distance(player, c))
            if distance(player, target) > KILL_RANGE:
                player.current_task_index = None
                start_walk(player, (target.x, target.y))
                return

    choice = pick_next_task(player, meetings_held)
    if choice is not None:
        player.current_task_index = choice
        target = player.task_list[choice].coord
        start_walk(player, target)
    else:
        player.current_task_index = None
        dest = random.choice(ALL_FLOOR_CELLS)
        if not start_walk(player, dest):
            player.state = "idle"

def run_tick(all_players, dt, tick, meetings_held, phase):
    """Returns the updated phase (may flip 'action' -> 'meeting' this tick)."""

    if phase == "action":
        for p in all_players:
            if not p.can_act:
                continue

            if p.state == "idle":
                decide_next_action(p, meetings_held, all_players)

            if p.state == "walking":
                duration = (p.task_list[p.current_task_index].duration
                            if p.current_task_index is not None else None)
                event = tick_movement(p, dt, task_duration=duration)
                if event == "arrived":
                    p.state = "idle"

            elif p.state == "waiting_at_task":
                event = tick_movement(p, dt)
                if event == "task_done":
                    p.task_list[p.current_task_index].done = True
                    p.current_task_index = None

            log_observations(p, all_players, tick)

        for p in all_players:
            if p.role == "impostor" and p.alive:
                tick_kill_cooldown(p, dt)
                body = attempt_kill(p, all_players, tick)
                if body:
                    flee_target = pick_flee_target(p, body["coord"])
                    if flee_target:
                        p.current_task_index = None
                        start_walk(p, flee_target)

        reported_body = check_for_reports(all_players, bodies, tick)
        if reported_body:
            freeze_for_meeting(all_players)
            phase = "meeting"
            print(f"  [tick {tick}] MEETING CALLED - {reported_body['found_by']} "
                  f"found {reported_body['victim']}'s body in {reported_body['room']}")

    return phase

if __name__ == "__main__":
    from langchain_ollama import ChatOllama

    random.seed(1)
    dt = 0.2
    meetings_held = 0
    cumulative_room_facts = []   # list of "SAW" lines, grows across every meeting, never cleared
    tick = 0
    phase = "action"

    for p in players:
        if p.role == "impostor":
            p.kill_cooldown_remaining = KILL_COOLDOWN

    _llm = ChatOllama(model="mistral:7b", temperature=0.3)
    def real_llm_call(prompt):
        return _llm.invoke(prompt).content

    winner = None
    max_ticks = 5000   # safety cap across multiple rounds/meetings
    replay = {p.name: [] for p in players}
    while tick < max_ticks:
        phase = run_tick(players, dt, tick, meetings_held, phase)
        for p in players:
            replay[p.name].append([p.x, p.y,p.alive])

        if phase == "meeting":
            early_winner, early_reason = check_task_win(players)
            if early_winner:
                winner = early_winner
                print(f"\n  [tick {tick}] WIN CONDITION MET OUTSIDE MEETING - skipping discussion")
                break
            meetings_held += 1
            print(f"\n  -> meetings_held is now {meetings_held}")

            results = run_discussion(players, bodies, real_llm_call, cumulative_room_facts) 
            # NEXT STEP: phase-1 SAW-lines from this meeting get appended to
            # cumulative_room_facts here, once run_discussion returns them.   
            print("=== DISCUSSION ===")
            for name, r in results.items():
                print(f"  {name}: {r['statement']}  (leaning: {r['reasoning_accusation']})")
            print("=== VOTES ===")
            for name, r in results.items():
                print(f"  {name}: votes {r['vote']}  -- \"{r['vote_reason']}\"")

            outcome = resolve_meeting(players, results, tick)
            print(f"\nOutcome: {outcome}\n")

            if outcome["winner"]:
                winner = outcome["winner"]
                break
            phase = "action"   # resume gameplay

        tick += 1

    if winner:
        print(f"\nGAME OVER - {winner} wins!")
    else:
        print(f"\nSimulation hit the {max_ticks}-tick safety cap with no winner.")
    import json
    with open('paths.json', 'w') as f:
        json.dump({
            "paths": replay,
            "bodies": [
                {
                    "x": b["coord"][0],
                    "y": b["coord"][1],
                    "death_tick": b["tick"],
                    "found_tick": b.get("found_tick")   # None if never reported
                }
                for b in bodies
            ]
        }, f)
    print("wrote paths.json (real game replay)")