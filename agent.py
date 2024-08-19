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
        self.facing = 'NORTH'
        self.visited = set()
        self.unknown_cells = set()
        self.safe = set()
        self.not_unsafe = set()
        self.tracked_path = []
        self.point = 0
        self.hp = 100
        self.available_hp = 0
        
        for i in range (1, self.grid_size + 1):
            for j in range(1, self.grid_size + 1):
                self.unknown_cells.add((i, j))
        self.update_KB()
    
    def perceive_current_cell(self):
        return self.program.get_cell_info(self.pos).split(' ')
    
    def neighbor_cells(self, x, y):
        neighbors = []
        surroundings = [
            (x+1, y),
            (x-1, y),
            (x, y+1),
            (x, y-1)
        ]
        
        for (i, j) in surroundings:
            if i <= 0 or i > self.grid_size or j <= 0 or j > self.grid_size:
                continue
            neighbors.append((i, j))
            
        return neighbors
    
    def update_KB(self):
        x, y = self.pos
        percepts = self.perceive_current_cell()
        Ps = []
        Ws = []
        PGs = []
        HPs = []
        
        for r, c in self.neighbor_cells(x, y):
            Ps.append(symbols(f'P{r}{c}'))
            Ws.append(symbols(f'W{r}{c}'))
            PGs.append(symbols(f'P_G{r}{c}'))
            HPs.append(symbols(f'H_P{r}{c}'))
        
        # Update KB with inferences based on percepts.
        # Breeze percepts
        
        self.KB = And(self.KB, to_cnf(Equivalent(symbols(f'B{x}{y}'), Or(*Ps)), True))
        if '.B.' in percepts:
            self.KB = And(self.KB, symbols(f'B{x}{y}'))
        else:
            self.KB = And(self.KB, Not(symbols(f'B{x}{y}')))
        
        # Stench percepts
        self.KB = And(self.KB, to_cnf(Equivalent(symbols(f'S{x}{y}'), Or(*Ws)), True))
        if '.S.' in percepts:
            self.KB = And(self.KB, symbols(f'S{x}{y}'))
        else:
            self.KB = And(self.KB, Not(symbols(f'S{x}{y}')))
            
        # Whiff percepts
        self.KB = And(self.KB, to_cnf(Equivalent(symbols(f'W_H{x}{y}'), Or(*PGs)), True))
        self.KB = And(self.KB, to_cnf(Equivalent(Not(symbols(f'W_H{x}{y}')), And(*[Not(PG) for PG in PGs])), True))
        if '.W_H.' in percepts:
            self.KB = And(self.KB, symbols(f'W_H{x}{y}'))
        else:
            self.KB = And(self.KB, Not(symbols(f'W_H{x}{y}')))
        
        # Glow percepts
        self.KB = And(self.KB, to_cnf(Equivalent(symbols(f'G_L{x}{y}'), Or(*HPs)), True))
        self.KB = And(self.KB, to_cnf(Equivalent(Not(symbols(f'G_L{x}{y}')), And(*[Not(HP) for HP in HPs])), True))
        if '.G_L.' in percepts:
            self.KB = And(self.KB, symbols(f'G_L{x}{y}'))
        else:
            self.KB = And(self.KB, Not(symbols(f'G_L{x}{y}')))
        
        if '.P_G.' in percepts:
            self.hp -= 25
            self.program.update_status(self.hp, self.point, self.available_hp)
        else:
            self.KB = And(self.KB, Not(symbols(f'P_G{x}{y}')))
        
        if '.H_P.' in percepts:
            self.KB = And(self.KB, symbols(f'H_P{x}{y}'))
        else:
            self.KB = And(self.KB, Not(symbols(f'H_P{x}{y}')))
        
        if '.W.' in percepts or '.P.' in percepts:
            return self.die()
        # Ensure current cell is safe
        self.KB = And(self.KB, Not(symbols(f'W{x}{y}')), Not(symbols(f'P{x}{y}')))
        
    def turn_left(self, current_direction, action):
        idx = DIRECTIONS.index(current_direction)
        current_direction = DIRECTIONS[(idx - 1) % 4]
        if action:
            self.program.add_action(f"Turning to {current_direction}")
            self.program.move_agent(self.pos, current_direction, 1)
        return current_direction
        
    def turn_right(self, current_direction, action):
        idx = DIRECTIONS.index(current_direction)
        current_direction = DIRECTIONS[(idx + 1) % 4]
        if action:
            self.program.add_action(f"Turning to {current_direction}")
            self.program.move_agent(self.pos, current_direction, 1)
        return current_direction
    
    def opposite_direction(self, direction):
        candidates = {
            'NORTH': 'SOUTH',
            'SOUTH': 'NORTH',
            'EAST': 'WEST',
            'WEST': 'EAST'
        }
        return candidates[direction]

    def align_direction_cost(self, current_direction, desired_direction):
        current_idx = DIRECTIONS.index(current_direction)
        desired_idx = DIRECTIONS.index(desired_direction)
        
        steps_right = (desired_idx - current_idx) % 4
        steps_left = (current_idx - desired_idx) % 4

        cost = 0
        
        if steps_right <= steps_left:
            for _ in range(steps_right):
                current_direction = self.turn_right(current_direction, False)
                cost += 10
        else:
            for _ in range(steps_left):
                current_direction = self.turn_left(current_direction, False)
                cost += 10
        return cost

    def align_direction(self, current_direction, desired_direction):
        current_idx = DIRECTIONS.index(current_direction)
        desired_idx = DIRECTIONS.index(desired_direction)
        
        steps_right = (desired_idx - current_idx) % 4
        steps_left = (current_idx - desired_idx) % 4
        
        if steps_right <= steps_left:
            for _ in range(steps_right):
                current_direction = self.turn_right(current_direction, True)
                self.point -= 10
                self.program.update_status(self.hp, self.point, self.available_hp)
        else:
            for _ in range(steps_left):
                current_direction = self.turn_left(current_direction, True)
                self.point -= 10
                self.program.update_status(self.hp, self.point, self.available_hp)
        return current_direction

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
            self.program.add_action("Move blocked by boundary")
            return 0  
        self.program.add_action(f"Moving to {self.pos}")

        # if 'S' in self.perceive_current_cell():
        #     self.shoot()

        return 10
    
    def shoot(self):
        x, y = self.pos
        
        
    def make_safe_move(self, node):
        x, y = node.state
        possible_moves = [
            ('NORTH', (x+1, y)),
            ('SOUTH', (x-1, y)),
            ('EAST', (x, y+1)),
            ('WEST', (x, y-1))
        ]
        actions = ['climb', 'grab', 'heal', 'move']
        
        not_pit = False
        not_wumpus = False
        not_poison = False
        
        if self.hp <= 50 and self.available_hp > 0:
            self.point -= 10
            self.available_hp -= 1
            self.hp += 25
            self.program.update_status(self.hp, self.point, self.available_hp)
            self.program.add_action(f"Using healing potion")
            return Node((x,y), node, (actions[2], self.facing), 0)
        
        if self.available_hp <= 3 and '.H_P.' in self.perceive_current_cell():
            self.point -= 10
            self.available_hp += 1
            self.program.update_status(self.hp, self.point, self.available_hp)
            self.program.remove_element((x,y), 'H_P')
            self.program.add_action(f"Picking up healing potion at ({x, y})")
            return Node((x,y), node, (actions[1], self.facing), 0)
        
        # Calculate the alignment cost for each possible move
        moves_with_costs = []
        for direction, (r, c) in possible_moves:
            if 1 <= r <= self.grid_size and 1 <= c <= self.grid_size and (r, c) not in self.visited:
                not_pit = self.PL_resolution(Not(symbols(f'P{r}{c}')))
                # Check whether the cell has no wumpus
                not_wumpus = self.PL_resolution(Not(symbols(f'W{r}{c}')))
                # Check whether the cell has poison
                not_poison = self.PL_resolution(Not(symbols(f'P_G{r}{c}')))
                if not_pit and not_wumpus:
                    if not not_poison:
                        self.not_unsafe.add((r, c))
                    if self.hp < 75 and not not_poison:
                        continue
                    alignment_cost = self.align_direction_cost(self.facing, direction)
                    moves_with_costs.append((direction, (r, c), alignment_cost))
                else:
                    self.not_unsafe.add((r, c))
                self.reduced_not_unsafe()
                self.unknown_cells.discard((r, c))

        # Sort the possible moves by alignment cost (fewest turns required)
        moves_with_costs.sort(key=lambda move: move[2])  # Sort by alignment_cost

        for direction, (r, c), alignment_cost in moves_with_costs:
            # Move in the aligned direction
            self.facing = self.align_direction(self.facing, direction) # Update the agent's facing direction
            total_cost = alignment_cost + self.move_forward()
            self.point -= total_cost - alignment_cost
            return Node((r, c), node, (actions[3], direction), total_cost)
        return None

    def is_surrounded_by_unsafe(self, cell):
        x, y = cell
        neighbors = self.neighbor_cells(x, y)
        
        for neighbor in neighbors:
            if neighbor in self.safe or neighbor in self.unknown_cells:
                return False
        return True

    def explore(self):
        frontier = []
        frontier.append(Node(self.start, None, ('move', self.facing), 0))  # (cost, position, direction, path)
        
        while len(frontier) != 0:
            node = frontier.pop()
            self.pos = node.state
            action, self.facing = node.action
            if action == 'move':
                self.program.move_agent(self.pos, self.facing, 1)
                self.program.update_status(self.hp, self.point, self.available_hp)

            self.visited.add(self.pos)
            
            if '.P_G.' in self.perceive_current_cell():
                self.not_unsafe.add(self.pos)
            else:
                self.safe.add(self.pos)
            
            self.unknown_cells.discard(self.pos)
            if self.pos != self.start:
                self.update_KB()

            if '.G.' in self.perceive_current_cell():
                self.program.add_action(f"Gold found at {self.pos}!")
                self.point += 5000
                self.program.update_status(self.hp, self.point, self.available_hp)
                self.program.remove_gold(self.pos)
                                   
            for unknown_cell in list(self.unknown_cells):  # Sử dụng list() để tránh thay đổi tập hợp khi duyệt
                if self.is_surrounded_by_unsafe(unknown_cell):
                    self.not_unsafe.add(unknown_cell)
                    self.unknown_cells.discard(unknown_cell)

            child = self.make_safe_move(node)
            if child:
                frontier.append(child)
                self.visited.add(child.state)
                action, _ = child.action
                if action == 'move':
                    self.tracked_path.append((node.state, self.facing))
            else:
                self.program.add_action("No safe moves left. Backtracking.")
                self.program.add_action("No safe moves left. Checking for inaccessible cells.")
                if not self.unknown_cells:
                    self.program.add_action("No more safe cells to explore. Returning to start.")
                    self.backtrack_to_start()
                    return
                if not self.tracked_path:
                    self.program.add_action("No more positions to backtrack to. Exiting.")
                    print(self.unknown_cells)
                    print(self.safe)
                    print(self.not_unsafe)
                    return None
                pos, direction = self.tracked_path.pop()
                self.facing = self.align_direction(self.facing, self.opposite_direction(direction))
                self.point -= self.move_forward()
                prev_node = Node(pos, node, ('move', self.facing), 0)
                frontier.append(prev_node)

        return None
    
    def reduced_not_unsafe(self):
        cells = self.safe.intersection(self.not_unsafe)
        for cell in cells:
            self.not_unsafe.discard(cell)

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
        self.program.add_action(f"Agent died at position {self.pos}.")

