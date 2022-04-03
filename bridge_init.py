#!/bin/python3

import os
import sys
import weakref

port = sys.argv[1]
print(port)
command = "websockify --daemon {webport} 10.55.10.147:{tcpport}".format(webport=str(int(port) + 1), tcpport=str(port))

os.system(command)