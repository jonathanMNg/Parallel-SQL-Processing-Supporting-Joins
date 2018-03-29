import pickle
from cluster import Cluster
from socket import error as socket_error
class Cluster_Server(Cluster):
    def isClient(self):
        return False
    def isServer(self):
        return True
    def connect(self):
        self.mySocket.bind((self.host, self.port))
    #send message under a string
    def sendMessage(self, message):
        return self.conn.sendall(message.encode())
    #receive message under a string
    def recvMessage(self):
        return self.conn.recv(1024).decode()
    #send data under an object
    def sendData(self, dataObject):
        return self.conn.sendall(pickle.dumps(dataObject))
    #receive data under an object
    def recvData(self):
        return pickle.loads(self.conn.recv(4096))
    def listen(self):
        self.mySocket.listen()
        self.conn, self.addr = self.mySocket.accept()
        return self.conn, self.addr
    def close(self):
        self.conn.close()
