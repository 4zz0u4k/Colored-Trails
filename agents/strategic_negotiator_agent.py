from mesa import Agent
from utils import find_best_path, compute_token_needs
import networkx as nx
import random
from collections import defaultdict

class StrategicNegotiatorAgent(Agent):
    def __init__(self, unique_id, initial_tokens, model):
        super().__init__(unique_id, model)
        self.tokens = initial_tokens.copy()
        self.blocked_steps = 0
        self.goal_reached = False
        self.needs = {}
        self.agent_id = unique_id
        self.path_to_goal = []
        self.trade_history = {}  # Keep track of past trades
        self.alternative_paths = []
        self.exploration_chance = 0.2  # Chance to try alternative paths
    
    def step(self):
        print(f"[*] Strategic Negotiator Agent {self.agent_id} is thinking ----------------------------")
        
        if self.goal_reached or self.blocked_steps >= 3:
            return
        
        # Find multiple potential paths
        self.alternative_paths = self.find_multiple_paths()
        
        # Evaluate and select best path based on token availability
        self.path_to_goal = self.select_optimal_path()
        
        # Calculate token needs for chosen path
        self.needs = compute_token_needs(self.path_to_goal, self.tokens, self.model)
        
        # Broadcast needs to other agents
        self.model.broadcast_needs(self.unique_id, self.needs)
        
        print(f"[*] Agent {self.agent_id} selected path: {self.path_to_goal}")
        print(f"[*] Agent {self.agent_id} needs: {self.needs}")
    
    def advance(self):
        self.strategic_trade()
        
        if self.goal_reached:
            return
        
        # Check if we can use tokens from offers
        offers = self.model.offers_pool.get(self.unique_id, {})
        for color, amount in offers.items():
            self.tokens[color] = self.tokens.get(color, 0) + amount
        
        # If current path is blocked, consider alternative paths
        if self.blocked_steps > 0 and random.random() < self.exploration_chance:
            new_path = self.select_optimal_path()
            if new_path != self.path_to_goal:
                print(f"[*] Agent {self.agent_id} is switching paths due to blockage")
                self.path_to_goal = new_path
                self.needs = compute_token_needs(self.path_to_goal, self.tokens, self.model)
                self.model.broadcast_needs(self.unique_id, self.needs)
        
        # Try to move along path
        if len(self.path_to_goal) > 1:
            next_pos = self.path_to_goal[1]
            tile_color = self.model.tile_colors[next_pos]
            
            if self.tokens.get(tile_color, 0) > 0:
                self.tokens[tile_color] -= 1
                self.model.grid.move_agent(self, next_pos)
                self.path_to_goal = self.path_to_goal[1:]
                self.blocked_steps = 0
            else:
                self.blocked_steps += 1
                print(f"[*] Agent {self.agent_id} is blocked! Needs {tile_color} token.")
        
        if self.pos == self.model.goal_pos:
            self.goal_reached = True
            print(f"[*] Agent {self.agent_id} reached the goal!")
    
    def find_multiple_paths(self, max_paths=5):
        """Find multiple potential paths to the goal"""
        G = nx.grid_2d_graph(self.model.grid_width, self.model.grid_height)
        
        try:
            # Get shortest path
            paths = [nx.shortest_path(G, source=self.pos, target=self.model.goal_pos)]
            
            # Try to find alternative paths
            for _ in range(max_paths - 1):
                # Modify graph to discourage using nodes from previous paths
                temp_G = G.copy()
                for path in paths:
                    for node in path[1:-1]:  # Don't modify start and end nodes
                        if temp_G.has_node(node):
                            for neighbor in temp_G.neighbors(node):
                                if temp_G.has_edge(node, neighbor):
                                    # Increase the cost of this edge
                                    temp_G[node][neighbor]['weight'] = 10
                
                # Find new shortest path with modified weights
                try:
                    new_path = nx.shortest_path(temp_G, source=self.pos, 
                                               target=self.model.goal_pos, weight='weight')
                    if new_path not in paths:
                        paths.append(new_path)
                except:
                    break
                    
            return paths
        except nx.NetworkXNoPath:
            return [find_best_path(self.pos, self.model.goal_pos, self.model)]
    
    def select_optimal_path(self):
        """Select the most efficient path based on token requirements"""
        if not self.alternative_paths:
            return find_best_path(self.pos, self.model.goal_pos, self.model)
        
        best_path = None
        best_score = float('inf')
        
        for path in self.alternative_paths:
            # Calculate token needs for this path
            path_needs = compute_token_needs(path, self.tokens, self.model)
            
            # Calculate a score based on path length and token deficiency
            path_score = len(path) * 2  # Base score on length
            
            # Add penalty for each missing token
            for color, amount in path_needs.items():
                path_score += amount * 5  # Missing tokens are expensive
            
            # Check if this path has a better score
            if path_score < best_score:
                best_score = path_score
                best_path = path
        
        return best_path or self.alternative_paths[0]
    
    def strategic_trade(self):
        print(f"[*] Agent {self.agent_id} is strategically trading -----------------------------------")
        
        # Assess what we have in excess vs what we need
        excess_tokens = {}
        for color, qty in self.tokens.items():
            required = self.calculate_total_need(color)
            if qty > required:
                excess_tokens[color] = qty - required
        
        # Analyze other agents' needs and our potential gains
        potential_trades = {}
        for other_id, other_needs in self.model.needs_pool.items():
            if other_id == self.unique_id:
                continue
            
            # Calculate trade value
            can_give = {}
            for color, needed_qty in other_needs.items():
                if color in excess_tokens and excess_tokens[color] > 0:
                    can_give[color] = min(needed_qty, excess_tokens[color])
            
            # Skip if we can't give anything
            if not can_give:
                continue
            
            # Get other agent's excess that matches our needs
            other_agent = self.model.get_agent_by_id(other_id)
            can_receive = {}
            
            # Using our knowledge of others' tokens to estimate what they might give
            if other_agent:
                other_tokens = getattr(other_agent, 'tokens', {})
                for color, needed in self.needs.items():
                    if color in other_tokens and other_tokens.get(color, 0) > self.calculate_other_need(other_agent, color):
                        can_receive[color] = min(needed, other_tokens.get(color, 0) - self.calculate_other_need(other_agent, color))
            
            # Calculate trade score (what we get vs what we give)
            trade_score = sum(can_receive.values()) - 0.7 * sum(can_give.values())
            
            # Adjust based on trade history
            if other_id in self.trade_history:
                trade_score += self.trade_history[other_id] * 0.3
            
            # Save potential trade
            potential_trades[other_id] = {
                'score': trade_score,
                'give': can_give
            }
        
        # Execute trades in order of score
        sorted_trades = sorted(potential_trades.items(), key=lambda x: x[1]['score'], reverse=True)
        for other_id, trade_info in sorted_trades:
            give_tokens = trade_info['give']
            
            # Make the offer
            for color, amount in give_tokens.items():
                if amount > 0 and excess_tokens.get(color, 0) >= amount:
                    # Add to offers pool
                    if other_id not in self.model.offers_pool:
                        self.model.offers_pool[other_id] = {}
                    
                    self.model.offers_pool[other_id][color] = self.model.offers_pool[other_id].get(color, 0) + amount
                    self.tokens[color] -= amount
                    excess_tokens[color] -= amount
                    
                    # Record trade in history
                    if other_id not in self.trade_history:
                        self.trade_history[other_id] = 0
                    self.trade_history[other_id] += 0.5  # Positive adjustment for making an offer
        
        print(f"[*] Offers pool after Agent {self.agent_id} traded: {self.model.offers_pool}")
    
    def calculate_total_need(self, color):
        """Calculate total tokens needed for entire path"""
        count = 0
        for pos in self.path_to_goal:
            if self.model.tile_colors[pos] == color:
                count += 1
        return count
    
    def calculate_other_need(self, other_agent, color):
        """Estimate how many tokens another agent needs"""
        if hasattr(other_agent, 'path_to_goal'):
            return sum(1 for pos in other_agent.path_to_goal if self.model.tile_colors[pos] == color)
        return 0