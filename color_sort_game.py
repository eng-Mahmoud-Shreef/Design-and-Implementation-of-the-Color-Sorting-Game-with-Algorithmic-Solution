import pygame
import random
import threading
from collections import deque
from multiprocessing import Process

# Game parameters
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
CONTAINER_WIDTH = 100
CONTAINER_HEIGHT = 350
BALL_RADIUS = 15
NUM_CONTAINERS = 6
BALLS_PER_CONTAINER = 4
BUTTON_RADIUS = 40
BUTTON_MARGIN = 90
BUTTON_VERTICAL_SPACING = 120
BUTTON_VERTICAL_OFFSET = 30
COLORS = ['red', 'blue', 'green', 'yellow']
COLOR_MAP = {
    'red': (255, 0, 0),
    'blue': (0, 0, 255),
    'green': (0, 255, 0),
    'yellow': (255, 255, 0)
}

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Color Sort Game!")
clock = pygame.time.Clock()

# Initialize Pygame mixer for sound effects
pygame.mixer.init()

# Load sound effects
move_sound = pygame.mixer.Sound("move.wav")
win_sound = pygame.mixer.Sound("win.wav")
click_sound = pygame.mixer.Sound("click.wav")
hidden_click_sound = pygame.mixer.Sound("hidden_click.wav")  # New sound for the hidden button
pygame.mixer.music.load("background_music.mp3")
pygame.mixer.music.play(-1, 0.0)  # Play background music indefinitely

# Adjust the volume of the background music (set it to 30% of the max volume)
pygame.mixer.music.set_volume(0.25)

# Load the background image
background_image = pygame.image.load('background.png')  # Replace with your image file path
background_image = pygame.transform.scale(background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))  # Scale to fit the screen

def draw_gradient_circle(x, y, radius, color_start, color_end, clicked=False):
    """Draws a circular button with a gradient effect from color_start to color_end, with click effect."""
    for i in range(radius):
        blend_ratio = i / radius
        blended_color = (
            int(color_start[0] * (1 - blend_ratio) + color_end[0] * blend_ratio),
            int(color_start[1] * (1 - blend_ratio) + color_end[1] * blend_ratio),
            int(color_start[2] * (1 - blend_ratio) + color_end[2] * blend_ratio),
        )
        if clicked:
            blended_color = tuple(max(0, c - 50) for c in blended_color)
        pygame.draw.circle(screen, blended_color, (x, y), radius - i)

def show_confetti():
    """Show confetti effect after winning."""
    for _ in range(50):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        color = random.choice([(255, 0, 0), (0, 255, 0), (0, 0, 255)])
        pygame.draw.circle(screen, color, (x, y), 5)
    pygame.display.flip()

# Solution window with dynamic height
def display_solution_window(solution):
    pygame.init()

    # Calculate the required height for the solution window based on the number of moves
    line_height = 30  # Height for each line of text
    padding = 100     # Extra space for the title and padding
    window_height = min(800, len(solution) * line_height + padding)  # Cap max height at 800

    solution_screen = pygame.display.set_mode((600, window_height))
    pygame.display.set_caption("Solution")

    # Load and scale the background to match the solution window
    background = pygame.transform.scale(pygame.image.load('background.png'), (600, window_height))
    font = pygame.font.Font(None, 36)
    
    running = True
    while running:
        solution_screen.blit(background, (0, 0))
        title_text = font.render("Full Solution", True, (0, 0, 0))
        solution_screen.blit(title_text, (20, 20))
        
        # Display each move in the solution
        for i, (from_idx, to_idx) in enumerate(solution):
            move_text = font.render(f"{i+1}. Move ball from container {from_idx+1} to container {to_idx+1}", True, (0, 0, 0))
            solution_screen.blit(move_text, (20, 60 + i * line_height))

        # Close the solution window on quit or 'Esc' key
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("Solution window closed.")
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                print("Solution window closed via ESC key.")
                running = False

        pygame.display.flip()
    pygame.quit()

def open_solution_window(solution):
    print("Opening solution window.")
    process = Process(target=display_solution_window, args=(solution,))
    process.start()

