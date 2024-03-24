import logging
import math
import time
from multiprocessing import Pipe

import numpy as np
from pygraphml import GraphMLParser

from src.position_fusion.map_arr import map_arr
from src.position_fusion.path import path

from src.templates.threadwithstop import ThreadWithStop
from src.utils.CarControl.CarControl import CarControl
from src.utils.messages.allMessages import (
    Config,
    FusedPosition,
    ImuData,
    Location,
    SpeedMotor,
    SteerMotor,
)


class threadLocalisation(ThreadWithStop):
    """Thread which will handle position fusion.
    Args:
        pipeRecv (multiprocessing.queues.Pipe): A pipe where we can receive configs for camera. We will read from this pipe.
        pipeSend (multiprocessing.queues.Pipe): A pipe where we can write configs for camera. Process Gateway will write on this pipe.
        queuesList (dictionar of multiprocessing.queues.Queue): Dictionar of queues where the ID is the type of messages.
        logger (logging object): Made for debugging.
        debugger (bool): A flag for debugging.
    """

    def __init__(self, queueList, pipeRecvLocs, logger, Speed, Steer):
        self.logger = logger
        super(threadLocalisation, self).__init__()
        self.queueList = queueList
        self.message = {}
        self.message_type = "enginerun"
        pipeRecvSteer, pipeSendSteer = Pipe(duplex=False)
        self.pipeRecvSteer = pipeRecvSteer
        self.pipeSendSteer = pipeSendSteer
        pipeRecvSpeed, pipeSendSpeed = Pipe(duplex=False)
        self.pipeRecvSpeed = pipeRecvSpeed
        self.pipeSendSpeed = pipeSendSpeed
        self.Speed = Speed
        self.Steer = Steer
        self.CarControl = CarControl(queueList, self.Speed, self.Steer)
        self._running = True
        self.radius = 0.22
        self.isInitialized = False
        self.pipeRecvLocs = pipeRecvLocs
        self.path = path
        self.map_arr = map_arr
        self.steer_angle = 0
        self.current_node = self.path[0]
        self.next_node = self.path[1]
        self.current_node_i = 0
        # self.subcribe()

    def subcribe(self):
        self.queueList["Config"].put(
            {
                "Subscribe/Unsubscribe": "subscribe",
                "Owner": SteerMotor.Owner.value,
                "msgID": SteerMotor.msgID.value,
                "To": {"receiver": "threadUKF", "pipe": self.pipeSendSteer},
            }
        )
        self.queueList["Config"].put(
            {
                "Subscribe/Unsubscribe": "subscribe",
                "Owner": SpeedMotor.Owner.value,
                "msgID": SpeedMotor.msgID.value,
                "To": {"receiver": "threadUKF", "pipe": self.pipeSendSpeed},
            }
        )
        self.queueList["Config"].put(
            {
                "Subscribe/Unsubscribe": "subscribe",
                "Owner": Location.Owner.value,
                "msgID": Location.msgID.value,
                "To": {"receiver": "threadUKF", "pipe": self.pipeSendLocs},
            }
        )
        self.queueList["Config"].put(
            {
                "Subscribe/Unsubscribe": "subscribe",
                "Owner": ImuData.Owner.value,
                "msgID": ImuData.msgID.value,
                "To": {"receiver": "threadUKF", "pipe": self.pipeSendIMU},
            }
        )
        # threading.Timer(1, self.Queue_Sending).start()

    def QueueSending(self, msg):
        if self.message_type == "speed":
            self.queueList[SpeedMotor.Queue.value].put(
                {
                    "Owner": SpeedMotor.Queue.Owner.value,
                    "msgID": SpeedMotor.Queue.msgID.value,
                    "msgType": SpeedMotor.Queue.msgType.value,
                    "msgValue": self.message,
                }
            )
        elif self.message_type == "steer":
            self.queueList[SteerMotor.Queue.value].put(
                {
                    "Owner": SteerMotor.Queue.Owner.value,
                    "msgID": SteerMotor.Queue.msgID.value,
                    "msgType": SteerMotor.Queue.msgType.value,
                    "msgValue": self.message,
                }
            )
        elif self.message_type == "enginerun":
            self.queueList[SteerMotor.Queue.value].put(
                {
                    "Owner": SteerMotor.Queue.Owner.value,
                    "msgID": SteerMotor.Queue.msgID.value,
                    "msgType": SteerMotor.Queue.msgType.value,
                    "msgValue": self.message,
                }
            )

    def stop(self):
        super(threadLocalisation, self).stop()

    def find_current_node(self, posx, posy):
        # if not self.isInitialized:
        for i,node in enumerate(self.path):
            distance_to_node_sqr = (posx - node[0]) ** 2 + (posy - node[1]) ** 2
            if distance_to_node_sqr < self.radius**2:
                if((posx - self.path[i+1][0]) ** 2 + (posy - self.path[i+1][1]) ** 2)<distance_to_node_sqr:
                    return self.path[i+1]
                return self.path[i]
        return self.current_node
        # for node in self.path:
        #     distance_to_node_sqr = (posx - node[0]) ** 2 + (posy - node[1]) ** 2
        #     # print(node, distance_to_node_sqr)
        #     if distance_to_node_sqr < self.radius**2:
                
        #         return node
        # return self.current_node
        # self.isInitialized = True
        # else:
        #     print("A")
        # return node
        pass

    def find_next_node(self):
        if self.current_node is None:
            return self.path[0]
        else:
            i = self.current_node_i
            while i < len(self.path):
                if self.path[i] == self.current_node:
                    self.current_node_i = i
                    return self.path[i + 1]
                i += 1


    def find_steer_angle(self):
        # if abs(theta) < np.pi / 1.5:
        #     if self.next_node[0] < self.current_node[0]:
        #         steer_angle = 21
        #     elif self.next_node[0] > self.current_node[0]:
        #         steer_angle = -21
        #     else:
        #         steer_angle = 0
        # else:
        #     if self.next_node[1] < self.current_node[1]:
        #         steer_angle = 21
        #     elif self.next_node[1] > self.current_node[1]:
        #         steer_angle = -21
        #     else:
        #         steer_angle = 0
        # return steer_angle
        if(self.current_node[0]==7.12 and self.current_node[1] == 3.95):
            steer = 5
        elif(self.current_node[0]==7.12 and self.current_node[1] == 4.25):
            steer = 19
        elif(self.current_node[0]==7.3 and self.current_node[1] == 4.6):
            steer = 5
        elif(self.current_node[0]==7.57 and self.current_node[1] == 4.91):
            steer = -19
        elif(self.current_node[0]==6.2 and self.current_node[1] == 5.3):
            steer = 21
        else:
            steer = -19
        # print(self.current_node,steer)
        return steer

    def QueueSending(self, msg):
        try:
            self.queueList["Test"].put(
                {
                    "Owner": Location.Owner.value,
                    "msgID": Location.msgID.value,
                    "msgType": Location.msgType.value,
                    "msgValue": msg,
                }
            )
            # threading.Timer(1, self.Queue_Sending).start()
        except Exception as e:
            print("Error in QueueSending", e)

    def SendState(self, x, y,xn,yn):
        msg = {
            "x": x,
            "y": y,
            "xn": xn,
            "yn": yn,
        }
        self.QueueSending(msg)

    def run(self):
        while self._running:
            try:
                if self.pipeRecvLocs.poll():
                    message = self.pipeRecvLocs.recv()
                    self.current_node = self.find_current_node(
                        message[0] - 1.25, message[1]
                    )
                    steer= self.find_steer_angle()
                    # theta = message[2]
                    # next_node = self.find_next_node()
                    # self.CarControl.setAngle(steer)
                    # self.SendState(self.current_node[0], self.current_node[1],self.next_node[0],self.next_node[1])
                    self.SendState(message[0], message[1],self.current_node[0],self.current_node[1])

            except Exception as e:
                print(e)
            time.sleep(0.1)

    def start(self):
        super(threadLocalisation, self).start()
