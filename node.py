class Node:
    def __init__(self, state, parent, action, path_cost):
        self.state = state
        self.parent = parent
        self.action = action
        self.path_cost = path_cost
        
    def __lt__(self, other):
        return self.path_cost < other.path_cost