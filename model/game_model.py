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
        self.running = False
        self.needs_pool = {}
        self.offers_pool = {}
        # goal position (bottom-right corner)
        self.goal_pos = (6, 4)

        # Generate grid with random tile colors
        self.tile_colors = {}
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                color = random.choice(COLORS)
                self.tile_colors[(x, y)] = color

        # 3 initial agents placements and tokens initialisation
        self.agents_intial_infos = {
            0: {"pos": (0, 0), "tokens": {"green": 1, "yellow": 1, "purple": 2}},
            1: {"pos": (0, 4), "tokens": {"green": 2, "grey": 1}},
            2: {"pos": (3, 2), "tokens": {"purple": 1, "yellow": 2, "grey": 1}}
        }

        for agent_id, info in self.agents_intial_infos.items():
            agent = PlayerAgent(agent_id, info["pos"], info["tokens"], self)
            self.grid.place_agent(agent, info["pos"])
            self.schedule.add(agent)

    def step(self):

        self.schedule.step()    # Agents decide on paths and exchange requests
        # Assigning a random order for negociations
        random_order = random.sample(range(0, len(self.agents_intial_infos)), len(self.agents_intial_infos))
        for agent_id in random_order:
            agent = self.get_agent_by_id(agent_id)
            agent.trade(self.needs_pool, self.offers_pool)
        self.needs_pool.clear()
        self.offers_pool.clear()
        self.schedule.advance() # Agents make exchanges and move

        # End conditions
        blocked_agents = [a for a in self.schedule.agents if a.blocked_steps >= 3]
        if any(a.goal_reached for a in self.schedule.agents) or blocked_agents:
            self.running = False
    

    def broadcast_needs(self, sender_id, needs):
        self.needs_pool[sender_id] = needs

    def get_agent_by_id(self, agent_id):
        for agent in self.schedule.agents:
            if agent.unique_id == agent_id:
                return agent