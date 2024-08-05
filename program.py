class Program:
    def __init__(self, input_file):
        self.map, self.size = self.read_map(input_file)
        self.update_percepts()

    def read_map(self, input_file):
        with open(input_file, 'r') as f:
            size = int(f.readline().strip())
            grid = [['-' for _ in range(size)] for _ in range(size)]
            for i in range(size):
                line = [cell for cell in f.readline().strip().split('.')]
                for j, cell in enumerate(line):
                    if cell != '-':
                        grid[i][j] = cell
        return grid, size

    def update_percepts(self):
        for i in range(self.size):
            for j in range(self.size):
                if self.map[i][j][0] != '-':
                    if 'P_G' in self.map[i][j]:
                        self.add_percept(i, j, 'W')
                    elif 'H_P' in self.map[i][j]:
                        self.add_percept(i, j, 'G_L')
                    elif 'W' in self.map[i][j]:
                        self.add_percept(i, j, 'S')
                    elif 'P' in self.map[i][j]:
                        self.add_percept(i, j, 'B')

    def add_percept(self, x, y, percept):
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                if self.map[nx][ny][0] == '-':
                    self.map[nx][ny] += '.' + percept

    def print_map(self):
        for row in self.map:
            print(' '.join(row))

program = Program('map1.txt')
program.print_map()