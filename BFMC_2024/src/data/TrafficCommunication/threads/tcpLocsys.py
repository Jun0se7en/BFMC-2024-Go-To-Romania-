import json
import time

from twisted.internet import protocol

from src.utils.messages.allMessages import Location


# The server itself. Creates a new Protocol for each new connection and has the info for all of them.
class tcpLocsys(protocol.ClientFactory):
    """This handle the data received(position)

    Args:
        sendQueue (multiprocessing.Queue): We place the information on this queue.
    """

    def __init__(self, id, sendQueue):
        self.connection = None
        self.retry_delay = 1
        self.sendQueue = sendQueue
        self.deviceID = id

    def clientConnectionLost(self, connector, reason):
        print(
            "Connection lost with server ",
            self.connectiondata,
            " Retrying in ",
            self.retry_delay,
            " seconds... (Check password match, IP or server availability)",
        )
        self.connectiondata = None
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print(
            "Connection failed. Retrying in",
            self.retry_delay,
            "seconds... Possible server down or incorrect IP:port match",
        )
        print(reason)
        time.sleep(self.retry_delay)
        connector.connect()

    def buildProtocol(self, addr):
        conn = SingleConnection()
        conn.factory = self
        return conn

    def stopListening(self):
        super().stopListening()

    def receive_data_from_server(self, message):
        message["id"] = 3
        message_to_send = {
            "Owner": Location.Owner.value,
            "msgID": Location.msgID.value,
            "msgType": Location.msgType.value,
            "msgValue": message,
        }
        self.sendQueue.put(message_to_send)


# One class is generated for each new connection
class SingleConnection(protocol.Protocol):
    def connectionMade(self):
        peer = self.transport.getPeer()
        self.factory.connectiondata = peer.host + ":" + str(peer.port)
        self.factory.connection = self
        print("Connection with locsys established : ", self.factory.connectiondata)

    def dataReceived(self, data):
        try:
            dat = data.decode()
            da = json.loads(dat)
            self.factory.receive_data_from_server(da)
        except json.JSONDecodeError as e:
            # print(da)
            print(f"Error parsing JSON: {e}")
        
