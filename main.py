from program import Program
from agent import Agent
from sympy import symbols, Not, And, Or, Implies, Equivalent
from sympy.logic.boolalg import to_cnf

program = Program('map1.txt')
program.print_map()

agent = Agent(program)

res = agent.explore()
print(res)