import networkx as nx
from collections import defaultdict

def find_best_path(start_pos, goal_pos, tokens, grid):
    # Build a graph of valid paths based on token availability
    G = nx.grid_2d_graph(grid.width, grid.height)
    for (x, y) in G.nodes:
        tile_color = grid[x][y]
        if tokens.get(tile_color, 0) == 0 and (x, y) != start_pos:
            G.remove_node((x, y))
    try:
        return nx.shortest_path(G, source=start_pos, target=goal_pos)
    except nx.NetworkXNoPath:
        return []

def compute_token_needs(path, current_tokens):
    needed = defaultdict(int)
    for pos in path[1:]:
        color = path[pos]
        needed[color] += 1
    for color in current_tokens:
        needed[color] = max(0, needed[color] - current_tokens.get(color, 0))
    return dict(needed)
