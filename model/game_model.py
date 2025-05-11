from mesa import Model
from mesa.time import SimultaneousActivation
from mesa.space import MultiGrid
from agents.player_agent import PlayerAgent
import random
from utils import find_best_path
from constants import COLORS

class ColoredTrailsModel(Model):
    def __init__(self):
        super().__init__()
        self.grid_width = 7
        self.grid_height = 5
        self.grid = MultiGrid(self.grid_width, self.grid_height, torus=False)
        self.schedule = SimultaneousActivation(self)

        # Define goal position (e.g., bottom-right corner)
        self.goal_pos = (6, 4)

        # Generate grid with random tile colors
        self.tile_colors = {}
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                color = random.choice(COLORS)
                self.tile_colors[(x, y)] = color

        # Place 3 agents — initial positions and tokens are up to you
        self.agents_info = {
            0: {"pos": (0, 0), "tokens": {"green": 1, "yellow": 1, "purple": 2}},
            1: {"pos": (0, 4), "tokens": {"green": 2, "grey": 1}},
            2: {"pos": (3, 2), "tokens": {"purple": 1, "yellow": 2, "grey": 1}}
        }

        for agent_id, info in self.agents_info.items():
            agent = PlayerAgent(agent_id, self)
            agent.tokens = info["tokens"]
            self.grid.place_agent(agent, info["pos"])
            self.schedule.add(agent)

    def step(self):
        for agent in self.schedule.agents:
            agent.needs = {}

        self.schedule.step()    # Agents decide on paths and exchange requests
        self.schedule.advance() # Agents make exchanges and move

        # End conditions
        blocked_agents = [a for a in self.schedule.agents if a.blocked_steps >= 3]
        if any(a.goal_reached for a in self.schedule.agents) or blocked_agents:
            self.running = False
    
    def get_score(self):
        if self.goal_reached:
            return 100 + sum(5 * amt for amt in self.tokens.values())
        else:
            # Estimate path length remaining
            path = find_best_path(self.pos, self.model.goal_pos, self.tokens, self.model.tile_colors)
            tiles_remaining = len(path) - 1 if path else 7  # max penalty
            return sum(5 * amt for amt in self.tokens.values()) - (10 * tiles_remaining)


