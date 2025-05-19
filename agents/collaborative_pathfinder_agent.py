from mesa import Agent
from utils import find_best_path, compute_token_needs
import networkx as nx
from collections import defaultdict, Counter

class CollaborativePathfinderAgent(Agent):
    def __init__(self, unique_id, initial_tokens, model):
        super().__init__(unique_id, model)
        self.tokens = initial_tokens.copy()
        self.blocked_steps = 0
        self.goal_reached = False
        self.needs = {}
        self.agent_id = unique_id
        self.path_to_goal = []
        self.global_token_analysis = {}
        self.altruism_factor = 0.4  # How much to prioritize group vs self
        self.last_path_update = 0
        
    def step(self):
        print(f"[*] Collaborative Pathfinder Agent {self.agent_id} is thinking ------------------------")
        
        if self.goal_reached or self.blocked_steps >= 3:
            return
        
        # Analyze global token economy
        self.analyze_global_token_distribution()
        
        # Find path that minimizes competition for scarce tokens
        self.path_to_goal = self.find_collaborative_path()
        
        # Calculate our token needs based on selected path
        self.needs = compute_token_needs(self.path_to_goal, self.tokens, self.model)
        
        # Broadcast needs to other agents
        self.model.broadcast_needs(self.unique_id, self.needs)
        
        print(f"[*] Agent {self.agent_id} collaborative path: {self.path_to_goal}")
        print(f"[*] Agent {self.agent_id} needs: {self.needs}")
        print(f"[*] Global token analysis: {self.global_token_analysis}")
    
    def advance(self):
        self.collaborative_trade()
        
        if self.goal_reached:
            return
        
        # Process received tokens
        offers = self.model.offers_pool.get(self.unique_id, {})
        for color, amount in offers.items():
            self.tokens[color] = self.tokens.get(color, 0) + amount
        
        # Reconsider path if we're blocked or token economy has changed significantly
        self.last_path_update += 1
        if self.blocked_steps > 0 or self.last_path_update >= 3:
            new_path = self.find_collaborative_path()
            if new_path != self.path_to_goal:
                print(f"[*] Agent {self.agent_id} is adjusting path based on current token economy")
                self.path_to_goal = new_path
                self.needs = compute_token_needs(self.path_to_goal, self.tokens, self.model)
                self.model.broadcast_needs(self.unique_id, self.needs)
                self.last_path_update = 0
        
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
    
    def analyze_global_token_distribution(self):
        """Analyze token distribution and needs across all agents"""
        # Reset analysis
        self.global_token_analysis = {
            'total_available': defaultdict(int),
            'total_needed': defaultdict(int),
            'scarcity_index': defaultdict(float),
            'agent_positions': {},
            'agent_progress': {}
        }
        
        # Collect all available tokens
        for agent in self.model.schedule.agents:
            # Record agent position
            self.global_token_analysis['agent_positions'][agent.unique_id] = agent.pos
            
            # Calculate approximate progress to goal (as percentage of manhattan distance)
            start_dist = abs(self.model.agents_intial_infos[agent.unique_id]['pos'][0] - self.model.goal_pos[0]) + \
                         abs(self.model.agents_intial_infos[agent.unique_id]['pos'][1] - self.model.goal_pos[1])
            current_dist = abs(agent.pos[0] - self.model.goal_pos[0]) + abs(agent.pos[1] - self.model.goal_pos[1])
            if start_dist > 0:
                progress = max(0, (start_dist - current_dist) / start_dist)
            else:
                progress = 1.0
            self.global_token_analysis['agent_progress'][agent.unique_id] = progress
            
            # Sum available tokens
            for color, amount in agent.tokens.items():
                self.global_token_analysis['total_available'][color] += amount
        
        # Calculate all needed tokens from needs pool
        for agent_id, needs in self.model.needs_pool.items():
            for color, amount in needs.items():
                self.global_token_analysis['total_needed'][color] += amount
        
        # Calculate scarcity index (higher means more scarce)
        for color in set(list(self.global_token_analysis['total_available'].keys()) + 
                         list(self.global_token_analysis['total_needed'].keys())):
            available = self.global_token_analysis['total_available'].get(color, 0)
            needed = self.global_token_analysis['total_needed'].get(color, 0)
            
            if needed == 0:
                self.global_token_analysis['scarcity_index'][color] = 0
            elif available == 0:
                self.global_token_analysis['scarcity_index'][color] = 10  # Very scarce
            else:
                self.global_token_analysis['scarcity_index'][color] = needed / available
    
    def find_collaborative_path(self):
        """Find a path that minimizes competition for scarce tokens"""
        G = nx.grid_2d_graph(self.model.grid_width, self.model.grid_height)
        
        # Add edge weights based on tile color scarcity
        for u, v in G.edges():
            # Get color of the destination tile
            dest_color = self.model.tile_colors[v]
            
            # Base weight is 1.0
            weight = 1.0
            
            # Add weight based on scarcity
            scarcity = self.global_token_analysis['scarcity_index'].get(dest_color, 0)
            weight += scarcity * 2
            
            # If we don't have this token, add extra weight
            if dest_color not in self.tokens or self.tokens[dest_color] == 0:
                weight += 3
                
            # Set edge weight
            G[u][v]['weight'] = weight
        
        # Find shortest path with these weights
        try:
            collaborative_path = nx.shortest_path(G, source=self.pos, target=self.model.goal_pos, weight='weight')
            return collaborative_path
        except nx.NetworkXNoPath:
            # Fall back to regular shortest path if no path found
            return find_best_path(self.pos, self.model.goal_pos, self.model)
    
    def collaborative_trade(self):
        print(f"[*] Agent {self.agent_id} is making collaborative trades ---------------------------")
        
        # Determine what we can give without compromising our path
        reservable_tokens = {}
        for color, amount in self.tokens.items():
            needed_for_path = sum(1 for pos in self.path_to_goal if self.model.tile_colors[pos] == color)
            if amount > needed_for_path:
                reservable_tokens[color] = amount - needed_for_path
        
        # Create priority scores for each agent based on:
        # 1. How close they are to the goal
        # 2. How much they need tokens that are scarce
        agent_priority = {}
        for other_id, other_needs in self.model.needs_pool.items():
            if other_id == self.unique_id:
                continue
            
            # Base priority on progress
            progress = self.global_token_analysis['agent_progress'].get(other_id, 0)
            priority = progress * 5  # Agents closer to goal get higher priority
            
            # Adjust for token scarcity needs
            scarcity_factor = 0
            for color, amount in other_needs.items():
                scarcity_factor += self.global_token_analysis['scarcity_index'].get(color, 0) * amount
            
            priority += scarcity_factor
            agent_priority[other_id] = priority
        
        # Sort agents by priority
        prioritized_agents = sorted(agent_priority.items(), key=lambda x: x[1], reverse=True)
        
        # Make offers based on priority
        for other_id, priority in prioritized_agents:
            other_needs = self.model.needs_pool.get(other_id, {})
            for color, needed_amount in other_needs.items():
                if color in reservable_tokens and reservable_tokens[color] > 0:
                    # Determine how much to give
                    scarcity = self.global_token_analysis['scarcity_index'].get(color, 0)
                    
                    # For scarce tokens, be more conservative
                    if scarcity > 1.5:
                        offer_amount = min(needed_amount, reservable_tokens[color] // 2)
                    else:
                        offer_amount = min(needed_amount, reservable_tokens[color])
                    
                    # Make the offer if it's worth it
                    if offer_amount > 0:
                        if other_id not in self.model.offers_pool:
                            self.model.offers_pool[other_id] = {}
                        
                        self.model.offers_pool[other_id][color] = self.model.offers_pool[other_id].get(color, 0) + offer_amount
                        self.tokens[color] -= offer_amount
                        reservable_tokens[color] -= offer_amount
                        
                        print(f"[*] Agent {self.agent_id} offered {offer_amount} {color} tokens to Agent {other_id}")
                        
        # Special case: help agents who are very close to goal even if we need tokens ourselves
        for other_id, progress in self.global_token_analysis['agent_progress'].items():
            if other_id == self.unique_id or progress < 0.7:  # Only help agents very close to goal
                continue
                
            other_needs = self.model.needs_pool.get(other_id, {})
            for color, needed_amount in other_needs.items():
                # Check if we have this token and can spare it
                if color in self.tokens and self.tokens[color] > 0:
                    # Calculate how many we absolutely need
                    my_critical_need = sum(1 for pos in self.path_to_goal[:3] if self.model.tile_colors[pos] == color)
                    
                    # If we have more than our critical need, consider sharing
                    if self.tokens[color] > my_critical_need:
                        altruistic_offer = min(needed_amount, self.tokens[color] - my_critical_need)
                        
                        if altruistic_offer > 0:
                            if other_id not in self.model.offers_pool:
                                self.model.offers_pool[other_id] = {}
                            
                            self.model.offers_pool[other_id][color] = self.model.offers_pool[other_id].get(color, 0) + altruistic_offer
                            self.tokens[color] -= altruistic_offer
                            
                            print(f"[*] Agent {self.agent_id} made altruistic offer of {altruistic_offer} {color} to Agent {other_id}")
        
        print(f"[*] Offers pool after Agent {self.agent_id} traded: {self.model.offers_pool}")