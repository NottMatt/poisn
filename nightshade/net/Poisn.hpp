#ifndef POISN_H
#define POISN_H
#include <iostream>

#include "TCP.hpp"

typedef enum
{
    NONE,
    GENERAL,
    HOST_Q,
    NODE_Q,
    HIST_Q,
    RELAY_P,
    RELAY_L,
    RELAY_F,
} poisn_head;


typedef enum
{
    ERROR,
    NOT_CONNECTED,
    CONNECTED,
    LINK,
} poisn_state;

class Poisn: public TCP {
    public:
        /**
         * @brief inits the protocol
         */
        Poisn();


        /**
         * @brief inits the protocol, but specified the id of the last message seen
         * @param last_message the id of last message seen
         */
        Poisn(unsigned long last_message);


        /**
         * @brief finds the server using broadcast
         * @return success or not
         */
        bool find_server();


        /**
         * @brief finds server but is given an ip to try
         * @param ip a possible ip
         * @return success or not
         */
        bool find_server(char* ip);


        /**
         * @brief gets current state of poisn
         * @return enum with the state
         */
        poisn_state get_state();


        /**
         * @brief gets a message if there is on
         * @return an enum with what type of message, if any
         */
        poisn_head poll_message();
    private:
        unsigned long last_message;

        char* message_data;
        int message_length;

};

#endif
