# Curve Online

Eden Yosef

Language: Python

Tools: PyGame, TCP, Threading

An online curve game.

# General Description

While learning about TCP networking, I came up with the idea to make this project.

Curve Online is a competitive online game where you have to stay the last curve on the map!
I made this project using PyGame library, TCP (socket library), threading and more.

# Game Rules

Curve Online is an online game, up to 4 players.

The goal is to stay the last curve on the map, You die if you touch a wall or you collide with another curve.

# How To Use

### Menus:

* *p* - To connect to a game
* *esc* - To exit the game

### Player Movements:

* *Right Arrow* - Curve moves clockwise
* *Left Arrow* - Curve moves counterclockwise

# Client and Server

The client sends messages to the server in the following format:
**CMD|DATA**

The server decrypts the messages and sends the corresponding data back to the client.
