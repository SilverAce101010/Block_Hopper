import pygame, sys, random

pygame.init()
pygame.mixer.init()
jump_sound = pygame.mixer.Sound("sound/jump.mp3")
drop_sound = pygame.mixer.Sound("sound/block_thud.mp3")

# === CONFIG ===
TILE_SIZE = 40
COLS, ROWS = 10, 20
BLOCK_WIDTH, BLOCK_HEIGHT = COLS * TILE_SIZE, ROWS * TILE_SIZE
PADDING = 50
WIDTH = BLOCK_WIDTH + PADDING * 2 + 150
HEIGHT = BLOCK_HEIGHT + PADDING * 2
target_fps = 60  # Default value
FALL_INTERVAL_NORMAL = 250
FALL_INTERVAL_FAST = FALL_INTERVAL_NORMAL / 10

# === COLORS ===
WHITE, GRAY, BLACK = (255, 255, 255), (200, 200, 200), (0, 0, 0)
RED, CYAN, YELLOW = (255, 50, 50), (0, 255, 255), (255, 255, 0)
PURPLE, GREEN, ORANGE = (160, 32, 240), (0, 255, 0), (255, 165, 0)
BLUE = (50, 50, 255)

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
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Block Hopper")
clock = pygame.time.Clock()
font, big_font = pygame.font.SysFont(None, 36), pygame.font.SysFont(None, 72)
block_rect = pygame.Rect(PADDING, PADDING, BLOCK_WIDTH, BLOCK_HEIGHT)

# === PLAYER SETUP ===
player = pygame.Rect(block_rect.x + TILE_SIZE * 2, block_rect.y + TILE_SIZE * 7, TILE_SIZE, TILE_SIZE)
player_velocity = pygame.Vector2(0, 0)
GRAVITY, JUMP_POWER, PLAYER_SPEED, MAX_FALL_SPEED = 1, -15, 8, 20

# === GAME STATE ===
board = [[None] * COLS for _ in range(ROWS)]
p1score, p2score, p2_timer , paused, player_on_ground = 0, 0, 0, False, False
piece, next_piece, fall_timer, state = None, None, 0, "start"

# === MENU OPTIONS ===
menu_options = ["Start Game", "Options"]
restart_options = ["Restart", "Back"]
options_menu = ["Game Stats", "Graphics", "Audio", "Back"]
graphics_options = ["Visuals", "Frame Rate", "Back"]
audio_options = ["Volume", "Track", "Back"]
volume_options = ["Music Volume", "SFX Volume", "Back"]
frame_rate_options = ["FPS: 30", "FPS: 60", "Back"]
track_options = ["Menu_Music", "Gameplay_Music", "Back"]

selected_options = 0

current_music = None
music_volume = 0.5
sfx_volume = 0.3

pygame.mixer.music.set_volume(music_volume)
jump_sound.set_volume(sfx_volume)
drop_sound.set_volume(sfx_volume)

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

def play_music(filename):
    global current_music
    if current_music != filename:
        pygame.mixer.music.stop()
        pygame.mixer.music.load("sound/" + filename)
        pygame.mixer.music.play(-1)  # loop indefinitely
        current_music = filename

def clear_full_rows():
    global board
    new_board = [row for row in board if not all(row)]
    cleared = ROWS - len(new_board)
    if cleared > 0:
        drop_sound.play()
    board = [[None] * COLS for _ in range(cleared)] + new_board
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

def move_player(keys):
    global player_on_ground
    dx = (keys[pygame.K_d] - keys[pygame.K_a]) * PLAYER_SPEED
    player.x += dx

    if player.left < block_rect.left:
        player.left = block_rect.left

    elif player.right > block_rect.right:
        player.right = block_rect.right

    if collide_with_board(player): player.x -= dx

    player_velocity.y = min(player_velocity.y + GRAVITY, MAX_FALL_SPEED)
    player.y += player_velocity.y
    player_on_ground = player.bottom >= block_rect.bottom
    if player_on_ground: player.bottom, player_velocity.y = block_rect.bottom, 0

    if collide_with_board(player):
        player.y -= player_velocity.y
        if player_velocity.y > 0: player_on_ground = True
        player_velocity.y = 0

