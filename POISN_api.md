# Network-Shared I/O Protocol API definition

### Poisn is an Application Layer Protocol for multi-end communication:

The structure that this protocol supports consists of a central server and an arbitrary number of connected nodes.

    N N N      Peer Nodes
     \|/
      S        Server
      |
      N        Client Node

### Communication Patterns:
Nodes communicate with the central server, and the server relays the data to all other connected nodes over a persistent TCP connection. The data can be treated as would a standard input/output buffer, or integrated with a frontend UI that implements the POISN chat API.

The standard communication pattern consists of a
***header field***
and
***data field***
that contain context-specific information.

    HEAD: header identifies the format of the message
    DATA: data field contains all text to be transfered to the server or to node.

## Standard Server-Client Variations

* **General Prompt/Response**

        HEAD: General
        <Plaintext>

    * User Identification
    * User Authenication
    * Host Selection Response
    * Node Query
    * History Query
<br><br>

* **Host Query**

        HEAD: Host_Q
        <List of hosts associated with user>
<br>

* **Node Query Response**

        HEAD: Node_Q
        <List of active nodes>
<br>

* **History Query Response**

        HEAD: Hist_Q
        <List of messages since queried history index>
<br>

## Standard Relayed Variations

* **Plaintext Message**

        HEAD: Relay_P
        <Plaintext message>
<br>

* **Link Message**

        HEAD: Relay_L
        <Plaintext link URL>
<br>

* **File Encoding Message**

        HEAD: Relay_F filetype
        <Byte encoding of file>
