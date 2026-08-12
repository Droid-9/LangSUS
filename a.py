import json, time
from rich.live import Live
from rich.text import Text
from rich.console import Console

with open('SKLED.txt', encoding='utf-8') as f:
    grid = [list(l.rstrip('\n')) for l in f]
with open('paths.json') as f:
    pdata = json.load(f)

paths = pdata['paths']
max_len = max(len(p) for p in paths.values())

PLAYER_COLOR = {
    "Red": "red", "Blue": "blue", "Cyan": "cyan",
    "White": "white", "Black": "grey50", "Lime": "green",
}

bodies_data = pdata.get("bodies", [])

def render_frame(tick):
    occupied = {}
    for name, path in paths.items():
        idx = min(tick, len(path) - 1)
        x, y, alive = path[idx]
        occupied[(x, y)] = (name, alive)

    body_cells = set()
    for b in bodies_data:
        if tick >= b["death_tick"] and (b["found_tick"] is None or tick < b["found_tick"]):
            body_cells.add((b["x"], b["y"]))

    out = Text()
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if (x, y) in occupied:
                name, alive = occupied[(x, y)]
                symbol = "@" if alive else "&"
                out.append(symbol, style=f"bold {PLAYER_COLOR[name]}")
            elif (x, y) in body_cells:
                out.append("X", style="bold red")
            elif ch == '×':
                out.append("#", style="grey37")
            elif ch == '#':
                out.append("!", style="bold yellow")
            elif ch == '0':
                out.append("+", style="bold magenta")
            else:
                out.append(" ")
        out.append("\n")
    return out

console = Console()
with Live(render_frame(0), console=console, refresh_per_second=12, screen=False) as live:
    for tick in range(max_len):
        live.update(render_frame(tick))
        time.sleep(0.15)