
import select
import socket
import sys
import signal
import argparse
import threading
import ssl
from utils import *

SERVER_HOST = 'localhost'

stop_thread = False
state = -1
groups = None
group = None
users = None
user = None
invites = []

def get_and_send(client):
    while not stop_thread:
        data = sys.stdin.readline().strip()
        global state
        global groups
        global group
        global user
        if data:
            #in option select
            if state == 0:
                #view groups
                if data == '1':
                    state = 1
                    toSend = Data(7)
                    send(client.sock, toSend)
                #view users
                elif data == '2':
                    state = 2
                    toSend = Data(8)
                    send(client.sock, toSend)
                #view invites
                elif data == '3':
                    if len(invites) == 0:
                        print("no invites")
                        print('\nPlease select what you want to do\nTo view the groups, enter 1\nTo view the other users, enter 2\nTo view invites, enter 3\nTo create a group, enter 4', flush=True)
                        state = 0
                    else:
                        #state 6 for chosing an invite
                        state = 6
                        i = 0
                        print("accept an invite or /back to return")
                        for invite in invites:
                            print('Type',i,'for',invite.name)
                            i += 1
                #make group    
                elif data == '4':
                    state = 4
                    print('\nPlease enter the name of the group you want to make or /back to return to main page')

            #in group select
            elif state == 1:
                numGroups = len(groups)
                if data == '/back':
                    state = 0
                    print('\nPlease select what you want to do\nTo view the groups, enter 1\nTo view the other users, enter 2\nTo view invites, enter 3\nTo create a group, enter 4', flush=True)
                else: 
                    for i in range(numGroups):
                        if int(data) == i:
                            #state 3 indicates data is to be sent to group
                            state = 3
                            group = groups[i]
                            print("joined group", group.name)
                            toSend = Data(9)
                            toSend.addGroup(group)
                            send(client.sock, toSend)

            #in one on one chat select
            elif state == 2:
                numUsers = len(users)
                if data == '/back':
                    state = 0
                    print('\nPlease select what you want to do\nTo view the groups, enter 1\nTo view the other users, enter 2\nTo view invites, enter 3\nTo create a group, enter 4', flush = True)
                else:
                    for i in range(numUsers):
                        if int(data) == i:
                            state = 7
                            user = users[i]

            #in a group
            elif state == 3:
                if data == '/leave':
                    state = 0
                    #send leave message to server
                    toSend = Data(11)
                    toSend.addGroup(group)
                    send(client.sock, toSend)
                    group = None
                    print('\nPlease select what you want to do\nTo view the groups, enter 1\nTo view the other users, enter 2\nTo view invites, enter 3\nTo create a group, enter 4', flush = True)
                elif data == '/invite':
                    #request for member list
                    toSend = Data(13)
                    state = 5
                    send(client.sock, toSend)
                else:
                    toSend = Data(12)
                    toSend.addGroup(group)
                    toSend.addMessage(data)
                    send(client.sock, toSend)
                
            #creating a group
            elif state == 4:
                if data == '/back':
                    state = 0
                    print('\nPlease select what you want to do\nTo view the groups, enter 1\nTo view the other users, enter 2\nTo view invites, enter 3\nTo create a group, enter 4', flush = True)
                else:
                    group = GroupChat(data)
                    toSend = Data(6)
                    toSend.addMessage(data)
                    state = 3
                    send(client.sock, toSend)
            
            #inviting a member to group
            elif state == 5:
                if data == '/back':
                    state = 3
                else:
                    numUsers = len(users)
                    for i in range(numUsers):
                        if int(data) == i:
                            user = users[i]
                            #data on who to invite
                            toSend = Data(14)
                            toSend.addMember(user)
                            toSend.addGroup(group)
                            send(client.sock, toSend)
                            #return to in group state
                            state = 3
                    
            #chosing an invite
            elif state == 6:
                if data == '/back':
                    state = 0
                    print('\nPlease select what you want to do\nTo view the groups, enter 1\nTo view the other users, enter 2\nTo view invites, enter 3\nTo create a group, enter 4', flush = True)
                else:
                    for i in range(len(invites)):
                        if int(data) == i:
                            #state 3 indicates data is to be sent to group
                            state = 3
                            group = invites[i]
                            invites.remove(group)
                            toSend = Data(9)
                            toSend.addGroup(group)
                            send(client.sock, toSend)

            #in one on one chat
            elif state == 7:
                if data == '/back':
                    state = 0
                    print('\nPlease select what you want to do\nTo view the groups, enter 1\nTo view the other users, enter 2\nTo view invites, enter 3\nTo create a group, enter 4', flush = True)
                else:
                    toSend = Data(10)
                    toSend.addMember(user)
                    toSend.addMessage(data)
                    send(client.sock, toSend)







            

                


