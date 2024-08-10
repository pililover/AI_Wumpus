import pygame
import sys
class Program:
    def __init__(self, input_file):
        self.map, self.size = self.read_map(input_file)
        self.update_percepts()
        self.cell_size = 75
        self.width = self.size * self.cell_size
        self.height = self.size * self.cell_size
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Wumpus World")

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
                        
    def mark_visited(self, pos):
        x, y = pos
        self.map[self.size - x][y - 1] += '.V'

    def add_percept(self, x, y, percept):
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                self.map[nx][ny] += '.' + percept

    def draw_grid(self):
        self.screen.fill((255, 255, 255))  # Màu nền trắng
        for i in range(self.size):
            for j in range(self.size):
                rect = pygame.Rect(j * self.cell_size, i * self.cell_size, self.cell_size, self.cell_size)
                pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)  # Viền đen
                font = pygame.font.SysFont(None, 30)
                if self.map[i][j] == '-':
                    continue
                text = font.render(self.map[i][j], True, (0, 0, 0))
                self.screen.blit(text, (j * self.cell_size + 5, i * self.cell_size + 5))
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            self.draw_grid()
            pygame.time.Clock().tick(60)
        pygame.quit()
        sys.exit()
        
    def get_cell_info(self, pos):
        x, y = pos
        return self.map[self.size - x][y-1]
    
    def print_map(self):
        for row in self.map:
            print(' '.join(row))
# Ví dụ gọi class Program với file đầu vào
# if __name__ == "__main__":
#     input_file = "map1.txt"  # Đường dẫn đến file đầu vào
#     program = Program(input_file)
#     program.run()  # Chạy giao diện Pygame





