import json
import time

from twisted.internet import protocol


# The server itself. Creates a new Protocol for each new connection and has the info for all of them.
class tcpClient(protocol.ClientFactory):
    def __init__(self, connectionBrokenCllbck, locsysConnectCllbck, locsysID):
        self.connectiondata = None
        self.connection = None
        self.retry_delay = 1
        self.connectionBrokenCllbck = connectionBrokenCllbck
        self.locsysConnectCllbck = locsysConnectCllbck
        self.locsysID = locsysID

    def clientConnectionLost(self, connector, reason):
        print(
            "Connection lost with server ",
            self.connectiondata,
            " Retrying in ",
            self.retry_delay,
            " seconds... (Check Keypair, IP or server availability)",
        )
        try:
            self.connectiondata = None
            self.connection = None
            self.connectionBrokenCllbck()
        except:
            pass

    def clientConnectionFailed(self, connector, reason):
        print(
            "Connection failed. Retrying in",
            self.retry_delay,
            "seconds... Possible server down or incorrect IP:port match",
        )
        time.sleep(self.retry_delay)
        connector.connect()

    def buildProtocol(self, addr):
        conn = SingleConnection()
        conn.factory = self
        return conn

    def isConnected(self):
        if self.connection == None:
            return False
        else:
            return True

    def send_data_to_server(self, message):
        msgtosend = json.dumps(message)
        self.connection.send_data(msgtosend)

    def receive_data_from_server(self, message):
        msgPrepToList = message.replace("}{", "}}{{")
        msglist = msgPrepToList.split("}{")
        for msg in msglist:
            msg = json.loads(msg)
            if msg["reqORinfo"] == "request":
                if msg["type"] == "locsysDevice":
                    if "error" in msg:
                        print(msg["error"], "on traffic communication")
                    else:
                        print(msg["DeviceID"], msg["response"])
                        self.locsysConnectCllbck(msg["DeviceID"], msg["response"])


# One class is generated for each new connection
class SingleConnection(protocol.Protocol):
    def connectionMade(self):
        peer = self.transport.getPeer()
        self.factory.connectiondata = peer.host + ":" + str(peer.port)
        self.factory.connection = self
        msg = {
            "reqORinfo": "request",
            "type": "locsysDevice",
            "DeviceID": self.factory.locsysID,
        }
        self.send_data(msg)
        print("Connection with server established : ", self.factory.connectiondata)

    def dataReceived(self, data):
        self.factory.receive_data_from_server(data.decode())
        print(
            "got message from trafficcommunication server: ",
            self.factory.connectiondata,
        )

    def send_data(self, message):
        msg = json.dumps(message)
        self.transport.write(msg.encode())
