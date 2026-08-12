import json
from mapdata import get_room
import random
import mapdata

ALL_ROOMS = sorted(set(mapdata.CELL_TO_ROOM.values()))

def pick_unclaimed_room(already_claimed):
    candidates = [r for r in ALL_ROOMS if r not in already_claimed]
    return random.choice(candidates) if candidates else random.choice(ALL_ROOMS)

def get_last_sighting_in_room(player, room):
    """Most recent entry in this player's observation_log where the sighted
    player was in `room`. Returns the log entry dict, or None if never seen there."""
    for entry in reversed(player.observation_log):
        if entry["room"] == room:
            return entry
    return None

def build_activity_line(player):
    if player.state == "walking" and player.current_task_index is not None:
        task = player.task_list[player.current_task_index]
        return f"working on a task in {get_room(*task.coord)}"

    if player.state == "waiting_at_task" and player.current_task_index is not None:
        remaining = sum(1 for t in player.task_list if not t.done) - 1
        return f"just finished a task in {player.current_room}, {remaining} task(s) left"

    undone = sum(1 for t in player.task_list if not t.done)
    if undone == 0:
        return f"all tasks done, patrolling — was in {player.current_room} when the meeting was called"

    return f"in {player.current_room} when the meeting was called"

def build_phase1_statement(player, body_room, already_claimed_rooms=None):
    if player.role == "impostor" and already_claimed_rooms is not None:
        fake_room = pick_unclaimed_room(already_claimed_rooms)
        print(f"    [DEBUG] {player.name} real room={player.current_room}, faking={fake_room}, claimed_so_far={already_claimed_rooms}")
        activity = f"in {fake_room} when the meeting was called"
    else:
        activity = build_activity_line(player)

    if player.role == "impostor":
        sighting = None
    else:
        sighting = get_last_sighting_in_room(player, body_room)

    if sighting is not None:
        saw_line = f"I last saw {sighting['name']} in {body_room} (tick {sighting['tick']})."
    else:
        saw_line = f"I have no notable sightings to report in {body_room}."

    return f"{player.name}: I was {activity}. {saw_line}"

def build_phase2_prompt(player, public_facts, phase1_statements, cumulative_room_facts):
    role_context = ""
    if player.role == "impostor":
        role_context = (
            "\nYou are the IMPOSTOR. You must lie convincingly and blend in. "
            "Your phase-1 statement may have been a cover story."
        )

    cumulative_text = "\n".join(cumulative_room_facts) or "(nothing carried over from earlier meetings)"

    prompt = f"""You are {player.name}, a player in a social deduction game.

PUBLIC FACTS (everyone knows this):
{chr(10).join(public_facts)}

WHAT EVERYONE JUST SAID (phase 1 - activity + sightings):
{chr(10).join(phase1_statements)}

FACTS CARRIED OVER FROM EARLIER MEETINGS:
{cumulative_text}
{role_context}

IMPORTANT: Base your reasoning ONLY on the facts explicitly listed above.
Do not invent locations, events, movements, or details that are not stated
in the text above. If you don't have enough information to suspect anyone,
say so plainly rather than fabricating a connection.

If two players' statements about their location or sightings MATCH or
CORROBORATE each other (e.g. both say they were in the same room around
the same time), treat that as an alibi supporting both of them — not as
suspicious. Only treat statements as suspicious if they CONTRADICT each
other or leave a gap unaccounted for.

Now reason about who seems suspicious based on everything above.
Give a short statement (1-2 sentences) explaining your reasoning.
If you want to accuse someone specific, name them; otherwise say null.

Respond ONLY with valid JSON, nothing else, in exactly this shape:
{{"statement": "...", "accusation": "<name or null>"}}"""
    return prompt

def build_phase3_prompt(player, public_facts, phase1_statements, phase2_lines, cumulative_room_facts):
    role_context = ""
    if player.role == "impostor":
        role_context = (
        "\nYou are the IMPOSTOR. Do NOT vote for yourself under any circumstances — "
        "that is an instant loss for you, never do it, no matter what anyone said. "
        "Pick a crewmate to vote for instead: choose whoever received the LEAST "
        "suspicion in phase 2, and vote for them, framing them further in your "
        "statement. If everyone suspects you, vote for whichever crewmate seems "
        "safest to blame - never yourself."
    )

    cumulative_text = "\n".join(cumulative_room_facts) or "(nothing carried over from earlier meetings)"

    prompt = f"""You are {player.name}, a player in a social deduction game.
This is the FINAL vote. Discussion is over - everyone has now said their piece.

PUBLIC FACTS:
{chr(10).join(public_facts)}

PHASE 1 - everyone's activity + sightings:
{chr(10).join(phase1_statements)}

PHASE 2 - everyone's reasoning and suspicions (this is the actual discussion,
read it and let it change your mind if it should):
{chr(10).join(phase2_lines)}

FACTS CARRIED OVER FROM EARLIER MEETINGS:
{cumulative_text}
{role_context}

IMPORTANT: Base your vote ONLY on the facts and statements listed above.
You may vote differently than you leaned in phase 2 if the discussion changed
your mind. Vote null to skip if the evidence is too thin to eject anyone.

Respond ONLY with valid JSON, nothing else, in exactly this shape:
{{"statement": "<one short sentence on why you voted this way>", "accusation": "<name or null>"}}"""
    return prompt

def build_public_facts(bodies):
    facts = []
    for b in bodies:
        if b["found"]:
            facts.append(f"{b['victim']}'s body was found in {b['room']} by {b['found_by']}.")
    return facts

