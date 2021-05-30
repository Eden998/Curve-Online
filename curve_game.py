import pygame
import random
import math
from pygame import Vector2
from pygame.locals import (
    K_UP,
    K_DOWN,
    K_LEFT,
    K_RIGHT,
    K_ESCAPE,
    KEYDOWN,
    QUIT,
    K_r,
    K_p
)
import socket
import threading
import datetime

# Server info:
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5678

# Define constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 1000
SPEED = 5
ROTATION_SPEED = 5
PLAYER_SIZE = 10
FPS = 60

# colors
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
player_colors = [BLUE, RED, YELLOW, GREEN]
player_colors_str = ["Blue", "Red", "Yellow", "Green"]
player_starting_positions = [[250.0, 250.0], [750.0, 750.0], [250.0, 750.0], [750.0, 250.0]]

# Player Class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super(Player, self).__init__()
        self.speed = SPEED
        self.direction = Vector2(0, self.speed)
        self.direction.rotate_ip(random.randint(1, 360))
        self.radius = PLAYER_SIZE
        self.color = BLUE
        self.player_pos = [SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2]
        self.trail_countdown = 0
        self.count = 0
        self.trail = []
        self.head_trail_length = (self.radius // self.speed) // 2 + 1  # prevent losing from head collision
        self.winner = False

    def draw_snake(self):
        pygame.draw.circle(screen, self.color, self.player_pos, self.radius)
        send_draw_snake([self.player_pos[0], self.player_pos[1]])

    def player_move(self, pressed_keys):
        if pressed_keys[K_LEFT]:
            self.direction.rotate_ip(-ROTATION_SPEED)
        if pressed_keys[K_RIGHT]:
            self.direction.rotate_ip(ROTATION_SPEED)
        # checks if to add a collision point
        if self.trail_countdown == self.head_trail_length:
            self.trail.append([self.player_pos[0], self.player_pos[1]])
            send_trail([self.player_pos[0], self.player_pos[1]])
            self.trail_countdown = 0
        self.player_pos += self.direction
        self.trail_countdown += 1

    def is_alive(self):
        if self.player_pos[1] <= 0 or self.player_pos[1] >= SCREEN_WIDTH or self.player_pos[0] <= 0 or self.player_pos[0] >= SCREEN_HEIGHT:
            return False
        if len(self.trail) > self.head_trail_length:
            for spot in self.trail[:-self.head_trail_length]:
                if self.distance(spot) <= self.radius * 2:
                    return False
        for spot in players_trails:
            if self.distance(spot) <= self.radius * 2:
                return False
        return True

    def distance(self, p):
        return math.sqrt((self.player_pos[0] - p[0]) ** 2 + (self.player_pos[1] - p[1]) ** 2)


# Receiving Thread
server_messages = []
receive = True

class ReceiveThread(threading.Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        while receive:
            server_message = my_socket.recv(1024).decode()
            server_messages.append(server_message)


def split_message(message):
    return message.split("|")


def split_data(data):
    return data.split(",")


def merge_data(data):
    return ",".join(data)


def build_message(cmd, data):
    return cmd + "|" + data + "@"


def handle_messages(messages):
    empty = False
    if messages == "":
        empty = True
    if not empty:
        splitted_messages = messages[:-1].split('@')
        for message in splitted_messages:
            splitted_message = split_message(message)
            cmd = splitted_message[0]
            data = splitted_message[1]
            if cmd == "DRAW" and play:
                draw_snake(data)
            if cmd == "TRAIL" and play:
                add_trail(data)
            if cmd == "PLAYERSCOUNT":
                update_players_num(data)
            if cmd == "COUNTDOWN" and countdown:
                update_countdown(data)
            if cmd == "DEAD":
                update_dead(data)
            if cmd == "WIN":
                update_win()
            if cmd == "INITIALIZE_PLAYER":
                initialize_player(data)
    server_messages.remove(messages)


def draw_snake(data):
    data = split_data(data)
    color = player_colors[int(data[2])]
    spot_pos = [float(data[0]), float(data[1])]
    pygame.draw.circle(screen, color, spot_pos, PLAYER_SIZE)


players_trails = []


def add_trail(data):
    data = split_data(data)
    spot_pos = [float(data[0]), float(data[1])]
    players_trails.append(spot_pos)


# Initialize the game
pygame.init()

# Create the screen object
screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
pygame.display.set_caption('CurveFever Replica')


def clear_screen():
    screen.fill((0, 0, 0))


# Menu text
menu_font = pygame.font.Font('freesansbold.ttf', 80)

menu_text = menu_font.render('Menu:', True, BLUE)
menuRect = menu_text.get_rect()
menuRect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 200)

play_option_text = menu_font.render('To play press p', True, GREEN)
play_optionRect = play_option_text.get_rect()
play_optionRect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

exit_option_text = menu_font.render('To exit press esc', True, RED)
exit_optionRect = exit_option_text.get_rect()
exit_optionRect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 200)


