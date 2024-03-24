import time
from multiprocessing import Pipe

from twisted.internet import reactor

from src.data.TrafficCommunication.threads.tcpClient import tcpClient
from src.data.TrafficCommunication.threads.tcpLocsys import tcpLocsys
from src.data.TrafficCommunication.threads.udpListener import udpListener
from src.data.TrafficCommunication.useful.periodicTask import periodicTask
from src.templates.threadwithstop import ThreadWithStop


class threadTrafficCommunication(ThreadWithStop):
    """Thread which will handle processTrafficCommunication functionalities

    Args:
        shrd_mem (sharedMem): A space in memory for mwhere we will get and update data.
        queuesList (dictionary of multiprocessing.queues.Queue): Dictionary of queues where the ID is the type of messages.
        deviceID (int): The id of the device.
        decrypt_key (String): A path to the decription key.
    """

    # ====================================== INIT ==========================================
    def __init__(self, shrd_mem, queueslist, deviceID, decrypt_key):
        super(threadTrafficCommunication, self).__init__()
        self.listenPort = 9000
        self.tcp_factory = tcpClient(
            self.serverDisconnect, self.locsysConnect, deviceID
        )
        self.udp_factory = udpListener(decrypt_key, self.serverFound)
        self.queue = queueslist["General"]
        self.queueslist = queueslist

        self.reactor = reactor
        self.reactor.listenUDP(self.listenPort, self.udp_factory)
        # self.task = PeriodicTask(
        #     self.factory, 0.001, self.pipeRecv
        # )  # Replace X with the desired number of seconds
        self.running = True
        self.period_task = periodicTask(
            0.1,
            shrd_mem,
            self.tcp_factory,
            self.queueslist
        )

    # =================================== CONNECTION =======================================
    def serverDisconnect(self):
        """If the server discconects we stop the factory listening and we start the reactor listening"""
        self.reactor.listenUDP(self.listenPort, self.udp_factory)
        self.tcp_factory.stopListening()

    def serverFound(self, address, port):
        """If the server was found we stop the factory listening and we connect the reactor and we start the periodic task"""
        self.reactor.connectTCP(address, port, self.tcp_factory)
        self.udp_factory.stopListening()
        self.period_task.start()

    def locsysConnect(self, deviceID, IPandPORT):
        """In this method we get the port and ip and we connect the reactor"""
        ip, port = IPandPORT.split(":")
        print("Locsys connect")
        self.tcp_factory_locsys = tcpLocsys(id, self.queue)
        self.reactor.connectTCP("192.168.7.141", 4691, self.tcp_factory_locsys)

    # ======================================= RUN ==========================================
    def run(self):
        self.reactor.run(installSignalHandlers=False)

    # ====================================== STOP ==========================================
    def stop(self):
        self.reactor.stop()
        super(threadTrafficCommunication, self).stop()
