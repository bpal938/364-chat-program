import select
import socket
import sys
import signal
import argparse
import ssl

from utils import *

SERVER_HOST = 'localhost'


class ChatServer(object):
    """ An example chat server using select """

    def __init__(self, port, backlog=5):
        self.clients = 0
        self.clientmap = {}
        self.outputs = []  # list output sockets
        

        self.context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        self.context.load_cert_chain(certfile="cert.pem", keyfile="cert.pem")
        self.context.load_verify_locations('cert.pem')
        self.context.set_ciphers('AES128-SHA')

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((SERVER_HOST, port))
        self.server.listen(backlog)                
        self.server = self.context.wrap_socket(self.server, server_side=True)

        # Catch keyboard interrupts
        signal.signal(signal.SIGINT, self.sighandler)

        print(f'Server listening to port: {port} ...')

    def sighandler(self, signum, frame):
        """ Clean up client outputs"""
        print('Shutting down server...')

        # Close existing client sockets
        for output in self.outputs:
            output.close()

        self.server.close()

    def get_client_name(self, client):
        """ Return the name of the client """
        info = self.clientmap[client]
        host, name = info[0][0], info[1]
        return '@'.join((name, host))

    def get_group_members(self, client):
        info = self.clientmap[client]
        members = info[2]


    def run(self):
        # inputs = [self.server, sys.stdin]
        inputs = [self.server]
        self.outputs = []

        self.users = []
        self.groupChats = []
        self.groupSocks = []


        running = True
        while running:
            try:
                readable, writeable, exceptional = select.select(
                    inputs, self.outputs, [])
            except select.error as e:
                break

            for sock in readable:
                sys.stdout.flush()
                if sock == self.server:
                    # handle the server socket
                    client, address = self.server.accept()

                    print(
                        f'Chat server: got connection {client.fileno()} from {address}')
                    # Read the login name
                    cname = receive(client).split('NAME: ')[1]

                    # Compute client name and send back
                    self.clients += 1
                    send(client, f'CLIENT: {str(address[0])}')
                    inputs.append(client)
                    self.users.append(cname)

                    self.clientmap[client] = (address, cname, [])
                    
                    
                    self.outputs.append(client)

                # elif sock == sys.stdin:
                #     # didn't test sys.stdin on windows system
                #     # handle standard input
                #     cmd = sys.stdin.readline().strip()
                #     if cmd == 'list':
                #         print(self.clientmap.values())
                #     elif cmd == 'quit':
                #         running = False
                else:
                    # handle all other sockets
                    try:
                        data = receive(sock)
                        if data:
                            #check first 
                            indicator = data.indicator

                            #send normal message to users in current group chat
                            if indicator == 0:
                                userGroup = None
                                #find the group chat that user is in
                                for group in self.groupChats:
                                    if group.id == data.group.id:
                                        userGroup = group
                                #if there is at least one member
                                if len(userGroup) != 0:
                                    #create message (0 as indicator indicates a normal message)
                                    msg = f'\n#[{self.get_client_name(sock)}]>> {data.message}'
                                    data = Data(0).addMessage(msg)
                                    #send to each member
                                    for sendee in userGroup.members:
                                        send(sendee, data)

                            #user returning to connected client section
                            elif indicator == 1:
                                if data.group != None:
                                    msg = f'\n(Now hung up: Client from {self.get_client_name(sock)})'
                                    #create left the chat message for members (1 indicates a user left the chat)
                                    leaveData = Data(1).addMessage(msg).addRemovedMember(self.get_client_name)
                                    #find the group chat that user was in
                                    for group in self.groupChats:
                                        if group.id == data.group.id:
                                            #remove user from this group chat
                                            group.members.remove(sock)
                                            #if user was owner of group
                                            if group.owner == sock:
                                                #make another user host
                                                group.owner = group.members[0]
                                                #alert all users in group of this change
                                                leaveData.addNewHost(group.members[0], self.get_client_name(group.members[0]))
                                            #send leave data to other members of the group
                                            for member in group.members:
                                                send(member, leaveData)
                                #create data with list of people and groups (2 indicates sending of all data)
                                data = Data(2).addUserList(self.clientmap).addGroups(self.groupChats)
                                #send back to client
                                send(sock, data)

                            #user joining chat
                            elif indicator == 2:
                                #find group that user is joining
                                for group in self.groupChats:
                                        if group.id == data.group.id:
                                            #create join message to send to members of the group (3 indicates new member of group)
                                            msg = f'\n(Connected: New client ({self.clients}) from {self.get_client_name(client)})'
                                            joinData = Data(3).addMessage(msg).addMember(self.get_client_name)
                                            for member in group.members:
                                                send(member, joinData)
                                            group.addUser(sock)

                            #user inviting other user
                            elif indicator == 3:
                                #user inviting other user
                                invited = data.member
                                #invite contains the group they are being invited to (indicator 4)
                                invite = Data(4).addGroup(data.group)
                                send(invited, invite)

                            #new user
                            elif indicator == 4:
                                #create data with list of people and groups
                                data = Data(2).addUserList(self.clientmap).addGroups(self.groupChats)
                                #send back to client
                                send(sock, data)
                                #create message containing info about new user (indicator 5)
                                msg = Data(5).addUserList([User(self.get_client_name, sock)])
                                for user in self.users:
                                    send(msg, msg)

                            #sending normal message to users current one on one chat
                            elif indicator == 5:
                                otherMember = data.member 
                                msg = f'\n#[{self.get_client_name(sock)}]>> {data.message}'
                                data = Data(6).addMessage(msg)
                                send(otherMember, data)

                            #creating a new group
                            elif indicator == 6:
                                name = data.message
                                group = GroupChat(name)
                                group.addUser(self.get_client_name(sock))
                                self.groupChats.append(group)
                                sockGroup = SockGroup(name)
                                sockGroup.socks.append(sock)
                                self.groupSocks.append(sockGroup)

                            #request for group info
                            elif indicator == 7:
                                print('got group request')
                                toSend = Data(7)
                                toSend.addGroups(self.groupChats)
                                send(sock, toSend)
                            
                            #request for user info
                            elif indicator == 8:
                                print('got user request')
                                toSend = Data(8)
                                toSend.addUserList(self.users)
                                send(sock, toSend)
                            
                            #join group chat
                            elif indicator == 9:
                                groupName = data.group.name
                                for groupChat in self.groupChats:
                                    if groupChat.name == groupName:
                                        groupChat.addUser(self.get_client_name(sock))
                                for sockGroup in self.groupSocks:
                                    if sockGroup.name == groupName:
                                        msg = self.get_client_name(sock) + " joined the group"
                                        toSend = Data(20)
                                        toSend.addMessage(msg)
                                        for socket in sockGroup.socks:
                                            send(socket, toSend)
                                        sockGroup.socks.append(sock)

                                print('user joining group', data.group.name)

                            #message to one on one chat
                            elif indicator == 10:
                                chattingMember = data.member
                                toSend = Data(11)
                                msg = self.get_client_name(sock) + ' >> ' + data.message
                                toSend.addMessage(msg)
                                for socket in self.outputs:
                                    if self.get_client_name(socket).split('@')[0] == chattingMember:
                                        send(socket, toSend)


                            #user leaving group
                            elif indicator == 11:
                                groupName = data.group.name
                                for groupChat in self.groupChats:
                                    if groupChat.name == groupName:
                                        groupChat.members.remove(self.get_client_name(sock))
                                        if len(groupChat.members) == 0:
                                            self.groupChats.remove(groupChat)
                                for sockGroup in self.groupSocks:
                                    if sockGroup.name == groupName:
                                        msg = self.get_client_name(sock) + " left the group"
                                        toSend = Data(20)
                                        toSend.addMessage(msg)
                                        for socket in sockGroup.socks:
                                            if socket != sock:
                                                send(socket, toSend)
                                        sockGroup.socks.remove(sock)
                                        if len(sockGroup.socks) == 0:
                                            self.groupSocks.remove(sockGroup)
                                            
                                print('user leaving group', data.group.name)

                            #message to group
                            elif indicator == 12:
                                msg = self.get_client_name(sock) + ' >> ' + data.message
                                groupName = data.group.name
                                for sockGroup in self.groupSocks:
                                    if sockGroup.name == groupName:
                                        toSend = Data(20)
                                        toSend.addMessage(msg)
                                        for socket in sockGroup.socks:
                                            if socket != sock:
                                                send(socket, toSend)

                            #request for all members
                            elif indicator == 13:
                                toSend = Data(9)
                                toSend.addUserList(self.users)
                                send(sock, toSend)

                            #invite sent to user
                            elif indicator == 14:
                                invitedUser = data.member
                                toSend = Data(10)
                                toSend.addGroup(data.group)
                                for socket in self.outputs:
                                    if self.get_client_name(socket).split('@')[0] == invitedUser:
                                        send(socket, toSend)



                            
                        else:
                            print(f'Chat server: {sock.fileno()} hung up')
                            self.clients -= 1
                            sock.close()
                            inputs.remove(sock)
                            self.outputs.remove(sock)

                            # Sending client leaving information to others
                            msg = f'\n(Now hung up: Client from {self.get_client_name(sock)})'

                            for output in self.outputs:
                                send(output, msg)
                    except socket.error as e:
                        # Remove
                        inputs.remove(sock)
                        self.outputs.remove(sock)
                        
        self.server.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Socket Server Example with Select')
    parser.add_argument('--name', action="store", dest="name", required=True)
    parser.add_argument('--port', action="store",
                        dest="port", type=int, required=True)
    given_args = parser.parse_args()
    port = given_args.port
    name = given_args.name

    server = ChatServer(port)
    server.run()


