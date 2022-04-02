#!/bin/python3
'''
Copyright (c) 2022, Kevin Lockwood <kevin-b-lockwood@gmail.com>
Copyright (c) 2022, the POISN developers.

SPDX-License-Identifier: BSD-2-Clause
'''

import argparse
import pathlib
import socket
import queue
import threading

connections = {}

def main():
    parser = argparse.ArgumentParser(
            description = 'Official POISN protocol server')
    parser.add_argument('-c', '--config',
            help='config file',
            metavar='PATH',
            type=pathlib.Path,
            default='config')
    parser.add_argument('-p', '--port',
            type=int,
            default=5555,
            help='listening port')
    parser.add_argument('-m', '--max-connections',
            type=int,
            default=None,
            help='max number of client connections allowed')
    parser.add_argument('-q', '--queue-depth',
            metavar='N',
            type=int,
            default=10,
            help='depth of queue for clients attempting connection')
    parser.add_argument('--select-timeout',
            metavar='S',
            type=int,
            default=10)
    parser.add_argument('--recv-buf-size',
            metavar='N',
            type=int,
            default=2048,
            help='how many bytes each connection should recv at a time')
    args = parser.parse_args()
    print(args)

    master_buffer = queue.Queue()
    sock = socket.socket()
    host = '10.55.10.147'
    port = args.port

    try:
        sock.bind((host, port))
    except socket.error as e:
        print(str(e))

    print('listening')
    sock.listen(args.queue_depth)

    while True:
        # Accept a client
        client, address = sock.accept()
        print('Connected to: ' + address[0] + ':' + str(address[1]))

        # Create a thread to handle input from that socket
        in_thread = threading.Thread(target=sock_input,
                args=(args, client, master_buffer))

        # Create a thread to relay data out to the client
        thread_buffer = queue.Queue()
        out_thread = threading.Thread(target=sock_output,
                args=(client, thread_buffer))

        # Keep track of the thread and its buffer
        connections[get_socket_id(client)] = { 'out_buffer': thread_buffer }
        in_thread.start()
        out_thread.start()

    exit(0)

def master_queue_handler(buffer):
    while True:
        for connection in connections:
            sender, data = buffer.get()

def sock_input(args, connection, buffer):
    print("entering sock_input")
    # As long as we are connected, get input from the socket and enque it in
    # the master queue
    while get_socket_id(connection) in connections.keys():
        data = connection.recv(args.recv_buf_size)
        # If there was no received data, the connection is broken and will
        # never heal, so record that this socket is dead.
        if not data:
            connected = False;
        else:
            print("{}: {}".format(get_socket_id(connection),
                data.decode('utf-8', 'replace')))
            buffer.put((get_socket_id(connection), data))
    if get_socket_id(connection) in connections.keys():
        connections.remove(get_socket_id(connection))
    print("exiting sock_input")

def sock_output(connection, buffer):
    print("entering sock_output")
    connected = True
    while connected:
        try:
            connection.sendall(buffer.get())
        except socket.error:
            connected = False
    print("exiting sock_output")

def get_socket_id(socket):
    socket_id = "{}{}".format(socket.getsockname()[0],
            socket.getsockname()[1])
    return socket_id

# server config
# -> port
# -> ip?
# -> conn limit
# -> channels?

# init socket
# -> open socket
# -> for every connection
# --> accept new connection
# --> give it ID
# --> append it to array 'active connections'

# manage open connections
# -> for every active connection
# --> check if still active
# --> pull text from buffer
# --> if not empty
# ---> append it to array 'pending out'

# push text to rest
# -> for every pending out
# --> for every active connection
# ---> push pending out to connection

main()
