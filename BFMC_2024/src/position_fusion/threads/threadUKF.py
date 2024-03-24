import logging
import math
import time
from multiprocessing import Pipe

import numpy as np

from src.position_fusion.UKF import UKF_IMU
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


class threadUKF(ThreadWithStop):
    """Thread which will handle position fusion.
    Args:
        pipeRecv (multiprocessing.queues.Pipe): A pipe where we can receive configs for camera. We will read from this pipe.
        pipeSend (multiprocessing.queues.Pipe): A pipe where we can write configs for camera. Process Gateway will write on this pipe.
        queuesList (dictionar of multiprocessing.queues.Queue): Dictionar of queues where the ID is the type of messages.
        logger (logging object): Made for debugging.
        debugger (bool): A flag for debugging.
    """

    def __init__(self, queueList, pipeLoc, logger, Speed, Steer, debugger=False):
        self.logger = logger
        self.debugger = debugger
        super(threadUKF, self).__init__()
        self.queueList = queueList
        self.message = {}
        self.message_type = "enginerun"
        self.pipeLoc = pipeLoc
        pipeRecvSteer, pipeSendSteer = Pipe(duplex=False)
        self.pipeRecvSteer = pipeRecvSteer
        self.pipeSendSteer = pipeSendSteer
        pipeRecvSpeed, pipeSendSpeed = Pipe(duplex=False)
        self.pipeRecvSpeed = pipeRecvSpeed
        self.pipeSendSpeed = pipeSendSpeed
        pipeRecvLocs, pipeSendLocs = Pipe(duplex=False)
        self.pipeRecvLocs = pipeRecvLocs
        self.pipeSendLocs = pipeSendLocs
        pipeRecvIMU, pipeSendIMU = Pipe(duplex=False)
        self.pipeRecvIMU = pipeRecvIMU
        self.pipeSendIMU = pipeSendIMU
        self.Speed = Speed
        self.Steer = Steer
        self.CarControl = CarControl(queueList, self.Speed, self.Steer)
        self.prevtime = time.time()
        self._running = True
        self.dt = 0.2
        self.u = {"steer": 0, "speed": 0}
        self.ukf = UKF_IMU(self.dt, 0.26, 0.1, 1, 2)
        self.ukf.x = np.array([8.72, 35, 0, np.pi / 2])
        var_x = 2
        var_y = 2
        var_v = 1
        var_yaw = 2
        cov_xy = 0
        cov_xv = 0
        cov_xyaw = 0
        cov_yyaw = 0
        cov_yv = 0
        cov_vyaw = 0
        self.ukf.P = np.array(
            [
                [var_x, cov_xy, cov_xv, cov_xyaw],
                [cov_xy, var_y, cov_yv, cov_yyaw],
                [cov_xv, cov_yv, var_v, cov_vyaw],
                [cov_xyaw, cov_yyaw, cov_vyaw, var_yaw],
            ]
        )
        self.ukf.Q = np.array(
            [
                [0.01, 0, 0, 0],
                [0, 0.01, 0, 0],
                [0, 0, 0.01, 0],
                [0, 0, 0, 0.007],
            ]
        )
        # self.ukf.P = np.diag([2, 2, 1, 2])
        # self.ukf.Q = np.diag([0.04,0.04,0.01,0.04])
        self.offset_heading_map = 0
        self.offset_heading = 90
        self.initBNO = False
        self.subcribe()
        # self.CarControl.enIMU(200)
        # simulation purpose

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

    def SendState(self):
        msg = {
            "x": self.ukf.x[0],
            "y": self.ukf.x[1],
        }
        self.QueueSending(msg)
        # print("send")
        # self.logger.info(
        #     "UKF:  x: %s, y: %s, v: %s, h: %s",
        #     self.ukf.x[0],
        #     self.ukf.x[1],
        #     self.ukf.x[2],
        #     self.ukf.x[3],
        # )
        # self.logger.info(self.ukf.P)

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

    def stop(self):
        super(threadUKF, self).stop()

    def run(self):
        while self._running:
            try:
                # update control input if available in the pipe
                # print(float(msg["value"]))
                self.u["steer"] = -math.radians(float(self.CarControl.getAngle()))
                # print(float(msg["value"]))
                self.u["speed"] = float(self.CarControl.getSpeed()) / 100
                # print(self.u["speed"], self.u["steer"])
                # predict
                self.dt = time.time() - self.prevtime
                if self.dt > 0.2:
                    self.prevtime = time.time()
                    # self.ukf.predict(self.dt, self.u)
                # update IMU if available in the pipe
                if self.pipeRecvIMU.poll():
                    msg = self.pipeRecvIMU.recv()
                    if self.initBNO == False:
                        self.offset_heading_map = float(msg["value"]["roll"])
                        self.initBNO = True
                    else:
                        imu_heading = (
                            float(msg["value"]["roll"])
                            - self.offset_heading_map
                            + self.offset_heading
                        )
                        # print(imu_heading)
                        if imu_heading > 180:
                            imu_heading = imu_heading % (180)
                            imu_heading = imu_heading * -1
                        else:
                            imu_heading = 180 - imu_heading
                        imu_heading = math.radians(imu_heading)
                        # print(imu_heading)
                        # self.ukf.update_IMU(np.array([imu_heading]))

                if self.pipeRecvLocs.poll():
                    msg = self.pipeRecvLocs.recv()
                    pos_x = float(msg["value"]["x"]) / 100
                    pos_y = float(msg["value"]["y"]) / 100
                    # print(pos_x, pos_y)
                    # if self.initUWB is False:
                    #     self.initUWB = True
                    #     self.ukf.x[0] = pos_x
                    #     self.ukf.x[1] = pos_y
                    # else:
                    # self.ukf.update_UWB(np.array([pos_x, pos_y]))
                    # self.SendState()
                    # self.ukf.update_UWB(np.array([pos_x, pos_y]))
                    self.pipeLoc.send([pos_x,pos_y,self.ukf.x[3]])
                    # self.pipeLoc.send([self.ukf.x[0], self.ukf.x[1], self.ukf.x[2]])
                    # self.SendState()
            except Exception as e:
                print(e)
                # time.sleep(0.1)

    def start(self):
        super(threadUKF, self).start()