class ColorSortGame:
    def __init__(self):
        self.reset_game()
        self.selected_container = None
        self.solution = []
        self.hint_counter = 0
        self.hint_text = ""
        self.hint_button_pressed = False
        self.restart_button_pressed = False
        self.is_solution_ready = False
        self.game_won = False
        self.sound_played = False  # To ensure the win sound plays only once
        self.move_count = 0  # Tracks the number of moves
        self.sound_on = True  # Sound is on by default
        self.sound_button_font = pygame.font.Font(None, 20)  # Smaller font for the button text

        self.button_x = NUM_CONTAINERS * (CONTAINER_WIDTH + 20) + BUTTON_MARGIN
        self.hint_button_y = SCREEN_HEIGHT // 2 - CONTAINER_HEIGHT // 2 + BUTTON_VERTICAL_OFFSET
        self.restart_button_y = self.hint_button_y + BUTTON_VERTICAL_SPACING
        self.sound_button_radius = 22  # Smaller radius for the sound button
        self.sound_button_x = 30  # Closer to the left edge
        self.sound_button_y = SCREEN_HEIGHT - 30  # Closer to the bottom edge
        # Add these two lines to the __init__ method in the ColorSortGame class:
        self.fadeout_started = False  # Flag to track if fade-out has started
        self.fadeout_timer = 0  # Timer to track how long the fade-out has been running
         # Initial volume for fade-out effect
        self.initial_volume = 0.20  # 25% volume for starting music
        self.fadeout_started = False  # Flag to track if fade-out has started
        self.fadeout_timer = 0  # Timer to track how long the fade-out has been running
        self.fade_duration = 1500  # 1.5 seconds fade-out duration
        pygame.mixer.music.set_volume(self.initial_volume)  # Set initial volume to 25%



    def reset_game(self):
        print("Resetting game.")
        self.containers = self._generate_containers(randomize_style="random_distribution")
        self.selected_container = None
        self.solution = []
        self.hint_counter = 0
        self.hint_text = ""
        self.is_solution_ready = False
        self.game_won = False
        self.sound_played = False  # Reset the sound flag on game reset
        threading.Thread(target=self.find_solution_from_current_state).start()
        self.move_count = 0  # Reset move counter on game reset

    def _generate_containers(self, randomize_style="random_distribution"):
        print("Generating random containers.")
        ball_pool = []
        for color in COLORS:
            ball_pool.extend([color] * BALLS_PER_CONTAINER)
        random.shuffle(ball_pool)
        containers = []
        for _ in range(NUM_CONTAINERS - 2):
            container = deque(ball_pool[:BALLS_PER_CONTAINER])
            ball_pool = ball_pool[BALLS_PER_CONTAINER:]
            containers.append(container)
        containers.append(deque())
        containers.append(deque())
        random.shuffle(containers)
        return containers

    def draw(self):
        screen.blit(background_image, (0, 0))

        title_font = pygame.font.Font(None, 50)
        title_text = title_font.render("Color Sort Game", True, (50, 50, 50))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        screen.blit(title_text, title_rect)

        for i, container in enumerate(self.containers):
            x = i * (CONTAINER_WIDTH + 20) + 50
            y = SCREEN_HEIGHT // 2 - CONTAINER_HEIGHT // 2

            if self.selected_container == i:
                pygame.draw.rect(screen, (211, 211, 211), (x, y, CONTAINER_WIDTH, CONTAINER_HEIGHT))
            else:
                pygame.draw.rect(screen, (255, 255, 255), (x, y, CONTAINER_WIDTH, CONTAINER_HEIGHT))

            pygame.draw.rect(screen, (0, 0, 0), (x, y, CONTAINER_WIDTH, CONTAINER_HEIGHT), 2)

            for j, color in enumerate(container):
                color_rgb = COLOR_MAP[color]
                ball_x = x + CONTAINER_WIDTH // 2
                ball_y = y + CONTAINER_HEIGHT - (j + 1) * ((CONTAINER_HEIGHT - 20) // BALLS_PER_CONTAINER) + BALL_RADIUS
                pygame.draw.circle(screen, color_rgb, (ball_x, ball_y), BALL_RADIUS)

        hint_button_color_start = (100, 100, 255)
        hint_button_color_end = (50, 50, 255)
        draw_gradient_circle(self.button_x, self.hint_button_y, BUTTON_RADIUS, hint_button_color_start, hint_button_color_end, clicked=self.hint_button_pressed)
        font = pygame.font.Font(None, 30)
        text = font.render("Hint", True, (255, 255, 255))
        screen.blit(text, (self.button_x - 20, self.hint_button_y - 10))

        restart_button_color_start = (100, 200, 100)
        restart_button_color_end = (50, 180, 50)
        draw_gradient_circle(self.button_x, self.restart_button_y, BUTTON_RADIUS, restart_button_color_start, restart_button_color_end, clicked=self.restart_button_pressed)
        text = font.render("Restart", True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.button_x, self.restart_button_y))
        screen.blit(text, text_rect)

        # Draw the Sound toggle button
        sound_button_color_start = (200, 100, 100) if self.sound_on else (150, 150, 150)
        sound_button_color_end = (150, 50, 50) if self.sound_on else (100, 100, 100)
        draw_gradient_circle(self.sound_button_x, self.sound_button_y, self.sound_button_radius, sound_button_color_start, sound_button_color_end)

        # Draw text inside the sound button
        sound_label = self.sound_button_font.render("Sound", True, (255, 255, 255))
        status_label = self.sound_button_font.render("On" if self.sound_on else "Off", True, (255, 255, 255))
        screen.blit(sound_label, (self.sound_button_x - sound_label.get_width() // 2, self.sound_button_y - 10))
        screen.blit(status_label, (self.sound_button_x - status_label.get_width() // 2, self.sound_button_y + 5))

        if self.game_won:
            self.draw_win_message()
            show_confetti()  # Display confetti after winning

        self.draw_hint()
        self.draw_credit_text()


    def draw_win_message(self):
        if not self.fadeout_started:
            # Start the fade-out process when the game is won
            self.fadeout_started = True
            self.fadeout_timer = pygame.time.get_ticks()

        # Set the fade-out target volume (e.g., 10% of the original volume)
        target_volume = 0.1  # 10% of the original volume
        fade_duration = self.fade_duration  # 1.5 seconds fade-out duration

        elapsed_time = pygame.time.get_ticks() - self.fadeout_timer
        # Calculate the fade-out volume, which gradually goes from the current volume to the target volume
        volume = max(target_volume, self.initial_volume - (elapsed_time / fade_duration) * (self.initial_volume - target_volume))  # Fade from initial_volume to target_volume

        pygame.mixer.music.set_volume(volume)  # Set the background music volume

        font = pygame.font.Font(None, 100)  # Larger font size for emphasis
        colors = [(255, 255, 255), (255, 215, 0)]  # Flash between white and yellow
        current_color = colors[pygame.time.get_ticks() // 500 % 2]  # Toggle color every 500ms for flashing

        # Play win sound once when game_won is set to True
        if not self.sound_played:
            if self.sound_on:
                win_sound.play()
            self.sound_played = True  # Ensure sound only plays once

        win_text = font.render("Good job! You won!", True, current_color)
        text_rect = win_text.get_rect(center=(SCREEN_WIDTH // 2 - 45, SCREEN_HEIGHT // 2))

        background_rect = pygame.Rect(
            50, text_rect.y - 20,
            (CONTAINER_WIDTH + 20) * NUM_CONTAINERS,
            text_rect.height + 40
        )
        pygame.draw.rect(screen, (0, 0, 0, 200), background_rect)  # Semi-transparent background

        screen.blit(win_text, text_rect)

        # After the fade-out duration, keep the music at the target volume without stopping it
        if elapsed_time >= fade_duration:
            # Ensure the volume stays at the target volume (very slight music)
            pygame.mixer.music.set_volume(target_volume)



    def draw_credit_text(self):
        font = pygame.font.Font(None, 24)
        credit_text = font.render("Developed by Eng. Mahmoud Shreef", True, (30, 30, 30))
        credit_rect = credit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20))
        screen.blit(credit_text, credit_rect)

    def handle_button_click(self, x, y):
        if self.button_x - BUTTON_RADIUS < x < self.button_x + BUTTON_RADIUS:
            if self.hint_button_y - BUTTON_RADIUS < y < self.hint_button_y + BUTTON_RADIUS:
                if self.sound_on:
                    click_sound.play()  # Play click sound
                print("Hint button clicked.")
                self.hint_button_pressed = True
                self.provide_hint()
            elif self.restart_button_y - BUTTON_RADIUS < y < self.restart_button_y + BUTTON_RADIUS:
                if self.sound_on:
                    click_sound.play()  # Play click sound
                print("Restart button clicked.")
                self.restart_button_pressed = True
                self.reset_game()
        if (x - self.sound_button_x) ** 2 + (y - self.sound_button_y) ** 2 <= self.sound_button_radius ** 2:
                print("Sound button clicked!")  # Debugging print to confirm button detection
                self.sound_on = not self.sound_on
                if self.sound_on:
                    pygame.mixer.music.unpause()  # Unpause background music when sound is on
                    click_sound.play()  # Play click sound if sound is turned on
                else:
                    pygame.mixer.music.pause()  # Pause the background music when sound is off
                    pygame.mixer.stop()  # Stop all sound effects when sound is off
                print("Sound toggled:", "On" if self.sound_on else "Off")

    def handle_hidden_button_click(self):
        if self.sound_on:
            hidden_click_sound.play()  # Play hidden button click sound
        open_solution_window(self.solution)

    def handle_button_release(self):
        self.hint_button_pressed = False
        self.restart_button_pressed = False

    def select_container(self, index):
        print(f"Container {index + 1} selected.")
        if self.selected_container is None:
            if self.containers[index]:
                self.selected_container = index
        else:
            if self.move_ball(self.selected_container, index):
                self.move_count += 1  # Increment move counter
                if self.sound_on:
                    move_sound.play()  # Play move sound
                print(f"Moved ball from container {self.selected_container + 1} to container {index + 1}.")
                self.selected_container = None
                if self.is_solved([list(container) for container in self.containers]):
                    print("Game won!")
                    self.game_won = True
            elif self.selected_container == index:
                self.selected_container = None

    def move_ball(self, from_idx, to_idx):
        if from_idx == to_idx or not self.containers[from_idx]:
            return False

        if len(self.containers[to_idx]) >= BALLS_PER_CONTAINER:
            return False

        if not self.containers[to_idx] or self.containers[from_idx][-1] == self.containers[to_idx][-1]:
            # Perform the move directly, no animation
            self.containers[to_idx].append(self.containers[from_idx].pop())
            self.move_count += 1  # Increment move counter

            if self.sound_on:
                move_sound.play()  # Play move sound

            return True
        return False

    def is_solved(self, containers):
        for container in containers:
            if len(container) > 0:
                if len(container) != BALLS_PER_CONTAINER or len(set(container)) > 1:
                    return False
        return True

    def provide_hint(self):
        self.solution = []
        self.hint_counter = 0
        self.is_solution_ready = False
        print("Calculating hint...")
        hint_thread = threading.Thread(target=self.find_solution_from_current_state)
        hint_thread.start()
        hint_thread.join()
        if self.is_solution_ready and self.solution:
            if self.hint_counter < len(self.solution):
                move = self.solution[self.hint_counter]
                self.hint_counter += 1
                self.hint_text = f"Hint: What if you try from {move[0] + 1} to {move[1] + 1}?"
                print(self.hint_text)
            else:
                self.hint_text = "No more hints available or solution not found."
        else:
            self.hint_text = "No solution found."
            print(self.hint_text)

    def find_solution_from_current_state(self):
        initial_state = tuple(tuple(container) for container in self.containers)
        queue = deque([(initial_state, [])])
        visited = set()
        visited.add(initial_state)

        while queue:
            state, path = queue.popleft()
            if self.is_solved(state):
                self.solution = path
                self.is_solution_ready = True
                print("Solution found.")
                return
            for i in range(NUM_CONTAINERS):
                for j in range(NUM_CONTAINERS):
                    if i != j:
                        new_state = self.make_move(state, i, j)
                        if new_state and new_state not in visited:
                            visited.add(new_state)
                            queue.append((new_state, path + [(i, j)]))
        self.solution = []
        self.is_solution_ready = False
        print("No solution found.")

    def make_move(self, state, from_idx, to_idx):
        state_copy = [deque(container) for container in state]
        if state_copy[from_idx] and (len(state_copy[to_idx]) < BALLS_PER_CONTAINER):
            if not state_copy[to_idx] or state_copy[from_idx][-1] == state_copy[to_idx][-1]:
                state_copy[to_idx].append(state_copy[from_idx].pop())
                return tuple(tuple(container) for container in state_copy)
        return None

    def draw_hint(self):
        font = pygame.font.Font(None, 36)
        feeling_text = font.render("Feeling stuck? ): Click Hint to get the next move.", True, (0, 0, 0))
        screen.blit(feeling_text, (10, SCREEN_HEIGHT - 120))
        if self.hint_text:
            hint_text = font.render(self.hint_text, True, (0, 0, 0))
            screen.blit(hint_text, (10, SCREEN_HEIGHT - 80))
            
    def draw_move_counter(self):
        font = pygame.font.Font(None, 36)
        
        # Render the "Moves" label
        moves_label = font.render("Moves:", True, (0, 0, 0))
        label_x = self.button_x - 30  # Align with the restart button's x-coordinate
        label_y = self.restart_button_y + BUTTON_RADIUS + 20  # Position below the restart button
        screen.blit(moves_label, (label_x, label_y))
        
        # Render the move count number and center it under the "Moves" label
        move_text = font.render(f"{self.move_count}", True, (0, 0, 0))
        move_text_x = label_x + (moves_label.get_width() - move_text.get_width()) // 2  # Center the number
        move_text_y = label_y + 30  # Position the number directly below the "Moves" label
        screen.blit(move_text, (move_text_x, move_text_y))

game = ColorSortGame()
running = True

while running:
    screen.blit(background_image, (0, 0))
    game.draw()
    game.draw_move_counter()  # Display the move counter
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            print("Game closed.")
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            game.handle_button_click(x, y)
            
            # Check for hidden button area
            if 10 < x < 50 and 10 < y < 50:
                if game.solution:
                    game.handle_hidden_button_click()
                    
            for i in range(NUM_CONTAINERS):
                container_x = i * (CONTAINER_WIDTH + 20) + 50
                container_y = SCREEN_HEIGHT // 2 - CONTAINER_HEIGHT // 2
                if container_x < x < container_x + CONTAINER_WIDTH and container_y < y < container_y + CONTAINER_HEIGHT:
                    game.select_container(i)
                    break
        elif event.type == pygame.MOUSEBUTTONUP:
            game.handle_button_release()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
