from mesa import Agent
from utils import find_best_path, compute_token_needs

class PlayerAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.tokens = {}
        self.blocked_steps = 0
        self.goal_reached = False
        self.needs = {}

    def step(self):
        if self.goal_reached or self.blocked_steps >= 3:
            return

        path = find_best_path(self.pos, self.model.goal_pos, self.tokens, self.model.tile_colors)
        if not path:
            self.blocked_steps += 1
            self.needs = {}
            return
        else:
            self.blocked_steps = 0
            self.path_to_goal = path

        self.needs = compute_token_needs(path, self.tokens)
        self.model.broadcast_needs(self, self.needs)

    def advance(self):
        # Give tokens to others if it doesn't affect reaching the goal
        for other in self.model.schedule.agents:
            if other == self or not other.needs:
                continue
            for color, amount in other.needs.items():
                if self.tokens.get(color, 0) >= amount:
                    hypothetical_tokens = self.tokens.copy()
                    hypothetical_tokens[color] -= amount
                    if find_best_path(self.pos, self.model.goal_pos, hypothetical_tokens, self.model.tile_colors):
                        self.tokens[color] -= amount
                        other.tokens[color] = other.tokens.get(color, 0) + amount
                        break

        # Try to move forward if path exists
        if hasattr(self, "path_to_goal") and len(self.path_to_goal) > 1:
            next_pos = self.path_to_goal[1]
            tile_color = self.model.tile_colors[next_pos]
            if self.tokens.get(tile_color, 0) > 0:
                self.tokens[tile_color] -= 1
                self.model.grid.move_agent(self, next_pos)
                self.path_to_goal.pop(0)
                if next_pos == self.model.goal_pos:
                    self.goal_reached = True