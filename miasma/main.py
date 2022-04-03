#!/bin/python3
'''
Copyright (c) 2022, Matthew Tiemersma <mattdtie@gmail.com>
Copyright (c) 2022, the POISN developers.

SPDX-License-Identifier: BSD-2-Clause
'''

from tkinter import *
from socket import *
import queue
import threading
from io import StringIO
from contextlib import redirect_stdout
import subprocess
import os
import json


def main():
    # get user text
    node_update = False

    inp_text = (inp_field.get(1.0, 'end'))[1:-1]
    flag = False
    if '\n' in inp_text and len(inp_text) > 1:
        message = inp_field.get(1.0, 'end')[0:-1]
        outbuffer.put(message)
        inp_field.delete(1.0, 'end')
        buf = open('buffer', 'a')
        buf.write(message)
        buf.close()
        last_f = open('last', 'w')
        last_f.write(message)
        last_f.close()
        if code_active:
            execute_py()
        flag = True
    root.after(1, main)

    # inbuffer
    if not inbuffer.empty():
        tcp_message = inbuffer.get()
        data = tcp_message

        if data.split('\n')[0].split(' ')[1] == 'NODE':
            node_update = True
            for n in data.split('\n')[1:]:
                node_f = open('nodes', 'a')
                node_f.write(n)
                node_f.close()
        else:
            last_f = open('last', 'w')
            last_f.write(data)
            last_f.close()
            if code_active:
                execute_py()

            flag=True
            buf_in = open('buffer', 'a')
            buf_in.write(data)
            buf_in.close()


    # Node update
    if node_update:
        for n in roster_nodes:
            n.pack_forget()
        node_f = open('nodes', 'r')
        nodes_arr = [username]
        for i in node_f.readlines():
            newnode = i.replace('\n', '')
            if len(newnode) > 20:
                newnode = newnode[0:20]
            nodes_arr = nodes_arr + [newnode]
        for i in range(len(nodes_arr)):
            node_f = Frame(roster, bg=LIGHT_COLOR, width=roster.winfo_width(), height=10)
            node_l = Label(node_f, text=nodes_arr[i], bg=LIGHT_COLOR, fg=FONT_COLOR, justify=LEFT, width=22)
            node_l.pack(anchor='ne')
            node_f.pack(side=TOP)
            roster_nodes.append(node_f)

    # write from buffer

    buf = open('buffer', 'r')
    if (flag):
        b_field.config(state=NORMAL)
        b_field.delete(1.0, 'end')
        b_field.insert('end', buf.read())
        b_field.config(state=DISABLED)
        b_field.yview(END)
        flag = False
    buf.close()


def execute_py():
    f = StringIO()
    with redirect_stdout(f):
            exec(open('code_file.py').read())
    output_str = f.getvalue()
    if len(output_str) > 0:
        outbuffer.put(output_str)
        inbuffer.put(output_str)

    a_button.config(bg=LIGHT_COLOR)
    globals()['code_active'] = False
    print(output_str)


def socket_in(in_buffer, is_connected):
    while is_connected:
        # TCP read
        tcp_message = str(conn.recv(2048).decode())
        if not tcp_message:
            is_connected = False
        else:
            in_buffer.put(tcp_message)

        print(tcp_message)


def socket_out(out_buffer, is_connected):
    while is_connected:
        out_msg = out_buffer.get()
        conn.sendall(out_msg.encode())


def activate():
    print('activate')
    # get content from textbox
    a_code = t_field.get(1.0, 'end')
    a_file = open('code_file.py', 'w')
    a_file.write("#!/bin/python3\n" + a_code)
    a_file.close()
    a_button.config(bg=WARN_COLOR)
    globals()['code_active'] = True


try:
    # print('')
    th = open('themes/light/theme.json', 'r')
    theme = json.load(th)
    TERM_COLOR = theme['colors']['terminal_pane']
    EDIT_COLOR = theme['colors']['editor_pane']
    DARK_COLOR = theme['colors']['dark_accent']
    LIGHT_COLOR = theme['colors']['light_accent']
    FONT_COLOR = theme['colors']['font']
    WARN_COLOR = theme['colors']['warn']
    username = 'nottmatt'

    # TCP connection

    IP = '10.55.10.147'
    PORT = 5555
    conn = socket(AF_INET, SOCK_STREAM)
    conn.connect((IP, PORT))
    print('Connected')
    connected = True

    outbuffer = queue.Queue()
    inbuffer = queue.Queue()

    sock_t_in = threading.Thread(target=socket_in, args=(inbuffer, connected))
    sock_t_out = threading.Thread(target=socket_out, args=(outbuffer, connected))
    sock_t_out.start()
    sock_t_in.start()

    code_active = False

