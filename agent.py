from sympy import symbols, Not, And, Or, Implies, Equivalent
from sympy.logic.boolalg import to_cnf
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
        
        self.update_KB()
    
    def perceive_current_cell(self):
        return self.program.get_cell_info(self.pos)
    
    def infer_surroundings(self, element):
        x, y = self.pos
        symbols_list = []
        surroundings = [
            (x+1, y),
            (x-1, y),
            (x, y+1),
            (x, y-1)
        ]
        
        for (i, j) in surroundings:
            if i <= 0 or i > self.grid_size or j <= 0 or j > self.grid_size:
                continue
            symbols_list.append(symbols(f'{element}{i}{j}'))
            
        return symbols_list
    
    def update_KB(self):
        x, y = self.pos
        percepts = self.perceive_current_cell()

        # Update KB with inferences based on percepts.
        symbols_list_P = self.infer_surroundings('P')
        right_P = Or(*symbols_list_P)
        cnf = to_cnf(Equivalent(symbols(f'B{x}{y}'), right_P), True)
        self.KB = And(self.KB, cnf)
        if 'B' in percepts:
            self.KB = And(self.KB, symbols(f'B{x}{y}'))
        else:
            self.KB = And(self.KB, Not(symbols(f'B{x}{y}')))
        
        symbols_list_W = self.infer_surroundings('W')
        right_W = Or(*symbols_list_W)
        cnf = to_cnf(Equivalent(symbols(f'S{x}{y}'), right_W), True)
        self.KB = And(self.KB, cnf)
        if 'S' in percepts:
            self.KB = And(self.KB, symbols(f'S{x}{y}'))
        else:
            self.KB = And(self.KB, Not(symbols(f'S{x}{y}')))

        if 'W' in percepts or 'P' in percepts:
            return self.die()

        # Ensure current cell is safe
        self.KB = And(self.KB, Not(symbols(f'W{x}{y}')), Not(symbols(f'P{x}{y}')))
        
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
            self.pos = (x-1,y)
        elif self.facing == 'WEST' and y > 1:
            self.pos = (x, y-1)
        else:
            print("Move blocked by boundary")
            return 0  # No cost if move is blocked
        print(f"Moving to {self.pos}")
        return 10  # Cost of moving forward
        
    def make_safe_move(self, node):
        x, y = node.state
        possible_moves = [
            ('NORTH', (x+1, y)),
            ('SOUTH', (x-1, y)),
            ('WEST', (x, y-1)),
            ('EAST', (x, y+1))
        ]

        for direction, (r, c) in possible_moves:
            if (1 <= r <= self.grid_size and 1 <= c <= self.grid_size) and (r, c) not in self.visited:
                is_safe = self.PL_resolution(Not(symbols(f'P{r}{c}'))) and self.PL_resolution(Not(symbols(f'W{r}{c}')))
                if is_safe:
                    cost = node.path_cost + self.align_direction(direction) + self.move_forward()
                    return Node((r,c), node, direction, cost)

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
        frontier = []
        frontier.append(Node(self.start, None, self.facing, 0))  # (cost, position, direction, path)

        while len(frontier) != 0:
            node = frontier.pop()
            self.pos = node.state
            self.facing = node.action

            self.visited.add(self.pos)
            if self.pos != self.start:
                self.update_KB()

            if 'G' in self.perceive_current_cell():
                print(f"Gold found at {self.pos}!")
                self.point += 5000
                return node  # Returning the path to gold

            child = self.make_safe_move(node)
            if child:
                frontier.append(child)
                self.visited.add(child.state)
                self.tracked_path.append(node.state)
            else:
                print("No safe moves left. Backtracking.")
                if not self.tracked_path:
                    print("No more positions to backtrack to. Exiting.")
                    return None
                pos = self.tracked_path.pop()
                new_cost = node.path_cost + self.turn_around() + self.move_forward()
                prev_node = Node(pos, node, self.facing, new_cost)
                frontier.append(prev_node)

        return None


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
        

