
import select
import socket
import sys
import signal
import argparse
import threading
import ssl
from PyQt5.QtCore import QThread
from utils import *
from PyQt5.QtWidgets import QApplication, QComboBox, QSpacerItem, QSizePolicy, QHBoxLayout, QPushButton, QSpacerItem, QVBoxLayout, QWidget, QGridLayout, QLabel, QLineEdit, QTextEdit

SERVER_HOST = 'localhost'

stop_thread = False

class Client(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        grid = QGridLayout()
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        self.setLayout(vbox)

        vbox.addLayout(grid)
        vbox.addLayout(hbox)


        grid.addWidget(QLabel('IP Address'), 0, 0)
        grid.addWidget(QLabel('Port'), 1, 0)
        grid.addWidget(QLabel('Nick Name'), 3, 0)

        self.serverIp = QLineEdit()
        self.serverPort = QLineEdit()
        self.username = QLineEdit()

        grid.addWidget(self.serverIp, 0, 1)
        grid.addWidget(self.serverPort, 1, 1)
        grid.addWidget(self.username, 3, 1)

        connectButton = QPushButton('Connect')
        connectButton.pressed.connect(self.connectServer)
        
        cancelButton = QPushButton('Cancel')
        cancelButton.pressed.connect(self.close)

        hbox.addWidget(connectButton)
        hbox.addWidget(cancelButton)

        self.setWindowTitle('Connect to a server')
        #self.setGeometry() 
        self.show()

    def connectionWindow(self):
        grid = QGridLayout ()

        grid.addWidget(QLabel('Connected Clients'), 0, 0)
        grid.addWidget(QLabel('Chat Rooms'), 2, 0)
        grid.addWidget(QLabel('Connected Clients'), 0, 0)

        grid.addWidget(QComboBox(), 1, 0)
        grid.addWidget(QComboBox(), 3, 0)

        grid.addWidget(QPushButton('1 on 1 chat'), 1, 1)
        grid.addWidget(QPushButton('Create'), 3, 1)
        grid.addWidget(QPushButton('Join'), 4, 1)
        grid.addWidget(QPushButton('Close'), 5, 1)

        self.setLayout(grid)
        self.show()



    


    def connectServer(self):
        client = ChatClient(name = 'name', port = 80, host = SERVER_HOST )
        client.run()
        #if client.connected:
        self.connectionWindow()
    
    def close(self):
        sys.exit(app.exec_())






def get_and_send(client):
    while not stop_thread:
        data = sys.stdin.readline().strip()
        if data:
            send(client.sock, data)


class ChatClient(QThread):
    """ A command line chat client using select """

    def __init__(self, name, port, host):
        self.name = name
        self.connected = False
        #self.host = host
        #self.port = port

        self.host = SERVER_HOST
        self.port = 80

        self.context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

        # Initial prompt
        self.prompt = f'[{name}@{socket.gethostname()}]> '

        # Connect to server at port
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock = self.context.wrap_socket(
                self.sock, server_hostname=host)

            self.sock.connect((host, self.port))
            print(f'Now connected to chat server@ port {self.port}')
            self.connected = True

            # Send my name...
            send(self.sock, 'NAME: ' + self.name)
            data = receive(self.sock)

            # Contains client address, set it
            addr = data.split('CLIENT: ')[1]
            self.prompt = '[' + '@'.join((self.name, addr)) + ']> '

            threading.Thread(target=get_and_send, args=(self,)).start()

        except socket.error as e:
            print(f'Failed to connect to chat server @ port {self.port}')
            sys.exit(1)

    def cleanup(self):
        """Close the connection and wait for the thread to terminate."""
        self.sock.close()

    def run(self):
        """ Chat client main loop """
        while self.connected:
            try:
                sys.stdout.write(self.prompt)
                sys.stdout.flush()

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
                            sys.stdout.write(data + '\n')
                            sys.stdout.flush()

            except KeyboardInterrupt:
                print(" Client interrupted. " "")
                stop_thread = True
                self.cleanup()
                break


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Client()
    sys.exit(app.exec_())