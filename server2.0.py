import socket
import select
import datetime

MAX_MSG_LENGTH = 1024
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5678

BLUE = (0, 0, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)

messages_to_send = []
player_colors = ["blue", "red", "yellow", "green"]
timer = None
countdown_seconds = 8


def print_client_sockets(client_sockets):
    for c in client_sockets:
        print("\t", c.getpeername())


def split_messages(messages):
    splitted_messages = messages[:-1].split('@')
    messages = []
    for message in splitted_messages:
        messages.append(message.split("|"))
    return messages


def split_data(data):
    return data.split(",")


def merge_data(data):
    return ",".join(data)


def build_message(cmd, data):
    return cmd + "|" + data + "@"


def initialize_player(client_socket):
    # sends color and starting position
    players_count = len(players_in_game)
    message = build_message("INITIALIZE_PLAYER", str(players_count))
    messages_to_send.append((client_socket, message))


def send_draw(client_sockets, current_socket, data):
    message = build_message("DRAW", data)
    for s in client_sockets:
        if s is not current_socket:
            messages_to_send.append((s, message))


def send_trail(client_sockets, current_socket, data):
    message = build_message("TRAIL", data)
    for s in client_sockets:
        if s is not current_socket:
            messages_to_send.append((s, message))


def send_players_num(client_sockets, current_socket):
    players_count = len(players_in_game)
    message = build_message("PLAYERSCOUNT", str(players_count))
    set_timer()
    messages_to_send.append((current_socket, message))


def set_timer():
    global timer
    players_num = len(players_in_game)
    if players_num >= 2 and timer is None:
        print("Timer has been set")
        timer = datetime.datetime.now()
    if players_num < 2:
        timer = None


def send_countdown(current_socket):
    # gets time until end of countdown
    if timer is not None:  # if
        time_left = int((datetime.timedelta(seconds=countdown_seconds) - (datetime.datetime.now() - timer)).total_seconds())
    else:
        time_left = countdown_seconds
    message = build_message("COUNTDOWN", str(time_left))
    messages_to_send.append((current_socket, message))


def send_dead(client_sockets, current_socket):
    dead_player = client_sockets.index(current_socket)
    message = build_message("DEAD", str(dead_player))
    for s in client_sockets:
        if s is not current_socket:
            messages_to_send.append((s, message))


def send_win(client_sockets, current_socket):
    message = build_message("WIN", '0')
    for s in client_sockets:
        messages_to_send.append((s, message))


players_in_game = []
players_dead = []
players_in_menu = []

def main():
    print("Setting up server...")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen()
    print("Listening for clients...")
    client_sockets = []
    while True:
        print("players in game: ", len(players_in_game))
        print("players dead: ", len(players_dead))
        print("players in menu: ", len(players_in_menu))
        ready_to_read, ready_to_write, in_error = select.select([server_socket] + client_sockets, client_sockets, [])
        for current_socket in ready_to_read:
            if current_socket is server_socket:
                (client_socket, client_address) = current_socket.accept()
                print("New client joined!", client_address)
                initialize_player(client_socket)
                players_in_game.append(client_socket)
                client_sockets.append(client_socket)
                print_client_sockets(client_sockets)
            else:
                messages = split_messages(current_socket.recv(MAX_MSG_LENGTH).decode())
                for message in messages:
                    if message != [""]:
                        cmd = message[0]
                        data = message[1]
                        if cmd == "QUIT":
                            print("Connection closed")
                            client_sockets.remove(current_socket)
                            if current_socket in players_in_game:
                                players_in_game.remove(current_socket)
                            elif current_socket in players_dead:
                                players_dead.remove(current_socket)
                            elif current_socket in players_in_menu:
                                players_in_menu.remove(current_socket)
                            current_socket.close()
                            set_timer()  # resets timer if less than 2 players
                            print_client_sockets(client_sockets)
                        if cmd == "INITIALIZE_PLAYER":
                            initialize_player(current_socket)
                            players_in_menu.remove(current_socket)
                            players_in_game.append(current_socket)
                        if cmd == "DRAW":
                            send_draw(client_sockets, current_socket, data)
                        if cmd == "TRAIL":
                            send_trail(client_sockets, current_socket, data)
                        if cmd == "PLAYERSCOUNT":
                            send_players_num(client_sockets, current_socket)
                        if cmd == "COUNTDOWN":
                            send_countdown(current_socket)
                        if cmd == "DEAD":
                            players_in_game.remove(current_socket)
                            players_dead.append(current_socket)
                            if len(players_in_game) > 1:
                                print("Continue Playing...")
                                # send_dead(client_sockets, current_socket)
                            else:
                                print("Sending win")
                                send_win(client_sockets, current_socket)
                                players_dead.remove(current_socket)
                                players_in_menu.append(current_socket)
                        if cmd == "REMOVE_PLAYER":
                            set_timer()
        for message in messages_to_send:
            current_socket, data = message
            if current_socket in ready_to_write:
                current_socket.send(data.encode())
                messages_to_send.remove(message)

main()