def build_prompt(player, public_facts):
    own_sightings = player.observation_log[-10:]
    sightings_text = "\n".join(
        f"- tick {e['tick']}: saw {e['name']} in {e['room']}"
        for e in own_sightings
    ) or "(nothing notable)"

    role_context = ""
    if player.role == "impostor":
        fake_rooms = ", ".join(t.coord.__repr__() for t in player.task_list)
        role_context = (
            "\nYou are the IMPOSTOR. You must lie convincingly and blend in. "
            "You may reference your (fake) task locations as cover if useful."
        )

    prompt = f"""You are {player.name}, a player in a social deduction game.

PUBLIC FACTS (everyone in this meeting knows this):
{chr(10).join(public_facts)}

WHAT YOU PERSONALLY SAW (private to you only):
{sightings_text}
{role_context}

Give a short statement (1-2 sentences) about what you know or suspect.
If you want to accuse someone specific, name them; otherwise say null.

Respond ONLY with valid JSON, nothing else, in exactly this shape:
{{"statement": "...", "accusation": "<name or null>"}}"""
    return prompt

def parse_llm_response(raw_text, valid_names):
    try:
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`").replace("json", "", 1).strip()
        data = json.loads(cleaned)
        statement = str(data.get("statement", "")).strip()
        accusation = data.get("accusation")
        if accusation not in valid_names:
            accusation = None
        if not statement:
            statement = "(no comment)"
        return {"statement": statement, "accusation": accusation, "valid": True}
    except (json.JSONDecodeError, AttributeError, TypeError):
        return {"statement": "(failed to respond clearly)", "accusation": None, "valid": False}

def get_statement(player, public_facts, valid_names, llm_call_fn):
    prompt = build_prompt(player, public_facts)
    raw = llm_call_fn(prompt)
    return parse_llm_response(raw, valid_names)

def run_discussion(all_players, bodies, llm_call_fn, cumulative_room_facts):
    public_facts = build_public_facts(bodies)
    valid_names = [p.name for p in all_players]

    # figure out the body room this meeting is about - the most recently
    # reported body drives the phase-1 "SAW" line
    reported = [b for b in bodies if b["found"]]
    body_room = reported[-1]["room"] if reported else None

    # --- phase 1: deterministic activity + sighting reports, no LLM ---
    phase1_statements = []
    new_room_facts = []
    claimed_rooms = []
    for p in all_players:
        if not p.alive:
            continue
        print(f"  ...phase1 asking {p.name}")
        line = build_phase1_statement(p, body_room, claimed_rooms)
        print(f"  {line}")
        phase1_statements.append(line)

        if p.role != "impostor":
            claimed_rooms.append(p.current_room)
            sighting = get_last_sighting_in_room(p, body_room)
            if sighting is not None:
                new_room_facts.append(
                    f"{p.name} last saw {sighting['name']} in {body_room} (tick {sighting['tick']})."
                )

    cumulative_room_facts.extend(new_room_facts)
    # --- phase 2: LLM reasoning + "leaning" accusation, sees phase-1 output only ---
    # This is discussion, not a vote - nobody has read anyone else's phase-2
    # reasoning yet, so nothing here should ever be tallied directly.
    phase2_results = {}
    for p in all_players:
        if not p.alive:
            continue
        print(f"  ...phase2 asking {p.name} to vote")
        prompt = build_phase2_prompt(p, public_facts, phase1_statements, cumulative_room_facts)
        raw = llm_call_fn(prompt)
        phase2_results[p.name] = parse_llm_response(raw, valid_names)

    phase2_lines = [
        f"{name}: {r['statement']} (leaning toward: {r['accusation'] or 'no one'})"
        for name, r in phase2_results.items()
    ]

    # --- phase 3: separate, later vote - sees the FULL phase-2 discussion first ---
    final_results = {}
    for p in all_players:
        if not p.alive:
            continue
        print(f"  ...phase3 asking {p.name} to vote")
        prompt = build_phase3_prompt(p, public_facts, phase1_statements, phase2_lines, cumulative_room_facts)
        # raw = llm_call_fn(prompt)
        # vote = parse_llm_response(raw, valid_names)
        # final_results[p.name] = {
        #     "statement": phase2_results[p.name]["statement"],
        #     "reasoning_accusation": phase2_results[p.name]["accusation"],
        #     "vote": vote["accusation"],
        #     "vote_reason": vote["statement"],
        #     "valid": phase2_results[p.name]["valid"] and vote["valid"],
        # }
        raw = llm_call_fn(prompt)
        vote = parse_llm_response(raw, valid_names)

        if vote["accusation"] == p.name:
            vote["accusation"] = None
            vote["statement"] += " [self-vote blocked by game rules — converted to skip]"

        final_results[p.name] = {
            "statement": phase2_results[p.name]["statement"],
            "reasoning_accusation": phase2_results[p.name]["accusation"],
            "vote": vote["accusation"],
            "vote_reason": vote["statement"],
            "valid": phase2_results[p.name]["valid"] and vote["valid"],
        }

    return final_results

if __name__ == "__main__":
    from player_state import players
    import assign_tasks  # noqa: F401

    red, blue, cyan, white, black, lime = players

    lime.observation_log = [
        {"tick": 190, "name": "Red", "room": "Corridor (near Security)"},
    ]
    lime.state = "idle"

    print(build_phase1_statement(lime, "Corridor (near Security)"))
    # expect: no mention of Red - impostor suppresses it

    blue.observation_log = [
        {"tick": 190, "name": "Red", "room": "Corridor (near Security)"},
    ]
    blue.state = "idle"
    print(build_phase1_statement(blue, "Corridor (near Security)"))
    # expect: DOES mention Red - crewmate stays truthful