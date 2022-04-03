#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <poll.h>
#include <iostream>
#include <unistd.h>
#include <cstring>
#include <thread>

using namespace std;
#include "TCP.hpp"


/**
 * makes a tcp socket
 * @return success or not
 */
bool TCP::makeTCP()
{
    bool success = true;
    if ((_theSock = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
        perror("Socket failed to make\n");
        success = false;
    }

    return success;
}


/**
 * tries to connect
 * @return whether we connected or not
 */
bool TCP::validate()
{
    // TODO is this useful?
    bool successful = true;
    if (!tcp_connect())
    {
        successful = false;
        printf("oh no!\n");
    }

    return successful;
}


/**
 * sends over the socket
 * @param protocol
 * @return
 */
void TCP::sendPTL(char* head, int head_len, char* data, int data_len)
{
    // create message and send it
    // TODO make good
    //_toSend.protocol = protocol;

    // send
    //if (send(_theSock, (const void*)&_toSend, sizeof(struct generalTCP), 0) < 0)
    //{
        //perror("send wackiness");
    //}
}


/**
 * waits for poll to trigger, then error checks, and sets the buf packet
 * 0 for fine, 1 for hung up and -1 for bad
 * @param waitForFill to wait for the buffer to fill up or not
 * @return int of what happened
 */
tcp_status TCP::get_from_poll()
{
    tcp_status status = TCP_OK;
    int peek;
    int len;
    int poll_value = poll(&_pfd, 1, 1000);
    if (poll_value == 0)
    {
        // time out, this is ok
        printf("poll timeout\n");
    }
    else if (poll_value < 0)
    {
        // error, this is bad
        perror("poll error:\n");
        status = TCP_BAD;
    }
    else if (poll_value > 0)
    {
        // normal, probably good
        if (_theSock < 0)
        {
            // very bad, though shouldn't happen
            printf("Socket: %d\n", _theSock);
            exit(-1);
        }

        if (_pfd.revents & POLLHUP)
        {
            // they hung up
            perror("hung up:\n");
            status = TCP_HUP;
        }
        else if (_pfd.revents & POLLIN)
        {
            // data to read
            peek = recv(_theSock, NULL, NULL, MSG_PEEK | MSG_DONTWAIT);

            // they broke the connection
            if (peek == 0)
            {
                // shouldn't happen
                perror("Oh no peek == 0: \n");
                status = TCP_HUP;
            }

            // error
            if (peek < 0)
            {
                // peek error
                printf("error: %d\n", peek);
                printf("socket: %d\n", _theSock);
                perror("msg error");
                exit(-1);
            }

            // delete old data
            if (_message_buffer != nullptr)
            {
                free(_message_buffer);
            }
            // allocate new data
            _message_buffer = (char*)calloc(1, peek);
            _message_len = peek;

            // copy from the socket
            len = recv(_theSock, _message_buffer, peek, 0);

            // should be the same
            if (len != _message_len)
            {
                printf("len %d message_len %d\n", len, _message_len);
                perror("Oh no:\n");
            }
        }
    }

    return status;
}


/**
 * connects our tcp socket to the server, sends our key
 * @param ip the server ip
 * @return if we did it
 */
bool TCP::tcp_connect()
{
    bool success = true;
    struct sockaddr_in tcpServer;
    socklen_t addrlen = sizeof(tcpServer);

    memset(&tcpServer, 0, addrlen);
    tcpServer.sin_family = AF_INET;
    tcpServer.sin_addr.s_addr= inet_addr(_ip);
    tcpServer.sin_port =  htons(_port);

    // try to connect, if yes then send the key
    if (connect(_theSock, (struct sockaddr*)&tcpServer, addrlen) < 0)
    {
        perror("Connect problems\n");
        success = false;
    }
    printf("connected!\n");

    return success;
}



/**
 * the constructor for the tcp thing
 * @param ip server ip
 * @param type what we are doing with the tcp socket
 * @param file filename for uploading
 */
TCP::TCP(char* ip, int port) : _ip(ip), _port(port)
{
    // make the socket
    makeTCP();

    _message_len = 0;
    _message_buffer = nullptr;

    _out_len = 0;
    _out_buffer = nullptr;

    // set poll var
    _pfd.fd = _theSock;
    _pfd.events = POLLIN | POLLHUP;
    _pfd.revents = 0;
}


/**
 * all things that inherit from tcp must make a run function
 * this function will be the main driver
 * should be able to be run on a thread
 */
void TCP::run()
{
    cout << "Oh no" << endl;
}









void progressBarThread(long& top, int& bottom, int width)
{
    while (top != bottom)
    {
        drawProgress((float) top / (float) bottom, width);
    }
}

void progressBarWithBufThread(long& top, int& bottom, int width, int& numBuffs)
{
    while (top != bottom)
    {
        drawProgressWithBufCount((float) top / (float) bottom, width, numBuffs);
        this_thread::sleep_for(500ms);
    }
}

void drawProgress(double percent, int width)
{
    drawProgressRaw(percent, width);
    cout << "\r";
    cout.flush();
}


void drawProgressWithBufCount(double percent, int width, int numBuffs)
{
    drawProgressRaw(percent, width);
    //cout << " " << numBuffs << " / " << MUSIC_BUFFERS << "\r";
    cout.flush();
}


/**
 * makes the pretty progress bar
 * stolen from stack overflow btw
 * @param percent how far along we want this
 * @param width the max width
 */
void drawProgressRaw(double percent, int width)
{
    cout << "[";
    int pos = width * percent;
    for (int i = 0; i < width; ++i) {
        if (i < pos) cout << "=";
        else if (i == pos) cout << ">";
        else cout << " ";
    }
    cout << "] " << int(percent * 100.0) << " %";
}