# Waiting for players screen:

players_num = 0
waiting_menu_font = pygame.font.Font('freesansbold.ttf', 60)

waiting_menu_text = waiting_menu_font.render('Waiting for players', True, RED)
waiting_menuRect = waiting_menu_text.get_rect()
waiting_menuRect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100)

players_num_text = waiting_menu_font.render("Number of players: " + str(players_num), True, RED)
players_numRect = players_num_text.get_rect()
players_numRect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)


# Game over text
game_over_font = pygame.font.Font('freesansbold.ttf', 80)
game_over_text = game_over_font.render('Game Over', True, RED)
gameOverRect = game_over_text.get_rect()
gameOverRect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

# Countdown screen:
countdown_timer = 15
countdown_font = pygame.font.Font('freesansbold.ttf', 60)

countdown_text = countdown_font.render(str(countdown_timer), True, RED)
countdownRect = countdown_text.get_rect()
countdownRect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100)


def player_color_message(player_color):
    color = player_colors_str[player_colors.index(player_color)]
    player_color_text = countdown_font.render("You are " + color, True, player.color)
    player_colorRect = player_color_text.get_rect()
    player_colorRect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    screen.blit(player_color_text, player_colorRect)

# win screen:

play_again_font = pygame.font.Font('freesansbold.ttf', 80)
play_again_text = play_again_font.render('Press p to play again', True, WHITE)
play_againRect = play_again_text.get_rect()
play_againRect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100)


# FPS display function
def display_fps():
    fps_font = pygame.font.Font('freesansbold.ttf', 20)
    fps_text = fps_font.render(str(int(clock.get_fps())), True, RED)
    fps_rect = fps_text.get_rect()
    fps_rect.center = (15, 15)
    frames_bg = pygame.Surface(fps_rect.size)
    frames_bg.fill(BLACK)
    screen.blit(frames_bg, fps_rect)
    screen.blit(fps_text, fps_rect)


my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def login_to_server():
    global my_socket
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.connect((SERVER_IP, SERVER_PORT))


def disconnect_from_server():
    global receive
    receive = False
    message = build_message("QUIT", "0")
    my_socket.send(message.encode())


def send_trail(spot):
    data = merge_data([str(spot[0]), str(spot[1])])
    message = build_message("TRAIL", data)
    my_socket.send(message.encode())


def send_dead():
    message = build_message("DEAD", "0")
    my_socket.send(message.encode())


def send_draw_snake(spot):
    data = merge_data([str(spot[0]), str(spot[1]), str(player_colors.index(player.color))])
    message = build_message("DRAW", data)
    my_socket.send(message.encode())


def initialize_player(data):
    # define color by players count
    global player
    global players_trails
    players_trails = []
    player = Player()
    players_count = int(data)
    if players_count < 4:
        player.color = player_colors[players_count]
        player.player_pos = player_starting_positions[players_count]


def send_initialize_player():
    message = build_message("INITIALIZE_PLAYER", "0")
    my_socket.send(message.encode())


def show_menu():
    clear_screen()
    screen.blit(menu_text, menuRect)
    screen.blit(play_option_text, play_optionRect)
    screen.blit(exit_option_text, exit_optionRect)


