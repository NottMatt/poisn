#!/bin/python3
'''
Copyright (c) 2022, Kevin Lockwood <kevin-b-lockwood@gmail.com>
Copyright (c) 2022, the POISN developers.

SPDX-License-Identifier: BSD-2-Clause
'''

import argparse
import asyncio
import pathlib
import socket

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
    args = parser.parse_args()

    print(args)
    exit(0)

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
