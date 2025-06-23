import pygame, sys, random, time
from PIL import Image
from datetime import datetime

pygame.init()
pygame.mixer.init()

jump_sound = pygame.mixer.Sound("sound/jump.mp3")
drop_sound = pygame.mixer.Sound("sound/block_thud.mp3")
boom = pygame.mixer.Sound("sound/boom.mp3")
default_image = pygame.image.load("assets/title.png")
title_image = pygame.transform.scale(default_image, (600, 600))
default_image2 = pygame.image.load("assets/title2.png")
title2_image = pygame.transform.scale(default_image2, (200, 50))

frog_print = pygame.image.load("assets/frog_print.png")
frog_print = pygame.transform.rotate(frog_print, 25)
frog_print = pygame.transform.scale(frog_print, (225, 225))

pen = pygame.image.load("assets/pen.png")
pen = pygame.transform.rotate(pen, 10)
pen = pygame.transform.flip(pen, True, False)
pen = pygame.transform.scale(pen, (200, 200))

score_underlay_image = pygame.image.load("assets/metal_underlay.png")
score_underlay_image = pygame.transform.scale(score_underlay_image, (200, 100))  # adjust size as needed

# === CONFIG ===
TILE_SIZE = 40
COLS, ROWS = 10, 20
BLOCK_WIDTH, BLOCK_HEIGHT = COLS * TILE_SIZE, ROWS * TILE_SIZE
PADDING = 50
WIDTH = BLOCK_WIDTH + PADDING * 2 + 200
HEIGHT = BLOCK_HEIGHT + PADDING * 2
target_fps = 60  # Default value
FALL_INTERVAL_NORMAL = 250
FALL_INTERVAL_FAST = FALL_INTERVAL_NORMAL / 10
FONT = "assets/Pixeltype.ttf"
block_style = 0
ANIMATION_SPEED = 0.5  # seconds per frame

background_image = pygame.image.load("assets/background.png")
background = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

background_image_play = pygame.image.load("assets/play_background.png")
background_play = pygame.transform.scale(background_image_play, (WIDTH, HEIGHT))

background_image_over = pygame.image.load("assets/over_background.png")
background_over = pygame.transform.scale(background_image_over, (WIDTH, HEIGHT))

wall_image = pygame.image.load("assets/wall.png")
wall_image = pygame.transform.scale(wall_image, (TILE_SIZE, TILE_SIZE))

# === COLORS ===
WHITE, GRAY, BLACK = (255, 255, 255), (100, 100, 100), (0, 0, 0)
RED, CYAN, YELLOW = (255, 50, 50), (0, 200, 255), (255, 255, 0)
PURPLE, GREEN, ORANGE = (160, 32, 240), (0, 255, 0), (255, 165, 0)
BLUE = (95, 95, 255)

# === TETROMINOES ===
TETROMINOES = {
    'I': ([(0, -1), (0, 0), (0, 1), (0, 2)], CYAN),
    'O': ([(0, 0), (1, 0), (0, 1), (1, 1)], YELLOW),
    'T': ([(0, 0), (-1, 0), (1, 0), (0, 1)], PURPLE),
    'S': ([(0, 0), (1, 0), (0, 1), (-1, 1)], GREEN),
    'Z': ([(0, 0), (-1, 0), (0, 1), (1, 1)], RED),
    'J': ([(0, 0), (-1, 0), (0, 1), (0, 2)], BLUE),
    'L': ([(0, 0), (1, 0), (0, 1), (0, 2)], ORANGE),
}

# === INIT ===
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Squrog Hopper")
clock = pygame.time.Clock()
font, big_font, small_font = pygame.font.Font(FONT, 40), pygame.font.Font(FONT, 75), pygame.font.Font(FONT, 20)
block_rect = pygame.Rect(PADDING, PADDING, BLOCK_WIDTH, BLOCK_HEIGHT)
buffer = 0

# === PLAYER SETUP ===
player = pygame.Rect(block_rect.x + TILE_SIZE * 2, block_rect.y + TILE_SIZE * 7, TILE_SIZE, TILE_SIZE)
player_velocity = pygame.Vector2(0, 0)
GRAVITY, JUMP_POWER, PLAYER_SPEED, MAX_FALL_SPEED = 0.9, -15, 8, 20
jump_counter, jumps, dash = 2, 0, 0
dash_max = 1  # number of dashes allowed before landing
dash_active = False
dash_timer = 0
DASH_DURATION = 100  # milliseconds
DASH_SPEED = 20      # dash distance per frame
dash_trail = []  # list of (image, position, alpha, time left)
DASH_TRAIL_LIFETIME = 150  # m

