#!/bin/python3

# IDEA 1
# init terminal
# -> user issues command
# text editor opens up
# -> user writes code
# -> user 'commits' code
# -> code validated
# text editor closes
# terminal reappears
# (user code is now 'active')
# listen for incoming text
# -> any incoming text is printed
# -> and then passed to users 'active' program
# -> any outputs from user program printed
# -> output sent off to server
# OPTIONAL: user script written in-line from terminal?
# USER 1 -> $ print("hello world")
# USER 2 -> $ print(<inp>.split()[0] + "nerd")
# TERMINAL -> hello world
# TERMINAL -> hello nerd

# might need to slow down processing to avoid infinite loops (don't want to ddos)

# IDEA 2
# essentially same idea, but editor is different window
