#!/bin/python3
'''
Copyright (c) 2022, Kevin Lockwood <kevin-b-lockwood@gmail.com>
Copyright (c) 2022, the POISN developers.

SPDX-License-Identifier: BSD-2-Clause
'''

import argparse
import json
import pathlib
import queue
import socket
import threading

connections = {}
connections_lock = threading.Lock()
config = {}
history = []

def main():
    parser = argparse.ArgumentParser(
            description = 'Official POISN protocol server')
    parser.add_argument('-c', '--config',
            help='config file',
            metavar='PATH',
            type=pathlib.Path,
            default='config.json')
    parser.add_argument('--history',
            help='chat log/history file', metavar='PATH',
            type=pathlib.Path,
            default='history.json')
    parser.add_argument('-p', '--port',
            type=int,
            default=5555,
            help='listening port')
    parser.add_argument('-m', '--max-connections',
            type=int,
            default=None,
            help='max number of client connections allowed')
    parser.add_argument('-q', '--queue-depth',
            metavar='QUEUE_DEPTH',
            type=int,
            default=10,
            help='depth of queue for clients attempting connection')
    parser.add_argument('--recv-buf-size',
            metavar='BUF_SIZE',
            type=int,
            default=2048,
            help='how many bytes each connection should recv at a time')
    args = parser.parse_args()
    print(args)

    # Populate history and config variables from file
    config = json_loader(args.config)
    with open(args.history) as history_file:
        for line in history_file.readlines():
            history.append(json.loads(line))

    master_queue = queue.Queue()
    sock = socket.socket()
    host = '10.55.10.147'
    port = args.port

    try:
        sock.bind((host, port))
    except socket.error as e:
        print(str(e))
        exit(1)

    print('listening')
    sock.listen(args.queue_depth)

    # Create master queue handler to pass data out to each connected client
    master_queue_handler_thread = threading.Thread(target=master_queue_handler,
            args=(history, config))
    master_queue_handler_thread.start()

    while True:
        try:
            # Accept a client
            client, address = sock.accept()
            print('Connected to: ' + address[0] + ':' + str(address[1]))

            authentication_thread = threading.Thread(
                    target=authentication_handler,
                    args=(args, client, config, history))
            authentication_thread.start()

        except KeyboardInterrupt:
            print("\033[32mINFO:\033[0m Shutting down")
            print(config)
            with open(args.config, "w") as config_file:
                config_file.write(json.dumps(config, indent=4))
            print("\033[32mINFO:\033[0m Safe to kill")
            exit(0)

    exit(0)

def authentication_handler(args, client, config, history):

    # Get username
    try:
        client.sendall("Username: ".encode())
        username = client.recv(args.recv_buf_size).decode('utf-8', 'replace').strip()
        client.sendall("Password: \033[28m".encode())
        password = client.recv(args.recv_buf_size).decode('utf-8', 'replace').strip()
        client.sendall("\033[0m".encode())
        client.send('\033[A'.encode())
        client.send('Password: '.encode())
        for i in range(0, len(password)):
            client.send(' '.encode())
        client.send('\n'.encode())
    except ConnectionResetError:
        return

    # Get user device/host so we can keep track of what to send to which
    # device/connection
    client.sendall("Host: ".encode())
    host = client.recv(args.recv_buf_size).decode('utf-8', 'replace').strip()

    print("{}@{}".format(username, host))
    # Create a thread to handle input from that socket
    in_thread = threading.Thread(target=sock_input,
            args=(args, client, history))

    # Create a thread to relay data out to the client
    thread_buffer = queue.Queue()
    out_thread = threading.Thread(target=sock_output,
            args=(client, thread_buffer))
    # Acquire lock so that we don't change the size of connections out
    # from under an iterator
    connections_lock.acquire()
    # Keep track of the thread and its buffer
    last_message = 0
    print(f'config: {config}')
    if username in config['clients']:
        if host in config['clients'][username]:
            if 'last-message' in config['clients'][username][host]:
                if len(history) >= config['clients'][username][host]['last-message']:
                    last_message = config['clients'][username][host]['last-message']
                else:
                    last_message = 0
                print(last_message)
            else:
                config['clients'][username][host]['last-message'] = 0
        else:
            config['clients'][username][host] = {'last-message': 0}
    else:
        config['clients'][username] = {host: {'last-message': 0}}


    connections[get_socket_id(client)] = {
            'username': username,
            'host': host,
            'out_buffer': thread_buffer,
            'last-message': last_message}
    connections_lock.release()
    # Start the producer and consumer
    in_thread.start()
    out_thread.start()

