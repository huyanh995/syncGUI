import socket

from numpy import record
import lxml.etree
from threading import Thread

class GP3(Thread):
    def __init__(self, config):
        super().__init__()
        self.gp3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.gp3.settimeout(2.0)
        self.connect = (config["host"], config["port"])

    def connect(self):
        try:
            self.gp3.connect(self.connect)
            return True
        except Exception as e:
            print(e)
            return False

    def start_stream(self):
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_DATA" STATE="1" />\r\n'))
        self.gp3.send(str.encode('<SET ID="ENABLE_SEND_TIME" STATE="1" />\r\n'))
        pass

    def run(self):
        # Receive data from socket
        global recording
        while recording:

            pass