# Example sprite frame paths (replace with your actual paths)
frog_idle1 = pygame.image.load("player/frog_idle1.png")
frog_idle1 = pygame.transform.scale(frog_idle1, (TILE_SIZE, TILE_SIZE))

frog_idle2 = pygame.image.load("player/frog_idle2.png")
frog_idle2 = pygame.transform.scale(frog_idle2, (TILE_SIZE, TILE_SIZE))

frog_run1 = pygame.image.load("player/frog_run1.png")
frog_run1 = pygame.transform.scale(frog_run1, (TILE_SIZE, TILE_SIZE))

frog_run2 = pygame.image.load("player/frog_run2.png")
frog_run2 = pygame.transform.scale(frog_run2, (TILE_SIZE, TILE_SIZE))

frog_jump = pygame.image.load("player/frog_jump.png")
frog_jump = pygame.transform.scale(frog_jump, (TILE_SIZE, TILE_SIZE))

frog_dash = pygame.image.load("player/frog_dash.png")
frog_dash = pygame.transform.scale(frog_dash, (TILE_SIZE, TILE_SIZE))

idle_frames_paths = [frog_idle1, frog_idle2]
run_frames_paths = [frog_run1, frog_run2]
jump_frames_paths = [frog_jump, frog_jump]
dash_frames_paths = [frog_dash, frog_dash]

# === GAME STATE ===
board = [[None] * COLS for _ in range(ROWS)]
p1score, p2score, p2_timer , paused, player_on_ground = 0, 0, 0, False, False
piece, next_piece, fall_timer, state = None, None, 0, "start"
play_time_ms = 0  # Total milliseconds played

# === MENU OPTIONS ===
menu_options = ["Start Game", "Options"]
restart_options = ["Restart", "Back"]
options_menu = ["Game Stats", "Graphics", "Audio", "Back"]
graphics_options = ["Visuals", "Frame Rate", "Back"]
audio_options = ["Volume", "Track", "Back"]
volume_options = ["Music Volume", "SFX Volume", "Back"]
frame_rate_options = ["FPS: 30", "FPS: 60", "Back"]
track_options = ["Menu_Music", "Gameplay_Music", "Back"]

block_styles = [
    ("Crate", pygame.image.load("assets/crate.png")),
    ("Metal", pygame.image.load("assets/metal_underlay.png")),
    ("Tint", pygame.image.load("assets/wall.png")),
    ("Program Art", pygame.image.load("assets/evil_square.png")),
    ("Frog", pygame.image.load("player/frog_idle1.png")),
    # Add more as needed
]

selected_options = 0

#=== STATS ===
jump_stat = 0
row_stat = 0
high_score = 0
point_total_p1 = 0
point_total_p2 = 0
absolute_point_total = 0

# === MUSIC ===
current_music = None
music_volume = 0.5
sfx_volume = 0.3

pygame.mixer.music.set_volume(music_volume)
jump_sound.set_volume(sfx_volume - 0.15)
drop_sound.set_volume(sfx_volume)
boom.set_volume(sfx_volume + 0.55)

