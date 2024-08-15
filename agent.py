from sympy import symbols, Not, And, Or, Implies, Equivalent
from sympy.logic.boolalg import to_cnf
from sympy.logic.inference import satisfiable
from itertools import combinations
from queue import PriorityQueue
from node import Node
import collections

DIRECTIONS = ['NORTH', 'EAST', 'SOUTH', 'WEST']

class Agent:
    def __init__(self, program):
        self.KB = And()
        self.start = (1, 1)
        self.pos = (1, 1)
        self.program = program
        self.grid_size = program.size
        self.tracked_map = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.facing = 'NORTH'
        self.visited = set()
        self.tracked_path = []
        self.point = 0
        self.wumpus = True
        
        self.update_KB()
    
    def perceive_current_cell(self):
        return self.program.get_cell_info(self.pos)
    
    def infer_surroundings(self, element):
        x, y = self.pos
        surroundings = [
            (x+1, y),
            (x-1, y),
            (x, y+1),
            (x, y-1)
        ]
        
        valid_neighbors = []
        for (i, j) in surroundings:
            if 1 <= i <= self.grid_size and 1 <= j <= self.grid_size:
                valid_neighbors.append((i, j))
                
        return valid_neighbors
    
    def update_KB(self):
        x, y = self.pos
        percepts = self.perceive_current_cell()

        B = symbols(f'B{x}{y}')
        S = symbols(f'S{x}{y}')
        P = symbols(f'P{x}{y}')
        W = symbols(f'W{x}{y}')
        G = symbols(f'G{x}{y}')
        safe = symbols(f'Safe{x}{y}')
        danger = symbols(f'Danger{x}{y}')

        neighbors = self.infer_surroundings('nextTo')

        max_neighbors = 4
        for nx, ny in neighbors:
            self.KB = And(self.KB, Implies(P, Or(*[symbols(f'B{nx}{ny}')])))

        corner = symbols(f'Corner{x}{y}')
        edge = symbols(f'Edge{x}{y}')
        middle = symbols(f'Middle{x}{y}')
        self.KB = And(self.KB, Or(corner, edge, middle))

        self.KB = And(self.KB, Implies(corner, len(neighbors) == 2))
        self.KB = And(self.KB, Implies(edge, len(neighbors) == 3))
        self.KB = And(self.KB, Implies(middle, len(neighbors) == 4))

        self.KB = And(self.KB, Implies(P, Or(*[symbols(f'B{nx}{ny}') for nx, ny in neighbors])))
        self.KB = And(self.KB, Implies(W, Or(*[symbols(f'S{nx}{ny}') for nx, ny in neighbors])))
        self.KB = And(self.KB, Implies(P, danger))
        self.KB = And(self.KB, Implies(W, danger))

        for nx, ny in neighbors:
            self.KB = And(self.KB, Implies(symbols(f'P{nx}{ny}'), B))

        for nx, ny in neighbors:
            self.KB = And(self.KB, Implies(symbols(f'W{nx}{ny}'), S))

        self.KB = And(self.KB, Implies(Not(P) & Not(W), safe))

        self.KB = And(self.KB, Or(safe, danger))

        if 'B' in percepts:
            self.KB = And(self.KB, B)
        else:
            self.KB = And(self.KB, Not(B))

        if 'S' in percepts:
            self.KB = And(self.KB, S)
        else:
            self.KB = And(self.KB, Not(S))

        if 'G' in percepts:
            self.KB = And(self.KB, G)
        else:
            self.KB = And(self.KB, Not(G))

        if 'W' in percepts or 'P' in percepts:
            return self.die()

        self.KB = And(self.KB, Not(W), Not(P))
        
                
    def turn_left(self):
        idx = DIRECTIONS.index(self.facing)
        self.facing = DIRECTIONS[(idx - 1) % 4]
        cost = 10
        print(f"Turning to {self.facing}")
        return cost
        
    def turn_right(self):
        idx = DIRECTIONS.index(self.facing)
        self.facing = DIRECTIONS[(idx + 1) % 4]
        cost = 10
        print(f"Turning to {self.facing}")
        return cost
    
    def turn_around(self):
        cost = 0
        cost = cost + self.turn_right() + self.turn_right()
        return cost    
        
    def move_forward(self):
        x, y = self.pos
        if self.facing == 'NORTH' and x < self.grid_size:
            self.pos = (x+1, y)
        elif self.facing == 'EAST' and y < self.grid_size:
            self.pos = (x, y+1)
        elif self.facing == 'SOUTH' and x > 1:
            self.pos = (x-1, y)
        elif self.facing == 'WEST' and y > 1:
            self.pos = (x, y-1)
        else:
            print("Move blocked by boundary")
            return 0  
        print(f"Moving to {self.pos}")

        if 'S' in self.perceive_current_cell() and self.wumpus:
            self.shoot()

        return 10  
        
    def make_safe_move(self, node):
        x, y = node.state
        possible_moves = [
            ('NORTH', (x+1, y)),
            ('SOUTH', (x-1, y)),
            ('WEST', (x, y-1)),
            ('EAST', (x, y+1))
        ]

        for direction, (r, c) in possible_moves:
            if (0 <= r < self.grid_size and 0 <= c < self.grid_size) and (r, c) not in self.visited:
                is_safe = self.PL_resolution(Not(symbols(f'P{r}{c}'))) and self.PL_resolution(Not(symbols(f'W{r}{c}')))
                print(self.PL_resolution(Not(symbols(f'P{r}{c}'))), self.PL_resolution(Not(symbols(f'W{r}{c}'))))
                if is_safe:
                    cost = node.path_cost + self.align_direction(direction) + self.move_forward()
                    return Node((r, c), node, direction, cost)

        return None
    
    def align_direction(self, desired_direction):
        current_idx = DIRECTIONS.index(self.facing)
        desired_idx = DIRECTIONS.index(desired_direction)
        
        steps_right = (desired_idx - current_idx) % 4
        steps_left = (current_idx - desired_idx) % 4

        cost = 0
        if steps_right <= steps_left:
            for _ in range(steps_right):
                cost += self.turn_right()
        else:
            for _ in range(steps_left):
                cost += self.turn_left()
        return cost

    def explore(self):
        self.visited = set()
        start_pos = self.start
        if self.dfs(start_pos, [start_pos]):
            return True
        else:
            print("No safe path to the gold found.")
            print(f"Final score: {self.point}")
            return False

    def dfs(self, pos, path):
        if 'G' in self.perceive_current_cell():
            print(f"Gold found at {self.pos}!")
            self.point += 5000
            # path = path + [self.pos]
            print(f"Explore: {' -> '.join(map(str, path))}")
            print(f"Final score: {self.point}")
            return True

        self.visited.add(pos)
        self.update_KB()

        directions = ['NORTH', 'WEST', 'EAST', 'SOUTH']
        neighbors = self.get_neighbors(pos)

        for direction in directions:
            neighbor = neighbors.get(direction)
            if neighbor and neighbor not in self.visited and self.is_safe(neighbor):
                self.visited.add(neighbor)
                self.align_direction(direction)
                self.move_forward()
                if self.dfs(neighbor, path + [self.pos]):
                    return True
                self.move_backward()
                self.point -= 10
                self.visited.remove(neighbor)

        return False

    def move_backward(self):
        x, y = self.pos
        if self.facing == 'NORTH' and x > 1:
            self.pos = (x - 1, y)
        elif self.facing == 'EAST' and y > 1:
            self.pos = (x, y - 1)
        elif self.facing == 'SOUTH' and x < self.grid_size:
            self.pos = (x + 1, y)
        elif self.facing == 'WEST' and y < self.grid_size:
            self.pos = (x, y + 1)
        else:
            print("Move blocked by boundary")
            return 0
        print(f"Moving backward to {self.pos}")
        return 10

    def get_neighbors(self, pos):
        x, y = pos
        return {
            'NORTH': (x, y + 1) if y + 1 <= self.grid_size else None,
            'WEST': (x - 1, y) if x - 1 > 0 else None,
            'EAST': (x + 1, y) if x + 1 <= self.grid_size else None,
            'SOUTH': (x, y - 1) if y - 1 > 0 else None
        }

    def is_safe(self, pos):
        cell_info = self.program.get_cell_info(pos)
        return 'W' not in cell_info and 'P' not in cell_info
    
        
    def backtrack_to_start(self):
        # Implement a method to backtrack to the starting position
        pass

    def PL_resolve(self, literal, Ci, Cj):
        clause1 = set(Ci.args if isinstance(Ci, Or) else [Ci])
        clause2 = set(Cj.args if isinstance(Cj, Or) else [Cj])
        clause1.remove(literal)
        clause2.remove(Not(literal))
        if any(Not(other) in clause2 for other in clause1):
            return None

        return clause1.union(clause2)
    
    def PL_resolution(self, query):
        negate_query_cnf = to_cnf(Not(query), True)
        tainted_clauses = set(negate_query_cnf.args if isinstance(negate_query_cnf, Or) else [negate_query_cnf])
        clauses = set(self.KB.args if isinstance(self.KB, And) else [self.KB])
        clauses.update(tainted_clauses)
        new = set()
        
        while True:
            clausesWith = collections.defaultdict(list)
            for clause in clauses:
                if isinstance(clause, Or):
                    for literal in clause.args:
                        clausesWith[literal].append(clause)
                else:
                    clausesWith[clause].append(clause)

            pairs = []
            for Ci in tainted_clauses:
                if isinstance(Ci, Or):
                    for literal in Ci.args:
                        for Cj in clausesWith[Not(literal)]:
                            pairs.append((literal, Ci, Cj))
                else:
                    literal = Ci
                    for Cj in clausesWith[Not(literal)]:
                        pairs.append((literal, Ci, Cj))

            for (literal, Ci, Cj) in pairs:
                resolvent = self.PL_resolve(literal, Ci, Cj)
                if resolvent is not None:
                    if resolvent == set():
                        return True
                    else:
                        new.add(Or(*resolvent))

            added = False
            for clause in new:
                if clause not in clauses:
                    tainted_clauses.add(clause)
                    clauses.add(clause)
                    added = True

            if not added:
                return False

    def die(self):
        print(f"Agent died at position {self.pos}.")
        exit()
        
    def infer_wumpus_position(self):
        for x in range(1, self.grid_size + 1):
            for y in range(1, self.grid_size + 1):
                cell_info = self.program.get_cell_info((x, y))
                if 'W' in cell_info:
                    return (x, y)
        return None

    def shoot(self):
        wumpus_pos = self.infer_wumpus_position()
        if not wumpus_pos:
            return False

        wx, wy = wumpus_pos
        ax, ay = self.pos

        if wx == ax:
            if wy > ay:
                desired_direction = 'EAST'
            else:
                desired_direction = 'WEST'
        elif wy == ay:
            if wx > ax:
                desired_direction = 'NORTH'
            else:
                desired_direction = 'SOUTH'
        else:
            print("Wumpus is not in a straight line from the agent.")
            return False

        self.align_direction(desired_direction)
        print(f"Shooting arrow towards {desired_direction} to hit Wumpus at {wumpus_pos}")

        self.KB = And(self.KB, Not(symbols(f'W{wx}{wy}')))
        self.KB = And(self.KB, symbols(f'Safe{wx}{wy}')) 
        
        self.program.mark_cell_safe((wx, wy))
        self.wumpus = False
        self.pos = (wx, wy)
        
        self.point -= 100
        print(f"Final score: {self.point}")


        return True