class ChatClient():
    """ A command line chat client using select """

    def __init__(self):
        global state
        global groups
        global users
        global invites
        self.name = input('Welcome to Chat Application\nPlease enter your name: ')
        self.connected = False
        self.host = input('Please enter the server ip: ')
        self.port = int(input('Please enter the port: '))

        #self.host = SERVER_HOST
        #self.port = 80

        self.context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

        # Initial prompt
        self.prompt = f'[{self.name}@{socket.gethostname()}]> '

        # Connect to server at port
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock = self.context.wrap_socket(
                self.sock, server_hostname=self.host)

            self.sock.connect((self.host, self.port))
            print(f'Now connected to chat server@ port {self.port}')
            self.connected = True

            # Send my name...
            send(self.sock, 'NAME: ' + self.name)
            data = receive(self.sock)

            # Contains client address, set it
            addr = data.split('CLIENT: ')[1]
            self.prompt = '[' + '@'.join((self.name, addr)) + ']> '

            #states show what should be displayed and done with user input
            #0 = choose what to do, 1 = send to group, 2 = send to one, 3 = join group, 4 = create group
            state = 0

            print('Please select what you want to do\nTo view the groups, enter 1\nTo view the other users, enter 2\nTo view invites, enter 3\nTo create a group, enter 4')

            threading.Thread(target=get_and_send, args=(self,)).start()

        except socket.error as e:
            print(f'Failed to connect to chat server @ port {self.port}')
            sys.exit(1)

    def cleanup(self):
        """Close the connection and wait for the thread to terminate."""
        self.sock.close()

    def run(self):
        """ Chat client main loop """
        global state
        global groups
        global users
        global invites
        while self.connected:
            try:
                #sys.stdout.write(self.prompt)
                #sys.stdout.flush()

                # Wait for input from stdin and socket
                # readable, writeable, exceptional = select.select([0, self.sock], [], [])
                readable, writeable, exceptional = select.select(
                    [self.sock], [], [])

                for sock in readable:
                    # if sock == 0:
                    #     data = sys.stdin.readline().strip()
                    #     if data:
                    #         send(self.sock, data)
                    if sock == self.sock:
                        data = receive(self.sock)
                        if not data:
                            print('Client shutting down.')
                            self.connected = False
                            break
                        else:
                            if data.indicator == 7:
                                #got list of groups
                                groups = data.groups
                                print('Pick a group to join or /back to return')
                                i = 0
                                for group in groups:
                                    print('Type',i,'for',group.name)
                                    i += 1
                            elif data.indicator == 8:
                                #got list of users
                                users = data.userList
                                print('Pick a user to chat with or /back to return')
                                i = 0
                                for user in users:
                                    print('Type',i,'for',user)
                                    i += 1

                            elif data.indicator == 20:
                                print(data.message)

                            elif data.indicator == 9:
                                #got list of users
                                users = data.userList
                                print('Pick a user to invite or /back to return')
                                i = 0
                                for user in users:
                                    print('Type',i,'for',user)
                                    i += 1

                            elif data.indicator == 10:
                                invites.append(data.group)
                                print("invited to: " +data.group.name)

                            elif data.indicator == 11:
                                if state == 7:
                                    print(data.message)

                            

            except KeyboardInterrupt:
                print(" Client interrupted. " "")
                stop_thread = True
                self.cleanup()
                break


if __name__ == '__main__':
    client = ChatClient()
    client.run()