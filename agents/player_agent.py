from mesa import Agent
from utils import find_best_path, compute_token_needs

class PlayerAgent(Agent):
    def __init__(self, unique_id, intial_position, intial_tokens, model):
        super().__init__(unique_id, intial_position, intial_tokens, model)
        self.tokens = intial_tokens
        self.blocked_steps = 0
        self.goal_reached = False
        self.pos = intial_position 
        self.needs = {}

    def step(self):
        if self.goal_reached or self.blocked_steps >= 3:
            return

        path = find_best_path(self.pos, self.model.goal_pos, self.model.grid)
        self.needs = compute_token_needs(path, self.tokens, self.model)
        self.model.broadcast_needs(self.unique_id, self.needs)
        self.path_to_goal = path        
            

    def trade(self):
        required_tokens = self.needs

        excess_tokens = {}
        for color, qty in self.tokens.items():
            required = required_tokens.get(color, 0)
            if qty > required:
                excess_tokens[color] = qty - required

        for other_id, other_needs in self.model.needs_pool.items():
            if other_id == self.unique_id:
                continue 

            for color, needed_qty in other_needs.items():
                offer_amount = min(needed_qty, excess_tokens.get(color, 0))
                if offer_amount > 0:
                    if other_id not in self.model.offers_pool:
                        self.model.offers_pool[other_id] = {}
                    self.model.offers_pool[other_id][color] = self.model.offers_pool[other_id].get(color, 0) + offer_amount

                    excess_tokens[color] -= offer_amount
                    self.tokens[color] -= offer_amount
    
    def advance(self):
        if self.goal_reached:
            return

        offers = self.model.offers_pool.get(self.unique_id, {})
        for color, amount in offers.items():
            self.tokens[color] = self.tokens.get(color, 0) + amount

        next_tile = self.path_to_goal[1]  
        tile_color = self.model.grid[next_tile[1]][next_tile[0]]  

    
        if self.tokens.get(tile_color, 0) > 0:
            self.tokens[tile_color] -= 1
            self.pos = next_tile
            self.model.grid.place_agent(self, self.pos)
            self.path_to_goal = self.path_to_goal[1:]  
            self.blocked_steps = 0  
        else:
            self.blocked_steps += 1  

        if self.pos == self.model.goal_pos:
            self.goal_reached = True