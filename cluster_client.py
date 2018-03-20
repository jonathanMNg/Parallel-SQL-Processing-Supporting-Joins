import pickle
from cluster import Cluster
from socket import error as socket_error
class Cluster_Client(Cluster):
    def isClient(self):
        return True
    def isServer(self):
        return False
    def connect(self):
        try:
            self.mySocket.connect((self.host, self.port))
            return True
        except socket_error as e:
            return False
            print (e)
    def sendMessage(self, message):
        self.mySocket.send(message.encode())
    def recvMessage(self):
        return self.mySocket.recv(1024).decode()
    #send data under an object
    def sendData(self, dataObject):
        self.mySocket.send(pickle.dumps(dataObject))
    #receive data under an object
    def recvData(self):
        return pickle.loads(self.mySocket.recv(4096))
    def __del__(self):
        self.mySocket.close()
    def close(self):
        self.mySocket.close()