def show_waiting_screen():
    clear_screen()
    players_num_text = waiting_menu_font.render("Number of players: " + str(players_num), True, RED)
    players_numRect = players_num_text.get_rect()
    players_numRect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    screen.blit(waiting_menu_text, waiting_menuRect)
    screen.blit(players_num_text, players_numRect)


def check_players_num():
    message = build_message("PLAYERSCOUNT", "0")
    my_socket.send(message.encode())


def update_players_num(data):
    # checks if players num changed and refreshes the screen
    global players_num
    if int(data) != players_num:
        players_num = int(data)
        show_waiting_screen()


def show_countdown_screen():
    clear_screen()
    countdown_text = countdown_font.render(str(countdown_timer), True, RED)
    countdownRect = countdown_text.get_rect()
    countdownRect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100)
    if countdown:
        screen.blit(countdown_text, countdownRect)


def check_game_countdown():
    message = build_message("COUNTDOWN", "0")
    my_socket.send(message.encode())


def update_countdown(data):
    global countdown_timer
    countdown_timer = int(data)
    show_countdown_screen()


def update_dead(data):
    pass  # to implement


def update_win():
    global win
    win = True


def send_remove_player():
    message = build_message("REMOVE_PLAYER", '0')
    my_socket.send(message.encode())


def show_end_screen(player_win):
    clear_screen()
    if player_win:
        win_font = pygame.font.Font('freesansbold.ttf', 80)
        win_text = win_font.render('You Win!', True, GREEN)
        winRect = win_text.get_rect()
        winRect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        screen.blit(win_text, winRect)
    else:
        lose_font = pygame.font.Font('freesansbold.ttf', 80)
        lose_text = lose_font.render('You Lose :(', True, RED)
        loseRect = lose_text.get_rect()
        loseRect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        screen.blit(lose_text, loseRect)
    screen.blit(play_again_text, play_againRect)


def play_again():
    global waiting_for_players
    waiting_for_players = True


player = Player()
clock = pygame.time.Clock()


receive_thread = ReceiveThread()

# game status:
running = True
menu = True
waiting_for_players = False
countdown = False
play = False
game_end = False
restart = False
win = False

# menu display
show_menu()

while running:
    for event in pygame.event.get():
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                disconnect_from_server()
                running = False

        elif event.type == QUIT:
            disconnect_from_server()
            running = False

        # restart button
        if event.type == KEYDOWN and play:
            if event.key == K_r and not player.is_alive():
                player = Player()
                screen.fill(BLACK)

        # pressing p to play
        if event.type == KEYDOWN and menu:
            if event.key == K_p:
                # Connect to server
                login_to_server()
                receive_thread.start()
                menu = False
                waiting_for_players = True
                show_waiting_screen()

        if event.type == KEYDOWN and restart:
            if event.key == K_p:
                send_initialize_player()
                restart = False
                waiting_for_players = True
                players_num = 0
                countdown_timer = 8
                win = False
                show_waiting_screen()

    for message in server_messages:
        handle_messages(message)

    if waiting_for_players:
        check_players_num()
        if players_num >= 2:
            # activating countdown phase
            waiting_for_players = False
            countdown = True
            clear_screen()
        if players_num > 4:
            disconnect_from_server()
            running = False

    if countdown:
        check_game_countdown()
        check_players_num()
        player_color_message(player.color)
        if countdown_timer <= 0:
            countdown = False
            play = True
            clear_screen()
        elif players_num < 2:
            countdown = False
            waiting_for_players = True
            show_waiting_screen()

    if play:
        alive = player.is_alive()
        if alive:
            # Get all the keys currently pressed
            pressed_keys = pygame.key.get_pressed()
            # Update the player sprite based on user keypresses
            # player.update(pressed_keys)
            player.player_move(pressed_keys)
            player.draw_snake()
            if win:
                play = False
                game_end = True
                player.winner = True
                send_dead()

        else:
            # draws game over on screen
            play = False
            player.winner = False
            game_end = True
            screen.blit(game_over_text, gameOverRect)
            send_dead()

    if game_end:
        if win:
            show_end_screen(player.winner)
            send_remove_player()
            game_end = False
            restart = True

    if restart:
        pass  # to implement

    # frames display:
    display_fps()

    clock.tick(FPS)

    pygame.display.flip()