finally:

    # initialize window
    WIDTH = 1000
    HEIGHT = 700
    ROST_WIDTH = 200
    root = Tk()
    root.iconbitmap('./miasma_logo.ico')

    root.wm_title('Miasma - Poisn Client')
    root['bg'] = TERM_COLOR
    root.geometry('{w}x{h}+50+50'.format(w=WIDTH + ROST_WIDTH, h=HEIGHT))
    Grid.rowconfigure(root, 0, weight=1)
    Grid.columnconfigure(root, 0, weight=20)
    Grid.columnconfigure(root, 1, weight=30)
    Grid.columnconfigure(root, 2, weight=1)

    # EDITOR window
    editor = Frame(root)
    editor['bg'] = DARK_COLOR
    editor.grid(row=0, column=0, sticky="NSEW")

    # FEED window
    feed = Frame(root)
    feed['bg'] = TERM_COLOR
    feed.grid(row=0, column=1, sticky="NSEW")

    # ROSTER window
    roster = Frame(root, width=ROST_WIDTH)
    roster['bg'] = LIGHT_COLOR
    roster.grid(row=0, column=2, sticky="NSE")

    # EDITOR components
    # activate button
    a_frame1 = Frame(editor, bg=DARK_COLOR, height=15, width=0)
    a_frame2 = Frame(editor, bg=DARK_COLOR, height=15, width=0)
    a_button = Button(editor, text='ACTIVATE  >>', bd=0, bg=LIGHT_COLOR, fg=FONT_COLOR,
                      activebackground=WARN_COLOR, height=2, width=20, command=activate)
    a_frame1.pack(side=BOTTOM, anchor=SE)
    a_button.pack(side=BOTTOM, anchor=SE)
    a_frame2.pack(side=BOTTOM, anchor=SE)

    # text field
    t_frame = Frame(editor, bg=EDIT_COLOR)
    t_frame.pack(side=BOTTOM, fill=BOTH, expand=True)
    Grid.rowconfigure(t_frame, 0, weight=1)
    Grid.columnconfigure(t_frame, 0, weight=1)
    Grid.columnconfigure(t_frame, 1, weight=100)
    t_field = Text(t_frame, width=t_frame.winfo_width(), height=t_frame.winfo_height(),
                   bg=EDIT_COLOR, fg=FONT_COLOR, bd=0)
    t_field.grid(row=0, column=1, sticky="NSEW")
    sb = Scrollbar(t_frame)
    sb.grid(row=0, column=0, sticky="NSW")
    t_field.config(yscrollcommand=sb.set)
    sb.config(command=t_field.yview)

    a_frame3 = Frame(editor, bg=DARK_COLOR, height=15, width=0)
    a_frame3.pack(side=BOTTOM, anchor=SE)

    # FEED Components
    # input bar
    i_frame1 = Frame(feed, bg=TERM_COLOR, height=15, width=0)
    i_frame2 = Frame(feed, bg=TERM_COLOR, height=15, width=0)

    inp_bar = Frame(feed, height = 1, width=feed.winfo_width(), bg=LIGHT_COLOR)
    i_frame1.pack(side=BOTTOM, anchor=SW)
    inp_bar.pack(side=BOTTOM, anchor=SE, fill=X, padx=10)

    Grid.rowconfigure(inp_bar, 0, weight=1)
    Grid.columnconfigure(inp_bar, 0, weight=1)

    inp_field = Text(inp_bar, width=inp_bar.winfo_width(), height=1,
                     bg=LIGHT_COLOR, fg=FONT_COLOR, bd=0)
    inp_field.pack(fill=BOTH, padx=10)

    # text buffer
    b_frame = Frame(feed, bg=TERM_COLOR, height=feed.winfo_height(), width=feed.winfo_width())
    b_frame.pack(side=TOP, fill=BOTH, expand=True)
    Grid.rowconfigure(b_frame, 0, weight=1)
    Grid.columnconfigure(b_frame, 0, weight=1)

    b_field = Text(b_frame, state=DISABLED,
                   width=b_frame.winfo_width(), height=b_frame.winfo_height(),
                   bg=TERM_COLOR, fg=FONT_COLOR, bd=0)

    b_field.grid(row=0, column=0, sticky="NSEW")
    sb_f = Scrollbar(b_frame)
    sb_f.config(command=b_field.yview)
    b_field.config(yscrollcommand=sb_f.set)

    # Roster components
    node_f_b = Frame(roster, bg=LIGHT_COLOR, width=roster.winfo_width(), height=10)
    node_l_b = Label(node_f_b, text='Active Nodes', bg=LIGHT_COLOR, fg=FONT_COLOR, justify=LEFT, width=22)
    node_l_b.pack(anchor='ne')
    node_f_b.pack(side=TOP, anchor='ne')
    roster_nodes = []

    root.after(1, main)
    root.mainloop()
    buf = open('buffer', 'w')
    buf.write('')
    buf.close()
    exit()