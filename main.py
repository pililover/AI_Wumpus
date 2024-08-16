from program import Program
from sympy import symbols, Not, And, Or, Implies, Equivalent
from sympy.logic.boolalg import to_cnf

if __name__ == "__main__":
    input_file = "map2.txt"  # Path to your input file
    program = Program(input_file)
    program.run()  # Launch the Pygame visualization