def master_queue_handler(buffer, config):
    while True:
        # Acquire lock on connections so that it won't change size while we
        # iterate through it
        connections_lock.acquire()
        for connection_id in connections.keys():
            # Get the index of the most recent message
            last_message = len(history)
            connection_data = connections[connection_id]

            # Send this client every message between the last one it saw and
            # the most recent message the server received
            for message in history[connections[connection_id]['last-message']:last_message]:

                # If this message was sent by the current client, don't send it
                # back to them, that would be silly
                if not (message['sender'] == connection_data['username']
                        and message['host'] == connection_data['host']):
                    connections[connection_id]['out_buffer'].put(
                            "{}\n".format(message['data']).encode())

            # Update last seen message for this client
            connections[connection_id]['last-message'] = last_message
            config['clients'][connection_data['username']][connection_data['host']]['last-message'] = last_message
        connections_lock.release()


def sock_input(args, connection, buffer):
    print("entering sock_input")
    connected = True
    # As long as we are connected, get input from the socket and enque it in
    # the master queue
    while connected:
        data = connection.recv(args.recv_buf_size)
        # If there was no received data, the connection is broken and will
        # never heal, so record that this socket is dead.
        if not data:
            connected = False;
        # There was data received, so process it and enqueue it in the master
        # queue
        else:
            connection_data = connections[get_socket_id(connection)]
            cleaned_data = data.decode('utf-8', 'replace').strip()
            print("\033[1m{}@{}:\033[0m {}".format(connection_data['username'],
                connection_data['host'], cleaned_data))
            message_package = {'sender': connection_data['username'],
                    'host': connection_data['host'],
                    'data': cleaned_data}
            buffer.append(message_package)

            # Assume that the client has echo checked it in the file to avoid
            # the eventuality of a message_id being duplicated in the future
            # causing collisions and messages disappearing
            with open(args.history, 'a') as history_file:
                history_file.write("{}\n".format(json.dumps(message_package)))
    # Remove this socket from the list of connections, as it's no longer
    # connected.
    if get_socket_id(connection) in connections.keys():
        connections_lock.acquire()
        connections.pop(get_socket_id(connection))
        connections_lock.release()
    print("exiting sock_input")

def sock_output(connection, buffer):
    print("entering sock_output")
    connected = True
    # push data from inbox queue through this socket
    while connected:
        try:
            connection.sendall(buffer.get())
        except socket.error:
            connected = False

        if get_socket_id(connection) not in connections.keys():
            connected = False
    print("exiting sock_output")

def get_socket_id(socket):
    '''
    Generates a unique identifier from a socket's qualities
    '''
    socket_id = "{}:{}".format(socket.getpeername()[0],
            socket.getpeername()[1])
    return socket_id

def json_loader(path):
    '''
    Loads a json file into a variable and handles expected errors
    '''
    try:
        with open(path) as json_file:
            variable = json.loads(json_file.read())
            print(variable)
            return variable
    except FileNotFoundError:
        print("\033[31mERROR:\033[0m {} not found".format(path))
        exit(1)
    except json.decoder.JSONDecodeError:
        print("\033[31mERROR:\033[0m {} not valid json".format(path))
        exit(1)

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
