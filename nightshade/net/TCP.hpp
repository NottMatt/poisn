#ifndef TCP_H
#define TCP_H
#include <poll.h>

#define POLLBAD (-1)
#define POLLOK (1)
#define POLLHUNGUP (0)

typedef enum
{
    TCP_BAD = -1,
    TCP_HUP = 0,
    TCP_OK = 1,
} tcp_status;

class TCP {
    public:

        //void sendPTL(int protocol);
        void sendPTL(char* head, int head_len, char* data, int data_len);

        tcp_status get_from_poll();

        bool tcp_connect();
        bool validate();

        TCP(char* ip, int port);
        virtual void run();

    private:
        bool makeTCP();

        // probably just gonna allocate large buffers for this
        // and expand them if we are given something too big
        // raw in buffer
        int _message_len;
        char* _message_buffer;

        // raw out buffer
        int _out_len;
        char* _out_buffer;


        // socket stuff
        struct pollfd _pfd;
        int _theSock;


        // address stuff
        char* _ip;
        int _port;
};

void progressBarThread(long& top, int& bottom, int width);
void progressBarWithBufThread(long& top, int& bottom, int width, int& numBuffs);
void drawProgress(double percent, int width);
void drawProgressWithBufCount(double percent, int width, int numBuffs);
void drawProgressRaw(double percent, int width);

#endif
