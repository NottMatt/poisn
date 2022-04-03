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
import os
import hashlib

connections = {}
connections_lock = threading.Lock()
config = {}
history = []

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

def main():
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

def password_prompt(socket, prompt):
    socket.sendall(f'{prompt}'.encode())
    password = socket.recv(args.recv_buf_size).decode('utf-8', 'replace').strip()
    socket.sendall("\033[0m".encode())
    socket.send('\033[A'.encode())
    socket.send(f'{prompt}'.encode())
    for i in range(0, len(password)):
        socket.send(' '.encode())
    socket.send('\n'.encode())
    return password

def get_new_password(socket, username):
    salt = os.urandom(32)
    password_is_good = False
    while not password_is_good:
        password = password_prompt(socket,     'Enter New Password:  ')
        if password == password_prompt(socket, 'Repeat New Password: '):
            password_is_good = True
        else:
            socket.sendall('Passwords do not match'.encode())
    return salt, password.encode('iso-8859-1')

def get_password(config, socket, username):
    salt = config['clients'][username]['salt'].encode('iso-8859-1')
    password = password_prompt(socket, 'Password: ').encode('iso-8859-1')

    return salt, password

def authentication_handler(args, client, config, history):

    # Get username
    try:
        client.sendall("Username: ".encode())
        username = client.recv(args.recv_buf_size).decode('utf-8', 'replace').strip()

        login = False
        if username in config['clients']:
            login = True
            salt, password = get_password(config, client, username)
        else:
            salt, password = get_new_password(client, username)

        hashed_password = hashlib.pbkdf2_hmac(
                'sha256',
                password,
                salt,
                100000).decode('iso-8859-1')
        if login:
            if not hashed_password == config['clients'][username]['password']:
                client.sendall('Incorrect password'.encode())
                client.close()
                return

    except ConnectionResetError:
        return

    hostprompt = f'Select one of the following hosts or create a new host\n'
    for host in config['clients'][username]['hosts']:
        hostprompt += f'\t{host}\n'

    # Get user device/host so we can keep track of what to send to which
    # device/connection
    hostprompt += "Host: "
    client.sendall(hostprompt.encode())
    host = client.recv(args.recv_buf_size).decode('utf-8', 'replace').strip()


    last_message = 0
    if username in config['clients']:
        if host in config['clients'][username]['hosts']:
            if 'last-message' in config['clients'][username]['hosts'][host]:
                if len(history) >= config['clients'][username]['hosts'][host]['last-message']:
                    last_message = config['clients'][username]['hosts'][host]['last-message']
                    print(last_message)
                else:
                    last_message = 0
            else:
                config['clients'][username]['hosts'][host]['last-message'] = 0
        else:
            config['clients'][username]['hosts'][host] = {'last-message': 0}
    else:
        config['clients'][username] = {'hosts': {host: {'last-message': 0}}}

    # Keep track of the thread's buffer
    thread_buffer = queue.Queue()

    connection = {
            'key': f'{username}@{host}:{client.getpeername()[0]}:{client.getpeername()[1]}',
            'socket': client,
            'username': username,
            'host': host,
            'ip': client.getpeername()[0],
            'port': client.getpeername()[1],
            'out_buffer': thread_buffer,
            'last-message': last_message}

    print(connection)

    # Acquire lock so that we don't change the size of connections out
    # from under an iterator
    connections_lock.acquire()
    connections[f'{username}@{host}:{client.getpeername()[0]}:{client.getpeername()[1]}'] = connection
    connections_lock.release()

    connection['out_buffer'].put(f'CONNECTED\n'.encode())

    # Create a thread to handle input from that socket
    in_thread = threading.Thread(target=sock_input,
            args=(args, connection, history))

    # Create a thread to relay data out to the client
    out_thread = threading.Thread(target=sock_output,
            args=(connection, thread_buffer))

    config['clients'][username]['salt'] = salt.decode('iso-8859-1')
    config['clients'][username]['password'] = hashed_password

    # Start the producer and consumer
    in_thread.start()
    out_thread.start()

def master_queue_handler(buffer, config):
    while True:
        # Acquire lock on connections so that it won't change size while we
        # iterate through it
        connections_lock.acquire()
        for connection in connections.values():
            # Get the index of the most recent message
            last_message = len(history)

            # Send this client every message between the last one it saw and
            # the most recent message the server received
            last_read_message = connection['last-message']
            for message in history[last_read_message:last_message]:

                # If this message was sent by the current client, don't send it
                # back to them, that would be silly
                if not (message['sender'] == connection['username']
                        and message['host'] == connection['host']):
                    connection['out_buffer'].put(
                            "{}@{}: {}\n".format(message['sender'],
                                message['host'],
                                message['data']).encode())

            # Update last seen message for this client
            connection['last-message'] = last_message
            config['clients'][connection['username']]['hosts'][connection['host']]['last-message'] = last_message
        connections_lock.release()


def sock_input(args, connection, buffer):
    print("entering sock_input")
    connected = True
    # As long as we are connected, get input from the socket and enque it in
    # the master queue
    while connected:
        try:
            data = connection['socket'].recv(args.recv_buf_size)
            # If there was no received data, the connection is broken and will
            # never heal, so record that this socket is dead.
            if not data:
                connected = False;
            # There was data received, so process it and enqueue it in the master
            # queue
            else:
                cleaned_data = data.decode('utf-8', 'replace').strip()

                # Return the list of all active nodes
                if cleaned_data.find('Q NODE') == 0:
                    active_nodes = {'clients': {}}

                    # Run through all connections and stack them into a json
                    for active_connection in connections.values():
                        if active_connection['username'] not in active_nodes['clients']:
                            active_nodes['clients'][active_connection['username']] = []

                        active_nodes['clients'][active_connection['username']].append(active_connection['host'])

                    # Send results back to the querying client
                    connection['out_buffer'].put(
                            f'A NODE\n{json.dumps(active_nodes)}\n'.encode())

                elif cleaned_data.find('Q HOST') == 0:
                    pass
                elif cleaned_data.find('Q HIST') == 0:
                    try:
                        num_messages_str = cleaned_data[len('Q HIST'):]
                        num_messages = int(cleaned_data[len('Q HIST'):])
                        connection['out_buffer'].put( f'A HIST\n{history[len(history) - num_messages:]}\n'.encode())
                    except TypeError:
                        connection['out_buffer'].put(
                                f'A HIST\nERROR: {num_messages_str} not valid number\n'.encode())
                else:
                    print("\033[1m{}@{}:\033[0m {}".format(connection['username'],
                        connection['host'], cleaned_data))
                    message_package = {'sender': connection['username'],
                            'host': connection['host'],
                            'data': cleaned_data}
                    buffer.append(message_package)

                    # Assume that the client has echo checked it in the file to avoid
                    # the eventuality of a message_id being duplicated in the future
                    # causing collisions and messages disappearing
                    with open(args.history, 'a') as history_file:
                        history_file.write("{}\n".format(json.dumps(message_package)))
        except (ConnectionResetError, OSError):
            connected = False
    # Remove this socket from the list of connections, as it's no longer
    # connected.
    if connection['key'] in connections.keys():
        connections_lock.acquire()
        connections.pop(connection['key'])
        connections_lock.release()
    print("exiting sock_input")

def sock_output(connection, buffer):
    print("entering sock_output")
    connected = True
    # push data from inbox queue through this socket
    while connected:
        try:
            connection['socket'].sendall(buffer.get())
        except (socket.error, OSError):
            connected = False
        if connection['key'] not in connections:
            print(connection['key'], connections)
            connected = False
    print("exiting sock_output")

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
