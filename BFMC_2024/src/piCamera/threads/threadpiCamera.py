import cv2
import threading
import socket
import base64
import time
import numpy as np
import os

from multiprocessing import Pipe
from src.templates.threadwithstop import ThreadWithStop
import struct
import pickle

from src.utils.messages.allMessages import (
    mainCamera,
    serialCamera,
    ObjectCamera,
    SegmentCamera,
    Recording,
    Record,
    Config,
)


class threadpiCamera(ThreadWithStop):

    # ================================ INIT ===============================================
    def __init__(self, serverip, port, queuesList, debugger):
        super(threadpiCamera, self).__init__()
        self.serverip = serverip
        self.port = port
        # Kết nối đến server
        self.server_address = (self.serverip, self.port)  # Địa chỉ và cổng của server
        self.client_socket = socket.socket()
        self.client_socket.connect(self.server_address)
        self.payload_size = struct.calcsize("Q")

        # Nhận dữ liệu từ server

        self.data = b""
        self.queuesList = queuesList
        self.debugger = debugger

    # =============================== STOP ================================================
    def stop(self):
        self.client_socket.close()
        # cv2.destroyAllWindows()
        super(threadpiCamera, self).stop()


    # ================================ RUN ================================================
    def run(self):
        """This function will run while the running flag is True. It captures the image from camera and make the required modifies and then it send the data to process gateway."""
        while self._running:
            start = time.time()
            chunk = self.client_socket.recv(4*1024)
            if not chunk:
                break
            self.data+=chunk
            packed_msg_size = self.data[:self.payload_size]
            self.data = self.data[self.payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]
            
            while len(self.data)<msg_size:
                self.data+=self.client_socket.recv(4*1024)
            image = self.data[:msg_size]
            self.data = self.data[msg_size:]
            
            image = pickle.loads(image)
            self.queuesList[mainCamera.Queue.value].put(
                {
                    "Owner": mainCamera.Owner.value,
                    "msgID": mainCamera.msgID.value,
                    "msgType": mainCamera.msgType.value,
                    "msgValue": image,
                }
            )
            self.queuesList[ObjectCamera.Queue.value].put(
                {
                    "Owner": ObjectCamera.Owner.value,
                    "msgID": ObjectCamera.msgID.value,
                    "msgType": ObjectCamera.msgType.value,
                    "msgValue": image,
                }
            )
            self.queuesList[SegmentCamera.Queue.value].put(
                {
                    "Owner": SegmentCamera.Owner.value,
                    "msgID": SegmentCamera.msgID.value,
                    "msgType": SegmentCamera.msgType.value,
                    "msgValue": image,
                }
            )
            
            print('Received: ', time.time() - start)

    # =============================== START ===============================================
    def start(self):
        time.sleep(25)
        super(threadpiCamera, self).start()

        