def reset_game():
    global board, p1score, p2score, p2_timer, player, player_velocity, piece, next_piece, fall_timer, paused
    board = [[None]*COLS for _ in range(ROWS)]
    p1score, p2score, p2_timer, fall_timer, paused = 0, 0, 0, 0, False
    player.topleft = (block_rect.x + TILE_SIZE * 2, block_rect.y + TILE_SIZE * 7)
    player_velocity.update(0, 0)
    piece, next_piece = Tetromino(), Tetromino()

def draw_board():
    pygame.draw.rect(screen, GRAY, block_rect)
    for c in range(COLS + 1):
        x = block_rect.x + c * TILE_SIZE
        pygame.draw.line(screen, BLACK, (x, block_rect.y), (x, block_rect.bottom))
    for r in range(ROWS + 1):
        y = block_rect.y + r * TILE_SIZE
        pygame.draw.line(screen, BLACK, (block_rect.x, y), (block_rect.right, y))

    for y, row in enumerate(board):
        for x, color in enumerate(row):
            if color:
                rect = (block_rect.x + x * TILE_SIZE, block_rect.y + y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, BLACK, rect, 1)

    if piece:
        for x, y in piece.get_blocks():
            if y >= 0:
                rect = (block_rect.x + x * TILE_SIZE, block_rect.y + y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(screen, piece.color, rect)
                pygame.draw.rect(screen, BLACK, rect, 1)

    pygame.draw.rect(screen, BLACK, player)
    pygame.draw.rect(screen, WHITE, player, 1)

    screen.blit(font.render(f"P1 Score: {p1score}", True, BLACK), (block_rect.right + 30, block_rect.top))
    screen.blit(font.render(f"P2 Score: {p2score}", True, BLACK), (block_rect.right + 30, block_rect.top + 35))
    screen.blit(font.render("Next:", True, BLACK), (block_rect.right + 30, block_rect.top + 85))

    if next_piece:
        preview_x, preview_y = block_rect.right + 55, block_rect.top + 125
        for dx, dy in next_piece.shape:
            x = preview_x + dx * TILE_SIZE
            y = preview_y + dy * TILE_SIZE
            pygame.draw.rect(screen, next_piece.color, (x, y, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(screen, BLACK, (x, y, TILE_SIZE, TILE_SIZE), 1)

    if paused:
        screen.blit(font.render("Paused", True, BLACK), (block_rect.right + 30, block_rect.top + 250))

def draw_centered_text(lines, y_offset=0):
    for i, (text, fnt, color) in enumerate(lines):
        surf = fnt.render(text, True, color)
        screen.blit(surf, ((WIDTH - surf.get_width()) // 2, y_offset + i * 60))

# === MAIN LOOP ===
running = True
while running:
    dt = clock.tick(target_fps)
    keys = pygame.key.get_pressed()
    screen.fill(WHITE)
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
                    elif event.key == pygame.K_w and player_on_ground:
                        player_velocity.y = JUMP_POWER
                        jump_sound.play()

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
                if event.key == pygame.K_ESCAPE:
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
                if event.key == pygame.K_ESCAPE:
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
        draw_centered_text([
            ("Block Hopper", big_font, BLACK)
        ], HEIGHT // 4)

        for i, option in enumerate(menu_options):
            color = BLUE if i == selected_options else BLACK
            prefix = "> " if i == selected_options else "  "
            surf = font.render(prefix + option, True, color)
            screen.blit(surf, ((WIDTH - surf.get_width()) // 2, HEIGHT // 2 + i * 50))

    elif state == "play":
        if not paused:
            move_player(keys)
            p2_timer, p2score
            p2_timer += dt
            if p2_timer >= 1500:
                p2score += 1
                p2_timer -= 1500
            fall_timer += dt
            interval = FALL_INTERVAL_FAST if keys[pygame.K_DOWN] else FALL_INTERVAL_NORMAL
            if fall_timer > interval:
                if not piece.move(0, 1):
                    piece.lock()
                    if state == "game_over": 
                        continue
                    p1score += clear_full_rows() * 10
                    piece = next_piece
                    next_piece = Tetromino()
                    if not piece.is_valid():
                        state = "game_over"
                fall_timer = 0
        draw_board()

    elif state == "game_over":
        draw_centered_text([
            ("Game Over", big_font, RED),
            (f"P1 Score: {p1score}", font, BLACK),
            (f"P2 Score: {p2score}", font, BLACK),
        ], HEIGHT // 4)

        for i, option in enumerate(restart_options):
            color = BLUE if i == selected_options else BLACK
            prefix = "> " if i == selected_options else "  "
            surf = font.render(prefix + option, True, color)
            screen.blit(surf, ((WIDTH - surf.get_width()) // 2, HEIGHT // 2 + i * 50))

    elif state == "options":
        draw_centered_text([
            ("Options", big_font, BLACK)
        ], HEIGHT // 4)

        for i, option in enumerate(options_menu):
            color = BLUE if i == selected_options else BLACK
            prefix = "> " if i == selected_options else "  "
            surf = font.render(prefix + option, True, color)
            screen.blit(surf, ((WIDTH - surf.get_width()) // 2, HEIGHT // 2 + i * 50))

    elif state == "graphics":
        draw_centered_text([
            ("Graphics", big_font, BLACK)
        ], HEIGHT // 4)

        for i, option in enumerate(graphics_options):
            color = BLUE if i == selected_options else BLACK
            prefix = "> " if i == selected_options else "  "
            surf = font.render(prefix + option, True, color)
            screen.blit(surf, ((WIDTH - surf.get_width()) // 2, HEIGHT // 2 + i * 50))

    elif state == "audio":
        draw_centered_text([
            ("Audio", big_font, BLACK)
        ], HEIGHT // 4)

        for i, option in enumerate(audio_options):
            color = BLUE if i == selected_options else BLACK
            prefix = "> " if i == selected_options else "  "
            surf = font.render(prefix + option, True, color)
            screen.blit(surf, ((WIDTH - surf.get_width()) // 2, HEIGHT // 2 + i * 50))

    elif state == "visuals":
        draw_centered_text([
            ("Visuals", big_font, BLACK),
            ("(No options yet)", font, GRAY)
        ], HEIGHT // 3)

    elif state == "frame_rate":
        draw_centered_text([("Frame Rate", big_font, BLACK)], HEIGHT // 4)

        for i, option in enumerate(frame_rate_options):
            color = BLUE if i == selected_options else BLACK
            prefix = "> " if i == selected_options else "  "
            text = f"{prefix}{option}"
            surf = font.render(text, True, color)
            screen.blit(surf, ((WIDTH - surf.get_width()) // 2, HEIGHT // 2 + i * 50))

    elif state == "volume":
        draw_centered_text([("Volume Settings", big_font, BLACK)], HEIGHT // 4)

        for i, option in enumerate(volume_options):
            color = BLUE if i == selected_options else BLACK
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
            ("Select Track", big_font, BLACK)
        ], HEIGHT // 4)

        for i, option in enumerate(track_options):
            color = BLUE if i == selected_options else BLACK
            prefix = "> " if i == selected_options else "  "
            surf = font.render(prefix + option, True, color)
            screen.blit(surf, ((WIDTH - surf.get_width()) // 2, HEIGHT // 2 + i * 50))

    elif state == "game_stats":
        draw_centered_text([
            ("Statistics", big_font, BLACK),
            ("(No options yet)", font, GRAY)
        ], HEIGHT // 3)

    pygame.display.flip()
pygame.quit()
sys.exit()
