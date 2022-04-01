#!/bin/python3

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