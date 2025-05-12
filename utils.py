import networkx as nx
from collections import defaultdict

def find_best_path(start_pos, goal_pos, model):
    # Find the shortest path
    G = nx.grid_2d_graph(model.grid_width, model.grid_height)
    return nx.shortest_path(G, source=start_pos, target=goal_pos)


def compute_token_needs(path, current_tokens, game_model):
    needed = defaultdict(int)
    for pos in path:
        color = game_model.tile_colors[pos]
        needed[color] += 1
    for color in current_tokens:
        needed[color] = max(0, needed[color] - current_tokens.get(color, 0))
    return dict(needed)