class Tetromino:
    def __init__(self, type_=None):
        self.type, (self.shape, self.color) = (type_, TETROMINOES[type_]) if type_ else random.choice(list(TETROMINOES.items()))
        self.x, self.y, self.rotation = COLS // 2, 0, 0

    def get_blocks(self):
        shape = self.shape
        for _ in range(self.rotation % 4):
            shape = [(-y, x) for x, y in shape]
        return [(self.x + dx, self.y + dy) for dx, dy in shape]

    def move(self, dx, dy):
        self.x += dx; self.y += dy
        if not self.is_valid():
            self.x -= dx; self.y -= dy
            return False
        return True

    def rotate(self):
        self.rotation += 1
        if not self.is_valid(): self.rotation -= 1

    def is_valid(self):
        return all(0 <= x < COLS and y < ROWS and (y < 0 or not board[y][x]) for x, y in self.get_blocks())

    def lock(self):
        global state
        drop_sound.play()
        for x, y in self.get_blocks():
            if 0 <= y < ROWS and 0 <= x < COLS:
                rect = pygame.Rect(block_rect.x + x * TILE_SIZE, block_rect.y + y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if rect.colliderect(player):
                    state = "game_over"
                    return
                board[y][x] = self.color
        if any(board[0][x] for x in range(COLS)):
            state = "game_over"

# Assuming you have pygame imported and initialized, and TILE_SIZE defined

# Load all frames and scale to desired size (e.g., TILE_SIZE x TILE_SIZE * 1.5 for visual height)
idle_frames = idle_frames_paths
run_frames = run_frames_paths
jump_frames = jump_frames_paths
dash_frames = dash_frames_paths

player_anim_state = "idle"  # "idle", "run", or "jump"
player_anim_frames = idle_frames
player_anim_index = 0
player_anim_timer = 0
player_facing_right = True  # To flip sprite if needed
# Rotation state for jump animation
player_rotation_angle = 0
rotation_in_progress = False
rotation_timer = 0
rotation_step_time = 75  # milliseconds per 90° step

def get_block_image():
    style_img = block_styles[block_style % len(block_styles)][1]
    return pygame.transform.scale(style_img, (TILE_SIZE, TILE_SIZE))

def tint_image(image, tint_color):
    tinted = image.copy()
    tint_surface = pygame.Surface(image.get_size()).convert_alpha()
    tint_surface.fill(tint_color)
    tinted.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return tinted

def generate_tinted_blocks():
    base_image = get_block_image()
    return {
        CYAN: tint_image(base_image, CYAN),
        YELLOW: tint_image(base_image, YELLOW),
        PURPLE: tint_image(base_image, PURPLE),
        GREEN: tint_image(base_image, GREEN),
        RED: tint_image(base_image, RED),
        BLUE: tint_image(base_image, BLUE),
        ORANGE: tint_image(base_image, ORANGE),
    }

tinted_blocks = generate_tinted_blocks()

def play_music(filename):
    global current_music
    if current_music != filename:
        pygame.mixer.music.stop()
        pygame.mixer.music.load("sound/" + filename)
        pygame.mixer.music.play(-1)  # loop indefinitely
        current_music = filename

def clear_full_rows():
    global board
    global row_stat
    new_board = [row for row in board if not all(row)]
    cleared = ROWS - len(new_board)
    if cleared > 0:
        boom.play()
    board = [[None] * COLS for _ in range(cleared)] + new_board
    row_stat += cleared
    return cleared

def collide_with_board(rect):
    for y, row in enumerate(board):
        for x, cell in enumerate(row):
            if cell:
                tile_rect = pygame.Rect(block_rect.x + x * TILE_SIZE, block_rect.y + y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if rect.colliderect(tile_rect):
                    return True
    if piece:
        for x, y in piece.get_blocks():
            if y >= 0:
                tile_rect = pygame.Rect(block_rect.x + x * TILE_SIZE, block_rect.y + y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if rect.colliderect(tile_rect):
                    return True
    return False

def move_player(keys, dt):
    global player_on_ground, player_anim_state, player_anim_frames
    global player_anim_index, player_anim_timer, player_facing_right
    global jumps, dash  # track jumps

    dx = (keys[pygame.K_d] - keys[pygame.K_a]) * PLAYER_SPEED
    player.x += dx

    # Keep player inside block_rect horizontally
    if player.left < block_rect.left:
        player.left = block_rect.left
    elif player.right > block_rect.right:
        player.right = block_rect.right

    if collide_with_board(player):
        player.x -= dx

    # Apply gravity and vertical movement
    if not dash_active:
        player_velocity.y = min(player_velocity.y + GRAVITY, MAX_FALL_SPEED)
        player.y += player_velocity.y

    # Check if player is on ground
    player_on_ground = player.bottom >= block_rect.bottom
    if player_on_ground:
        player.bottom = block_rect.bottom
        player_velocity.y = 0
        jumps = 0
        dash = 0

    if collide_with_board(player):
        player.y -= player_velocity.y
        if player_velocity.y > 0:
            player_on_ground = True
        player_velocity.y = 0
        jumps = 0
        dash = 0

    if dx != 0:
        player_facing_right = dx > 0  # Always allow direction change

    if not player_on_ground:
        player_anim_state = "jump"
        player_anim_frames = jump_frames
    else:
        if dx != 0:
            player_anim_state = "run"
            player_anim_frames = run_frames
        else:
            player_anim_state = "idle"
            player_anim_frames = idle_frames

    # Update animation timer
    player_anim_timer += dt
    if player_anim_timer >= ANIMATION_SPEED * 1000:  # convert to ms
        player_anim_timer = 0
        player_anim_index = (player_anim_index + 1) % len(player_anim_frames)

def reset_game():
    global board, p1score, p2score, p2_timer, player, player_velocity, piece, next_piece, fall_timer, paused, play_time_ms
    board = [[None]*COLS for _ in range(ROWS)]
    p1score, p2score, p2_timer, fall_timer, paused, play_time_ms = 0, 0, 0, 0, False, 0
    player.topleft = (block_rect.x + TILE_SIZE * 2, block_rect.y + TILE_SIZE * 7)
    player_velocity.update(0, 0)
    piece, next_piece = Tetromino(), Tetromino()

def draw_board():
    # Draw gray play area
    pygame.draw.rect(screen, GRAY, block_rect)

    # Draw tiled wall background behind grid
    for row in range(ROWS):
        for col in range(COLS):
            x = block_rect.x + col * TILE_SIZE
            y = block_rect.y + row * TILE_SIZE
            screen.blit(wall_image, (x, y))

    # Update and draw dash trail
    for trail in dash_trail[:]:
        trail[2] -= dt  # reduce time
        if trail[2] <= 0:
            dash_trail.remove(trail)
            continue

        trail[3] = int(255 * (trail[2] / DASH_TRAIL_LIFETIME))  # fade alpha
        faded = trail[0].copy()
        faded.set_alpha(trail[3])
        screen.blit(faded, trail[1])

    # # Draw the grid lines over the tiles
    # for c in range(COLS + 1):
    #     x = block_rect.x + c * TILE_SIZE
    #     pygame.draw.line(screen, BLACK, (x, block_rect.y), (x, block_rect.bottom))
    # for r in range(ROWS + 1):
    #     y = block_rect.y + r * TILE_SIZE
    #     pygame.draw.line(screen, BLACK, (block_rect.x, y), (block_rect.right, y))

    # Draw the board blocks
    for y, row in enumerate(board):
        for x, color in enumerate(row):
            if color:
                pos = (block_rect.x + x * TILE_SIZE, block_rect.y + y * TILE_SIZE)
                screen.blit(tinted_blocks[color], pos)

    # Draw active piece
    if piece:
        for x, y in piece.get_blocks():
            if y >= 0:
                pos = (block_rect.x + x * TILE_SIZE, block_rect.y + y * TILE_SIZE)
                screen.blit(tinted_blocks[piece.color], pos)

    # Draw player sprite (centered on player's rect)
    player_image = player_anim_frames[player_anim_index]

    # Flip image if facing left
    if player_facing_right:
        player_image = pygame.transform.flip(player_image, True, False)

    # Apply rotation if in progress
    if rotation_in_progress:
        player_image = pygame.transform.rotate(player_image, -player_rotation_angle)  # Negative = clockwise

    # Position the sprite so its bottom center aligns with the player's rect bottom center
    sprite_rect = player_image.get_rect()
    sprite_rect.midbottom = player.midbottom

    screen.blit(player_image, sprite_rect.topleft)

    # Format play time as MM:SS
    play_seconds = play_time_ms // 1000
    minutes = play_seconds // 60
    seconds = play_seconds % 60
    time_str = f"Time: {minutes:02}:{seconds:02}"
    screen.blit(font.render(time_str, True, WHITE), (block_rect.right + 60, block_rect.top))

    # Draw score underlay background
    underlay_x = block_rect.right + 50
    underlay_y = block_rect.top + 25
    underlay_width = 200
    underlay_height = 100
    screen.blit(score_underlay_image, (underlay_x, underlay_y))

    # Render score texts
    p1_text = font.render(f"P1 Score: {p1score}", True, BLACK)
    p2_text = font.render(f"P2 Score: {p2score}", True, BLACK)

    # Center horizontally inside underlay
    p1_x = underlay_x + (underlay_width - p1_text.get_width()) // 2
    p2_x = underlay_x + (underlay_width - p2_text.get_width()) // 2

    # Vertical placement — one near top, one near bottom
    p1_y = underlay_y + 30
    p2_y = underlay_y + 55

    # Draw scores
    screen.blit(p1_text, (p1_x, p1_y))
    screen.blit(p2_text, (p2_x, p2_y))

    screen.blit(font.render("Next:", True, WHITE), (block_rect.right + 60, block_rect.top + 125))

    # Draw next piece preview centered under the label
    if next_piece:
        shape = next_piece.shape
        for _ in range(next_piece.rotation % 4):
            shape = [(-y, x) for x, y in shape]

        # Calculate bounding box of the shape
        min_x = min(dx for dx, dy in shape)
        max_x = max(dx for dx, dy in shape)
        min_y = min(dy for dx, dy in shape)
        max_y = max(dy for dx, dy in shape)
        width_blocks = max_x - min_x + 1
        height_blocks = max_y - min_y + 1

        # Center the piece under the "Next:" label
        preview_center_x = block_rect.right + 100  # Adjust X-center here as needed
        preview_top_y = block_rect.top + 150      # Y-offset below the label

        for dx, dy in shape:
            x = preview_center_x + (dx - (min_x + width_blocks / 2 - 0.5)) * TILE_SIZE
            y = preview_top_y + (dy - min_y) * TILE_SIZE
            screen.blit(tinted_blocks[next_piece.color], (x, y))

    # Top and bottom rows
    for c in range(COLS + 2):  # +2 to cover both edges
        # Top border tile
        x_top = block_rect.x - TILE_SIZE + c * TILE_SIZE
        y_top = block_rect.y - TILE_SIZE
        screen.blit(get_block_image(), (x_top, y_top))

        # Bottom border tile
        x_bot = x_top
        y_bot = block_rect.bottom + 1
        screen.blit(get_block_image(), (x_bot, y_bot))

    # Left and right columns
    for r in range(ROWS + 2):  # +2 for top and bottom border tiles
        # Left border tile
        x_left = block_rect.x - TILE_SIZE
        y_left = block_rect.y - TILE_SIZE + r * TILE_SIZE
        screen.blit(get_block_image(), (x_left, y_left))

        # Right border tile
        x_right = block_rect.right + 1
        y_right = y_left
        screen.blit(get_block_image(), (x_right, y_right))

    # Draw translucent dark overlay if paused
    if paused:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Black with alpha for transparency
        screen.blit(overlay, (0, 0))

        paused_text = big_font.render("Paused", True, WHITE)
        text_rect = paused_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(paused_text, text_rect)

def draw_centered_text(lines, y_offset=0):
    for i, (text, fnt, color) in enumerate(lines):
        surf = fnt.render(text, True, color)
        screen.blit(surf, ((WIDTH - surf.get_width()) // 2, y_offset + i * 60))

# === MAIN LOOP ===
running = True
while running:
    dt = clock.tick(target_fps)
    keys = pygame.key.get_pressed()
    if state == "play":
        screen.blit(background_play, (0, 0))
    elif state == "game_over":
        screen.blit(background_over, (0, 0))
    else:
        screen.blit(background, (0, 0))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # menu selection
        elif event.type == pygame.KEYDOWN:
            if state == "start":
                if event.key == pygame.K_UP:
                    selected_options = (selected_options - 1) % len(menu_options)
                elif event.key == pygame.K_DOWN:
                    selected_options = (selected_options + 1) % len(menu_options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if menu_options[selected_options] == "Start Game":
                        state = "play"
                        selected_options = 0
                        reset_game()
                    elif menu_options[selected_options] == "Options":
                        state = "options"
                        selected_options = 0
                elif event.key == pygame.K_ESCAPE:
                    running = False

            elif state == "options":
                if event.key == pygame.K_UP:
                    selected_options = (selected_options - 1) % len(options_menu)
                elif event.key == pygame.K_DOWN:
                    selected_options = (selected_options + 1) % len(options_menu)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    selected_item = options_menu[selected_options]
                    if selected_item == "Back":
                        state = "start"
                        selected_options = 0
                    elif selected_item == "Game Stats":
                        state = "game_stats"
                        selected_options = 0
                    elif selected_item == "Graphics":
                        state = "graphics"
                        selected_options = 0
                    elif selected_item == "Audio":
                        state = "audio"
                        selected_options = 0
                elif event.key == pygame.K_ESCAPE:
                    state = "start"
                    selected_options = 0

            # player controls
            elif state == "play":
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif not paused:
                    if event.key == pygame.K_LEFT:
                        piece.move(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        piece.move(1, 0)
                    elif event.key == pygame.K_UP:
                        piece.rotate()
                    elif event.key == pygame.K_w and jumps < jump_counter:
                        player_velocity.y = JUMP_POWER
                        jump_sound.play()
                        jumps += 1
                        jump_stat += 1
                        player_rotation_angle = 0
                        rotation_in_progress = True
                        rotation_timer = 0
                    if event.key == pygame.K_LSHIFT and not dash_active and dash < dash_max:
                        dash_active = True
                        dash_timer = 0
                        dash += 1
                        player_velocity.y = 0  # cancel gravity
                        player_anim_state = "dash"
                        player_anim_frames = dash_frames
                        player_anim_index = 0
                        player_anim_timer = 0

            elif state == "game_over":
                if event.key == pygame.K_UP:
                    selected_options = (selected_options - 1) % len(restart_options)
                elif event.key == pygame.K_DOWN:
                    selected_options = (selected_options + 1) % len(restart_options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    selected_item = restart_options[selected_options]
                    if selected_item == "Restart":
                        state = "play"
                        selected_options = 0
                        reset_game()
                    elif selected_item == "Back":
                        state = "start"
                        selected_options = 0
                elif event.key == pygame.K_ESCAPE:
                    state = "start"
                    selected_options = 0

            elif state == "game_stats":
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                    state = "options"
                    selected_options = 0

            elif state == "graphics":
                if event.key == pygame.K_UP:
                    selected_options = (selected_options - 1) % len(graphics_options)
                elif event.key == pygame.K_DOWN:
                    selected_options = (selected_options + 1) % len(graphics_options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    selected_item = graphics_options[selected_options]
                    if selected_item == "Visuals":
                        state = "visuals"
                        selected_options = 0
                    elif selected_item == "Frame Rate":
                        state = "frame_rate"
                        selected_options = 0
                    elif selected_item == "Back":
                        state = "options"
                        selected_options = 0
                elif event.key == pygame.K_ESCAPE:
                    state = "options"
                    selected_options = 0

            elif state == "audio":
                if event.key == pygame.K_UP:
                    selected_options = (selected_options - 1) % len(audio_options)
                elif event.key == pygame.K_DOWN:
                    selected_options = (selected_options + 1) % len(audio_options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    selected_item = audio_options[selected_options]
                    if selected_item == "Volume":
                        state = "volume"
                        selected_options = 0
                    elif selected_item == "Track":
                        state = "track"
                        selected_options = 0
                    elif selected_item == "Back":
                        state = "options"
                        selected_options = 0
                elif event.key == pygame.K_ESCAPE:
                    state = "options"
                    selected_options = 0

            elif state == "visuals":
                if event.key == pygame.K_UP:
                    selected_options = (selected_options - 1) % len(visuals_options)
                elif event.key == pygame.K_DOWN:
                    selected_options = (selected_options + 1) % len(visuals_options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    selected_item = visuals_options[selected_options]

                    if selected_item.startswith("Block Style:"):
                        block_style = (block_style + 1) % len(block_styles)
                        tinted_blocks = generate_tinted_blocks()

                    elif selected_item == "Back":
                        state = "graphics"
                        selected_options = 0

                elif event.key == pygame.K_ESCAPE:
                    state = "graphics"
                    selected_options = 0

            elif state == "frame_rate":
                if event.key == pygame.K_UP:
                    selected_options = (selected_options - 1) % len(frame_rate_options)
                elif event.key == pygame.K_DOWN:
                    selected_options = (selected_options + 1) % len(frame_rate_options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if frame_rate_options[selected_options] == "FPS: 30":
                        target_fps = 30
                        state = "graphics"
                        selected_options = 0
                    elif frame_rate_options[selected_options] == "FPS: 60":
                        target_fps = 60
                        state = "graphics"
                        selected_options = 0
                    elif frame_rate_options[selected_options] == "Back":
                        state = "graphics"
                        selected_options = 0
                elif event.key == pygame.K_ESCAPE:
                    state = "graphics"
                    selected_options = 0

            elif state == "volume":
                if event.key == pygame.K_UP:
                    selected_options = (selected_options - 1) % len(volume_options)
                elif event.key == pygame.K_DOWN:
                    selected_options = (selected_options + 1) % len(volume_options)
                elif event.key == pygame.K_LEFT:
                    if volume_options[selected_options] == "Music Volume":
                        music_volume = max(0.0, music_volume - 0.1)
                        pygame.mixer.music.set_volume(music_volume)
                    elif volume_options[selected_options] == "SFX Volume":
                        sfx_volume = max(0.0, sfx_volume - 0.1)
                        jump_sound.set_volume(sfx_volume)
                        drop_sound.set_volume(sfx_volume)
                elif event.key == pygame.K_RIGHT:
                    if volume_options[selected_options] == "Music Volume":
                        music_volume = min(1.0, music_volume + 0.1)
                        pygame.mixer.music.set_volume(music_volume)
                    elif volume_options[selected_options] == "SFX Volume":
                        sfx_volume = min(1.0, sfx_volume + 0.1)
                        jump_sound.set_volume(sfx_volume)
                        drop_sound.set_volume(sfx_volume)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if volume_options[selected_options] == "Back":
                        state = "audio"
                        selected_options = 0
                elif event.key == pygame.K_ESCAPE:
                    state = "audio"
                    selected_options = 0

            elif state == "track":
                if event.key == pygame.K_UP:
                    selected_options = (selected_options - 1) % len(track_options)
                elif event.key == pygame.K_DOWN:
                    selected_options = (selected_options + 1) % len(track_options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    selected_item = track_options[selected_options]
                    if selected_item == "Back":
                        state = "audio"
                        selected_options = 0
                    else:
                        # Play the selected track music file here
                        play_music(f"{selected_item.lower()}.mp3")  # example filename format
                elif event.key == pygame.K_ESCAPE:
                    state = "audio"
                    selected_options = 0

    # === Music Management ===
    if state == "play":
        play_music("gameplay_music.mp3")
    elif state == "track":
        # Do nothing here, music plays based on user selection
        pass
    else:
        # For all other states except play and track, play menu music
        play_music("menu_music.mp3")

    # renders menus
    if state == "start":
        title2_rect = title2_image.get_rect(center=(WIDTH // 2, HEIGHT // 6.5))
        screen.blit(title2_image, title2_rect)
        title_rect = title_image.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        screen.blit(title_image, title_rect)

        for i, option in enumerate(menu_options):
            color = WHITE if i == selected_options else GRAY
            prefix = "> " if i == selected_options else "  "
            surf = font.render(prefix + option, True, color)
            screen.blit(surf, ((WIDTH - surf.get_width()) // 2, HEIGHT // 2 + i * 50))

    elif state == "play":
        if not paused:
            move_player(keys, dt)
            play_time_ms += dt
            p2_timer, p2score
            p2_timer += dt
            if p2_timer >= 1500:
                p2score += 1
                point_total_p2 += 1
                absolute_point_total += 1
                p2_timer -= 1500
            fall_timer += dt
            if dash_active:
                dash_timer += dt
                dash_dx = DASH_SPEED if player_facing_right else -DASH_SPEED
                player.x += dash_dx
                # Capture current player image with rotation
                trail_img = player_anim_frames[player_anim_index]
                if player_facing_right:
                    trail_img = pygame.transform.flip(trail_img, True, False)
                if rotation_in_progress:
                    trail_img = pygame.transform.rotate(trail_img, -player_rotation_angle)

                # Copy current sprite and position
                trail_surf = trail_img.copy()
                trail_rect = trail_surf.get_rect()
                trail_rect.midbottom = player.midbottom

                # Add to trail list with alpha and lifetime
                dash_trail.append([trail_surf, trail_rect.topleft, 150, 255])  # (image, position, time left, alpha)

                if collide_with_board(player) or player.left < block_rect.left or player.right > block_rect.right:
                    player.x -= dash_dx  # Cancel dash if blocked

                if dash_timer >= DASH_DURATION:
                    dash_active = False
            interval = FALL_INTERVAL_FAST if keys[pygame.K_DOWN] else FALL_INTERVAL_NORMAL
            if fall_timer > interval:
                if not piece.move(0, 1):
                    piece.lock()
                    if state == "game_over": 
                        continue     
                    buffer += clear_full_rows() * COLS
                    p1score += buffer
                    point_total_p1 += buffer
                    absolute_point_total += buffer
                    buffer = 0
                    piece = next_piece
                    next_piece = Tetromino()
                    if not piece.is_valid():
                        state = "game_over"
                fall_timer = 0
            if rotation_in_progress:
                rotation_timer += dt
                if rotation_timer >= rotation_step_time:
                    rotation_timer = 0
                    player_rotation_angle += 90
                    if player_rotation_angle >= 360:
                        rotation_in_progress = False
                        player_rotation_angle = 0
        draw_board()

    elif state == "game_over":
        if p1score > high_score:
            high_score = p1score
        elif p2score > high_score:
            high_score = p2score

        high_surf = font.render(f"High Score: {high_score}", True, BLACK)
        high_surf = pygame.transform.rotate(high_surf, -5)
        screen.blit(high_surf, ((WIDTH - high_surf.get_width()) // 4.5, HEIGHT // 2 + 160))

        p1_surf = font.render(f"P1 Score: {p1score}", True, BLACK)
        p1_surf = pygame.transform.rotate(p1_surf, -5)
        screen.blit(p1_surf, ((WIDTH - p1_surf.get_width()) // 4.5, HEIGHT // 4 + 65))

        p2_surf = font.render(f"P2 Score: {p2score}", True, BLACK)
        p2_surf = pygame.transform.rotate(p2_surf, -5)
        screen.blit(p2_surf, ((WIDTH - p2_surf.get_width()) // 4.5, HEIGHT // 4 + 125))

        screen.blit(frog_print, (WIDTH // 4 - frog_print.get_width() // 3.5, HEIGHT - 240))

        screen.blit(pen, (WIDTH - (pen.get_width() + 5), HEIGHT - 260))

        now = datetime.now()
        datetime_str = font.render(now.strftime("%d-%m / %H:%M"), True, BLACK)
        datetime_str = pygame.transform.rotate(datetime_str, -5)
        screen.blit(datetime_str, (WIDTH // 5, HEIGHT - 390))

        for i, option in enumerate(restart_options):
            color = BLACK if i == selected_options else GRAY
            prefix = "> " if i == selected_options else "  "
            surf = font.render(prefix + option, True, color)
            surf = pygame.transform.rotate(surf, -5)
            screen.blit(surf, ((WIDTH - surf.get_width()) // 1.5, HEIGHT // 2.75 + i * 50))

    elif state == "options":
        draw_centered_text([
            ("Options", big_font, WHITE)
        ], HEIGHT // 4)

        for i, option in enumerate(options_menu):
            color = WHITE if i == selected_options else GRAY
            prefix = "> " if i == selected_options else "  "
            surf = font.render(prefix + option, True, color)
            screen.blit(surf, ((WIDTH - surf.get_width()) // 2, HEIGHT // 2 + i * 50))

    elif state == "graphics":
        draw_centered_text([
            ("Graphics", big_font, WHITE)
        ], HEIGHT // 4)

        for i, option in enumerate(graphics_options):
            color = WHITE if i == selected_options else GRAY
            prefix = "> " if i == selected_options else "  "
            surf = font.render(prefix + option, True, color)
            screen.blit(surf, ((WIDTH - surf.get_width()) // 2, HEIGHT // 2 + i * 50))

    elif state == "audio":
        draw_centered_text([
            ("Audio", big_font, WHITE)
        ], HEIGHT // 4)

        for i, option in enumerate(audio_options):
            color = WHITE if i == selected_options else GRAY
            prefix = "> " if i == selected_options else "  "
            surf = font.render(prefix + option, True, color)
            screen.blit(surf, ((WIDTH - surf.get_width()) // 2, HEIGHT // 2 + i * 50))

    elif state == "visuals":
        draw_centered_text([("Visuals", big_font, WHITE)], HEIGHT // 4)

        visuals_options = [f"Block Style: {block_styles[block_style % len(block_styles)][0]}", "Back"]

        for i, option in enumerate(visuals_options):
            color = WHITE if i == selected_options else GRAY
            prefix = "> " if i == selected_options else "  "
            surf = font.render(prefix + option, True, color)
            screen.blit(surf, ((WIDTH - surf.get_width()) // 2, HEIGHT // 2 + i * 50))

    elif state == "frame_rate":
        draw_centered_text([("Frame Rate", big_font, WHITE)], HEIGHT // 4)

        for i, option in enumerate(frame_rate_options):
            color = WHITE if i == selected_options else GRAY
            prefix = "> " if i == selected_options else "  "
            text = f"{prefix}{option}"
            surf = font.render(text, True, color)
            screen.blit(surf, ((WIDTH - surf.get_width()) // 2, HEIGHT // 2 + i * 50))

    elif state == "volume":
        draw_centered_text([("Volume Settings", big_font, WHITE)], HEIGHT // 4)

        for i, option in enumerate(volume_options):
            color = WHITE if i == selected_options else GRAY
            prefix = "> " if i == selected_options else "  "

            if option == "Music Volume":
                volume_display = f"{int(music_volume * 100)}%"
            elif option == "SFX Volume":
                volume_display = f"{int(sfx_volume * 100)}%"
            else:
                volume_display = ""

            text = f"{prefix}{option} {volume_display}"
            surf = font.render(text, True, color)
            screen.blit(surf, ((WIDTH - surf.get_width()) // 2, HEIGHT // 2 + i * 50))

    elif state == "track":
        draw_centered_text([
            ("Select Track", big_font, WHITE)
        ], HEIGHT // 4)

        for i, option in enumerate(track_options):
            color = WHITE if i == selected_options else GRAY
            prefix = "> " if i == selected_options else "  "
            surf = font.render(prefix + option, True, color)
            screen.blit(surf, ((WIDTH - surf.get_width()) // 2, HEIGHT // 2 + i * 50))

    elif state == "game_stats":
        draw_centered_text([
            ("Statistics", big_font, WHITE)
        ], HEIGHT // 5)

        draw_centered_text([
            ("High Score: " + str(high_score), font, WHITE),
            ("Overall Total Points: " + str(absolute_point_total), font, WHITE),
            ("Rows Cleared: " + str(row_stat), font, WHITE),
            ("Total Jumps: " + str(jump_stat), font, WHITE),
            ("Total Points P1: " + str(point_total_p1), font, WHITE),
            ("Total Points P2: " + str(point_total_p2), font, WHITE),
        ], HEIGHT // 3)

    pygame.display.flip()
pygame.quit()
sys.exit()
