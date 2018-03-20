import socket
class Cluster:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.mySocket = socket.socket()
    def close():
        self.mySocket.close()
    def getHost(self):
        return self.host
    def getPort(self):
        return self.port
    def setHost(self, host):
        self.host = host
    def setPort(self, port):
        self.port = port
    def __del__(self):
        self.mySocket.close()
