#!/bin/python3
'''
Copyright (c) 2022, Matthew Tiemersma <mattdtie@gmail.com>
Copyright (c) 2022, the POISN developers.

SPDX-License-Identifier: BSD-2-Clause
'''

from ctypes import windll
from tkinter import *
from socket import *


def main():
    # get user text
    node_update = False

    inp_text = (inp_field.get(1.0, 'end'))[1:-1]
    flag = False
    if ('\n' in inp_text and len(inp_text) > 1):
        message = inp_field.get(1.0, 'end')[0:-1]
        print(message)
        inp_field.delete(1.0, 'end')
        buf = open('buffer', 'a')
        buf.write(message)
        buf.close()
        flag = True
        if 'node' in message:
            node_update = True
    root.after(1, main)

    # TCP stuff

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
            node_f = Frame(roster, bg='#333333', width=roster.winfo_width(), height=10)
            node_l = Label(node_f, text=nodes_arr[i], bg='#333333', fg='#888888', justify=LEFT, width=22)
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
        flag = False
    buf.close()


def activate():
    print('activate')
    # get content from textbox
    a_code = t_field.get(1.0, 'end')
    a_file = open('code_file.py', 'w')
    a_file.write(a_code)
    a_file.close()
    a_button.config(bg='#89402e')


try:
    # print('')
    username = 'nottmatt'
    windll.shcore.SetProcessDpiAwareness(1)

    # TCP connection

    IP = '10.55.10.147'
    PORT = 5555
    conn = socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((IP, PORT))

    print('Connected')
finally:

    # initialize window
    WIDTH = 1000
    HEIGHT = 700
    ROST_WIDTH = 200
    root = Tk()
    root.iconbitmap('./miasma_logo.ico')

    root.wm_title('Miasma - Poisn Client')
    root['bg'] = '#1F1F1F'
    root.geometry('{w}x{h}+50+50'.format(w=WIDTH + ROST_WIDTH, h=HEIGHT))
    Grid.rowconfigure(root, 0, weight=1)
    Grid.columnconfigure(root, 0, weight=20)
    Grid.columnconfigure(root, 1, weight=30)
    Grid.columnconfigure(root, 2, weight=1)

    # EDITOR window
    editor = Frame(root)
    editor['bg'] = '#242424'
    editor.grid(row=0, column=0, sticky="NSEW")

    # FEED window
    feed = Frame(root)
    feed['bg'] = '#1F1F1F'
    feed.grid(row=0, column=1, sticky="NSEW")

    # ROSTER window
    roster = Frame(root, width=ROST_WIDTH)
    roster['bg'] = '#333333'
    roster.grid(row=0, column=2, sticky="NSE")

    # EDITOR components
    # activate button
    a_frame1 = Frame(editor, bg='#242424', height=15, width=0)
    a_frame2 = Frame(editor, bg='#242424', height=15, width=0)
    a_button = Button(editor, text='ACTIVATE  >>', bd=0, bg='#333333', fg='#888888',
                      activebackground='#404040', height=2, width=20, command=activate)
    a_frame1.pack(side=BOTTOM, anchor=SE)
    a_button.pack(side=BOTTOM, anchor=SE)
    a_frame2.pack(side=BOTTOM, anchor=SE)

    # text field
    t_frame = Frame(editor, bg='#272727')
    t_frame.pack(side=BOTTOM, fill=BOTH, expand=True)
    Grid.rowconfigure(t_frame, 0, weight=1)
    Grid.columnconfigure(t_frame, 0, weight=1)
    Grid.columnconfigure(t_frame, 1, weight=100)
    t_field = Text(t_frame, width=t_frame.winfo_width(), height=t_frame.winfo_height(),
                   bg='#272727', fg='#888888', bd=0)
    t_field.grid(row=0, column=1, sticky="NSEW")
    sb = Scrollbar(t_frame)
    sb.grid(row=0, column=0, sticky="NSW")
    t_field.config(yscrollcommand=sb.set)
    sb.config(command=t_field.yview)

    a_frame3 = Frame(editor, bg='#242424', height=15, width=0)
    a_frame3.pack(side=BOTTOM, anchor=SE)

    # FEED Components
    # input bar
    i_frame1 = Frame(feed, bg='#1F1F1F', height=15, width=0)
    i_frame2 = Frame(feed, bg='#1F1F1F', height=15, width=0)

    inp_bar = Frame(feed, height = 1, width=feed.winfo_width(), bg='#333333')
    i_frame1.pack(side=BOTTOM, anchor=SW)
    inp_bar.pack(side=BOTTOM, anchor=SE, fill=X, padx=10)

    Grid.rowconfigure(inp_bar, 0, weight=1)
    Grid.columnconfigure(inp_bar, 0, weight=1)

    inp_field = Text(inp_bar, width=inp_bar.winfo_width(), height=1,
                     bg='#333333', fg='#888888', bd=0)
    inp_field.pack(fill=BOTH, padx=10)

    # text buffer
    b_frame = Frame(feed, bg='#1F1F1F', height=feed.winfo_height(), width=feed.winfo_width())
    b_frame.pack(side=TOP, fill=BOTH, expand=True)
    Grid.rowconfigure(b_frame, 0, weight=1)
    Grid.columnconfigure(b_frame, 0, weight=1)

    b_field = Text(b_frame, state=DISABLED,
                   width=b_frame.winfo_width(), height=b_frame.winfo_height(),
                   bg='#1F1F1F', fg='#888888', bd=0)

    b_field.grid(row=0, column=0, sticky="NSEW")
    sb_f = Scrollbar(b_frame)
    sb_f.config(command=b_field.yview)
    b_field.config(yscrollcommand=sb_f.set)

    # Roster components
    node_f_b = Frame(roster, bg='#333333', width=roster.winfo_width(), height=10)
    node_l_b = Label(node_f_b, text='Active Nodes', bg='#333333', fg='#666666', justify=LEFT, width=22)
    node_l_b.pack(anchor='ne')
    node_f_b.pack(side=TOP, anchor='ne')
    roster_nodes = []

    root.after(1, main)
    root.mainloop()
    buf = open('buffer', 'w')
    buf.write('')
    buf.close()