from dataclasses import dataclass, field
from mapdata import get_room

@dataclass
class Task:
    coord: tuple
    duration: int
    done: bool = False
    is_fake: bool = False   # True for impostor "tasks" - real cover, never counts toward crew win

@dataclass
class Player:
    name : str
    role : str
    x : int
    y : int
    current_room : str = None
    previous_room : str = None
    alive : bool = True
    can_act : bool = True
    observation_log: list = field(default_factory=list)
    times_reported: int = 0   # how many bodies THIS player has reported - raw data for discussion, never judged by Python

    def __post_init__(self):
        self.current_room = get_room(self.x, self.y)

    task_list : list = field(default_factory=list) #list[Task] , only for crewmates
    task_strategy : str = "nearest" # nearest / farthest / delayed_observer
    current_task_index: int = None    # was 0 - now None means "no active task, roaming"

    state : str = "idle"  # "walking" | "waiting_at_task" | "roaming" | "idle"
    task_timer_remaining : float = 0.0
    path : list = field(default_factory=list)

    vision_radius : int = 3
    kill_cooldown_remaining : float = 0.0 #impostor only , unused for crewmate

SPAWN = (27,4)

players = [
    Player(name="Red",   role="crewmate", x=SPAWN[0], y=SPAWN[1], task_strategy="nearest"),
    Player(name="Blue",  role="crewmate", x=SPAWN[0], y=SPAWN[1], task_strategy="farthest"),
    Player(name="Cyan",  role="crewmate", x=SPAWN[0], y=SPAWN[1], task_strategy="nearest"),
    Player(name="White", role="crewmate", x=SPAWN[0], y=SPAWN[1], task_strategy="delayed_observer"),
    Player(name="Black", role="crewmate", x=SPAWN[0], y=SPAWN[1], task_strategy="farthest"),
    Player(name="Lime",  role="impostor", x=SPAWN[0], y=SPAWN[1], vision_radius=6),
]
