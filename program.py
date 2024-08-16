import pygame
import sys
import time
import threading
from agent import Agent

class Program:
    def __init__(self, input_file):
        self.map_files = ['map1.txt', 'map2.txt', 'map3.txt', 'map4.txt', 'map5.txt']  # Thêm các file bản đồ
        self.load_map(input_file)
        self.left_width = 250  # Tăng chiều rộng cho cột nút
        pygame.init()
        self.set_screen_size()
        self.button_surface = pygame.Surface((self.left_width, self.height))
        
        pygame.display.set_caption("Wumpus World")
        self.agent_pos = [((1, 1), 'NORTH')]
        self.actions_log = []
        self.step = 0
        self.scroll_y = 0
        self.map_buttons = [pygame.Rect(10, 10 + i * 60, 100, 50) for i in range(5)]  # Tạo các nút chọn bản đồ
        self.control_buttons = {
            'run': pygame.Rect(10, 310, 100, 50),
            'back': pygame.Rect(10, 370, 100, 50),
            'forward': pygame.Rect(10, 430, 100, 50),
        }

        self.running = False
        self.draw_grid()
        self.draw_buttons()
        self.draw_action_log()

    def set_screen_size(self):
        """Thiết lập kích thước màn hình dựa trên kích thước của bản đồ."""
        self.cell_size = 75
        self.width = self.size * self.cell_size + 500  # Additional space for percepts display
        self.height = max(self.size * self.cell_size, 600)  # Chiều cao tối thiểu để hiển thị đầy đủ nút
        self.screen = pygame.display.set_mode((self.width, self.height))

    def load_map(self, input_file):
        self.map, self.size = self.read_map(input_file)
        self.update_percepts()
        self.set_screen_size()  # Cập nhật lại kích thước màn hình khi nạp bản đồ mới

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
                        self.add_percept(i, j, 'W_P')
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
                self.map[nx][ny] += ' ' + percept
                
    def move_agent(self, pos, direction, step):
        time.sleep(0.5) 
        if self.agent_pos[self.step][0] is not None:
            self.clear_agent(self.agent_pos[self.step][0])
        self.agent_pos.append((pos, direction))
        self.step += step
        self.draw_grid()
        self.draw_agent(pos, direction)
        self.show_percepts(pos)
        self.screen.blit(self.button_surface, (0, 0))
        pygame.display.flip()
                        
    def mark_visited(self, pos):
        x, y = pos
        self.map[self.size - x][y - 1] += ' V'
    
    def clear_agent(self, pos):
        x, y = pos
        rect = pygame.Rect(self.left_width + self.cell_size * (y - 1), self.cell_size * (self.size - x), self.cell_size, self.cell_size)
        pygame.draw.rect(self.screen, (255, 255, 255), rect)
        pygame.display.flip()

    def draw_agent(self, pos, direction):
        x, y = pos
        rect = pygame.Rect(self.left_width + self.cell_size * (y - 1), self.cell_size * (self.size - x), self.cell_size, self.cell_size)

        agent_images = {
            'NORTH': pygame.image.load('./assets/agent_north.png'),
            'EAST': pygame.image.load('./assets/agent_east.png'),
            'SOUTH': pygame.image.load('./assets/agent_south.png'),
            'WEST': pygame.image.load('./assets/agent_west.png')
        }

        agent_image = agent_images[direction]
        agent_image = pygame.transform.scale(agent_image, (self.cell_size, self.cell_size))
        self.screen.blit(agent_image, rect.topleft) 
        pygame.display.flip()
        
    def add_action(self, action):
        self.actions_log.append(action)
        self.draw_action_log()

    def draw_action_log(self):
        log_x = self.left_width + self.size * self.cell_size + 10
        log_y = self.height // 2  # Start at the middle of the screen
        log_width = self.width - log_x - 10  # Use the remaining space on the right side
        log_height = self.height // 2 - 10  # Use only the lower half of the screen
        
        font = pygame.font.SysFont(None, 24)
        max_visible_actions = log_height // 30
        start_index = max(0, len(self.actions_log) - max_visible_actions - self.scroll_y)
        end_index = min(len(self.actions_log), start_index + max_visible_actions)

        for index, action in enumerate(self.actions_log[start_index:end_index]):
            action_text = font.render(action, True, (0, 0, 0))
            action_offset_y = log_y + 10 + index * 30
            self.screen.blit(action_text, (log_x + 10, action_offset_y))

        # Draw scroll bar
        if len(self.actions_log) > max_visible_actions:
            scrollbar_height = log_height * max_visible_actions / len(self.actions_log)
            scrollbar_y = log_y + (self.scroll_y / len(self.actions_log)) * log_height
            pygame.draw.rect(self.screen, (150, 150, 150), (log_x + log_width - 15, scrollbar_y, 10, scrollbar_height))
            
        pygame.display.flip()

    def handle_scroll(self, event):
        """Handle scrolling in the action log."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # Scroll up
                if self.scroll_y > 0:
                    self.scroll_y -= 1
            elif event.button == 5:  # Scroll down
                if self.scroll_y < len(self.actions_log) - 1:
                    self.scroll_y += 1
                    
    def draw_buttons(self):
        self.button_surface.fill((255, 255, 255))
        """Draw map selection buttons on the left side of the map."""
        for i, map_button in enumerate(self.map_buttons):
            pygame.draw.rect(self.button_surface, (100, 100, 100), map_button)
            map_text = pygame.font.SysFont(None, 24).render(f'Map {i + 1}', True, (255, 255, 255))
            self.button_surface.blit(map_text, (map_button.x + 10, map_button.y + 15))

        """Draw control buttons below map selection buttons."""
        pygame.draw.rect(self.button_surface, (0, 128, 0), self.control_buttons['run'])  # Green button for "Run"
        pygame.draw.rect(self.button_surface, (0, 0, 128), self.control_buttons['back'])  # Blue button for "Back"
        pygame.draw.rect(self.button_surface, (128, 128, 0), self.control_buttons['forward'])  # Yellow button for "Forward"

        # Draw control button labels
        font = pygame.font.SysFont(None, 24)
        run_text = font.render('Run', True, (255, 255, 255))
        back_text = font.render('Back', True, (255, 255, 255))
        forward_text = font.render('Forward', True, (255, 255, 255))

        self.button_surface.blit(run_text, (self.control_buttons['run'].x + 10, self.control_buttons['run'].y + 15))
        self.button_surface.blit(back_text, (self.control_buttons['back'].x + 10, self.control_buttons['back'].y + 15))
        self.button_surface.blit(forward_text, (self.control_buttons['forward'].x + 10, self.control_buttons['forward'].y + 15))

        self.screen.blit(self.button_surface, (0, 0))
        pygame.display.flip()
        
    def handle_button_click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Handle map selection
            for i, map_button in enumerate(self.map_buttons):
                if map_button.collidepoint(event.pos):
                    self.load_map(self.map_files[i])
                    self.agent_pos = [((1, 1), 'NORTH')]
                    self.actions_log = []
                    self.step = 0
                    self.running = False
                    self.draw_grid()
                    self.draw_action_log()
                    return  # Stop checking other buttons

            # Handle control buttons
            if self.control_buttons['run'].collidepoint(event.pos):
                self.running = True
            elif self.control_buttons['back'].collidepoint(event.pos):
                self.move_agent_back()
            elif self.control_buttons['forward'].collidepoint(event.pos):
                self.move_agent_forward()
                
    def move_agent_back(self):
        if self.step > 0:
            self.move_agent(self.agent_pos[self.step][0], self.agent_pos[self.step][1], -1)
            
    def move_agent_forward(self):
        if self.step < len(self.agent_pos) - 1:
            self.move_agent(self.agent_pos[self.step][0], self.agent_pos[self.step][1], 1)

    def show_percepts(self, pos):
        x, y = pos
        cell_content = self.map[self.size - x][y - 1]

        percepts_count = {}
        elements = cell_content.split(' ')
        
        for element in elements:
            if element in percepts_count:
                percepts_count[element] += 1
            else:
                percepts_count[element] = 1

        object = {
            'W': ('./assets/wumpus.png', 'Wumpus'),
            'P': ('./assets/pit.png', 'Pit'),
            'B': ('./assets/breeze.png', 'Breeze'),
            'S': ('./assets/stench.png', 'Stench'),
            'G': ('./assets/gold.png', 'Gold'),
            'P_G': ('./assets/poisonous_gas.png', 'Poisonous Gas'),
            'H_P': ('/assets/healing_potion.png', 'Healing Potion'),
            'W_P': ('./assets/whiff.png', 'Whiff'),
            'G_L': ('./assets/glow.png', 'Glow'),
            'V': ('./assets/wumpus.png', 'Visited')
        }

        offset_x = self.left_width + self.size * self.cell_size + 10 
        offset_y = 10 
        for percept, count in percepts_count.items():
            if percept in object:
                image = pygame.image.load(object[percept][0])
                image = pygame.transform.scale(image, (50, 50)) 
                text = pygame.font.SysFont(None, 24).render(object[percept][1], True, (0, 0, 0))
                self.screen.blit(text, (offset_x, offset_y + 10))  
                self.screen.blit(image, (offset_x + len(object[percept][1] * 15), offset_y)) 
                count_text = pygame.font.SysFont(None, 24).render(f"x{count}", True, (0, 0, 0))
                self.screen.blit(count_text, (offset_x + 60, offset_y + 10)) 
                offset_y += 60 

        pygame.display.flip()

    def draw_grid(self):
        self.screen.fill((255, 255, 255)) 
        for i in range(self.size):
            for j in range(self.size):
                rect = pygame.Rect(self.left_width + j * self.cell_size, i * self.cell_size, self.cell_size, self.cell_size)
                pygame.draw.rect(self.screen, (0, 0, 0), rect, 1) 
                font = pygame.font.SysFont(None, 30)
                if self.map[i][j] == '-':
                    continue
                text = font.render(self.map[i][j], True, (0, 0, 0))
                self.screen.blit(text, (self.left_width + j * self.cell_size + 5, i * self.cell_size + 5))
                
        self.screen.blit(self.button_surface, (0, 0))
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_button_click(event)
                    self.handle_scroll(event)
            if self.running:
                self.step = 0
                self.actions_log = []
                self.agent_pos = [((1, 1), 'NORTH')]
                self.agent = Agent(self)
                self.agent.explore()
                self.running = False
                self.draw_grid()
                self.draw_agent(self.agent_pos[self.step][0], self.agent_pos[self.step][1])
                self.screen.blit(self.button_surface, (0, 0))
            
            self.show_percepts(self.agent_pos[self.step][0])
            self.draw_action_log()
            pygame.display.update()

            pygame.time.Clock().tick(60)
        pygame.quit()
        sys.exit()

    def get_cell_info(self, pos):
        x, y = pos
        return self.map[self.size - x][y-1]
    
    def print_map(self):
        for row in self.map:
            print(' '.join(row))
            
    def update_cellinfor(self, pos, infor):
        x, y = pos
        self.map[self.size - x][y-1] = infor

    def mark_cell_safe(self, pos):
        self.update_cellinfor(pos,'-')
