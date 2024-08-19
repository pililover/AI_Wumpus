class Node:
    def __init__(self, state, parent = None, action = None, path_cost = 0, heuristic = 0):
        self.state = state
        self.parent = parent
        self.action = action
        self.path_cost = path_cost
        self.heuristic = heuristic
        
    def __lt__(self, other):
        return self.path_cost + self.heuristic < other.path_cost + other.heuristic