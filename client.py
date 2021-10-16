import sys
from PyQt5.QtWidgets import QApplication, QSpacerItem, QSizePolicy, QHBoxLayout, QPushButton, QSpacerItem, QVBoxLayout, QWidget, QGridLayout, QLabel, QLineEdit, QTextEdit

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

        grid.addWidget(QLineEdit(), 0, 1)
        grid.addWidget(QLineEdit(), 1, 1)
        grid.addWidget(QLineEdit(), 3, 1)

        hbox.addWidget(QPushButton('Connect'))
        hbox.addWidget(QPushButton('Cancel'))

        self.setWindowTitle('Connect to a server')
        #self.setGeometry() 
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Client()
    sys.exit(app.exec_())