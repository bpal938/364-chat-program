import socket
import pickle
import struct

def send(channel, *args):
    buffer = pickle.dumps(args)
    value = socket.htonl(len(buffer))
    size = struct.pack("L", value)
    channel.send(size)
    channel.send(buffer)

def receive(channel):
    size = struct.calcsize("L")
    size = channel.recv(size)
    try:
        size = socket.ntohl(struct.unpack("L", size)[0])
    except struct.error as e:
        return ''
    buf = ""
    while len(buf) < size:
        buf = channel.recv(size - len(buf))
    return pickle.loads(buf)[0]

class Data():
    def __init__(self, indicator):
        self.indicator = indicator
    
    def addUserList(self, userList):
        self.userList = userList

    def addMessage(self, message):
        self.message = message

    def addRemovedMember(self, toRemove):
        self.toRemove = toRemove

    def addNewHost(self, sock, name):
        self.groupHost = [sock, name]

    def addGroups(self, groups):
        self.group = groups

    def addMember(self, toAdd):
        self.member = toAdd
    
    def addGroup(self, group):
        self.group = group
    
class GroupChat():
    def __init__(self, user):
        self.owner = user
        self.members = []
        self.members.append(user)
    
    def addUser(self, user):
        self.members.append(user)


class User():
    def __init__(self, name, sock):
        self.userName = name
        self.sock = sock
        self.chat = None
    
    def joinChat(self, chat):
        self.chat = chat
    
    def leaveGroup(self):
        self.chat = None