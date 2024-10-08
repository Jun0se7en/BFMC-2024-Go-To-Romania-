# Copyright (c) 2019, Bosch Engineering Center Cluj and BFMC organizers
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE
import cv2
import threading
import base64
import picamera2
import time

from multiprocessing import Pipe
from src.utils.messages.allMessages import (
    mainCamera,
    serialCamera,
    Recording,
    Record,
    Config,
)
from src.templates.threadwithstop import ThreadWithStop


class threadCamera(ThreadWithStop):
    """Thread which will handle camera functionalities.\n
    Args:
        pipeRecv (multiprocessing.queues.Pipe): A pipe where we can receive configs for camera. We will read from this pipe.
        pipeSend (multiprocessing.queues.Pipe): A pipe where we can write configs for camera. Process Gateway will write on this pipe.
        queuesList (dictionar of multiprocessing.queues.Queue): Dictionar of queues where the ID is the type of messages.
        logger (logging object): Made for debugging.
        debugger (bool): A flag for debugging.
    """

    # ================================ INIT ===============================================
    def __init__(self, pipeRecv, pipeSend, queuesList, logger, debugger):
        super(threadCamera, self).__init__()
        self.queuesList = queuesList
        self.logger = logger
        self.pipeRecvConfig = pipeRecv
        self.pipeSendConfig = pipeSend
        self.debugger = debugger
        self.frame_rate = 5
        self.width = 640.0
        self.height = 360.0
        self.recording = False
        pipeRecvRecord, pipeSendRecord = Pipe(duplex=False)
        self.pipeRecvRecord = pipeRecvRecord
        self.pipeSendRecord = pipeSendRecord
        self.video_writer = ""
        self.subscribe()
        # self._init_cv_camera()
        self._init_cv_camera()
        self.Queue_Sending()
        self.Configs()

    def subscribe(self):
        """Subscribe function. In this function we make all the required subscribe to process gateway"""
        self.queuesList["Config"].put(
            {
                "Subscribe/Unsubscribe": "subscribe",
                "Owner": Record.Owner.value,
                "msgID": Record.msgID.value,
                "To": {"receiver": "threadCamera", "pipe": self.pipeSendRecord},
            }
        )
        self.queuesList["Config"].put(
            {
                "Subscribe/Unsubscribe": "subscribe",
                "Owner": Config.Owner.value,
                "msgID": Config.msgID.value,
                "To": {"receiver": "threadCamera", "pipe": self.pipeSendConfig},
            }
        )

    def Queue_Sending(self):
        """Callback function for recording flag."""
        self.queuesList[Recording.Queue.value].put(
            {
                "Owner": Recording.Owner.value,
                "msgID": Recording.msgID.value,
                "msgType": Recording.msgType.value,
                "msgValue": self.recording,
            }
        )
        threading.Timer(1, self.Queue_Sending).start()

    # =============================== STOP ================================================
    def stop(self):
        if self.recording:
            self.video_writer.release()
        super(threadCamera, self).stop()

    # =============================== CONFIG ==============================================
    def Configs(self):
        """Callback function for receiving configs on the pipe."""
        while self.pipeRecvConfig.poll():
            message = self.pipeRecvConfig.recv()
            message = message["value"]
            print(message)
            self.camera.set_controls(
                {
                    "AeEnable": False,
                    "AwbEnable": False,
                    message["action"]: float(message["value"]),
                }
            )
        threading.Timer(1, self.Configs).start()

    # ================================ RUN ================================================
    def run(self):
        """This function will run while the running flag is True. It captures the image from camera and make the required modifies and then it send the data to process gateway."""
        while self._running:
            start = time.time()
            # Pi Camera
            # request2 = self.camera.capture_array("main")
            # # print(request2.shape)
            # request2 = cv2.resize(request2,(320,240))
            # _, encoded_img = cv2.imencode(".jpg", request2)
            # image_data_encoded = base64.b64encode(encoded_img).decode("utf-8")
            # self.queuesList[serialCamera.Queue.value].put(
            #     {
            #         "Owner": serialCamera.Owner.value,
            #         "msgID": serialCamera.msgID.value,
            #         "msgType": serialCamera.msgType.value,
            #         "msgValue": image_data_encoded,
            #     }
            # ) 

            # Cam CV
            ret, request = self.camera.read()
            if not ret:
                print("Read failed")
                self.stop()
            _, encoded_img = cv2.imencode(".jpg", request)
            image_data_encoded = base64.b64encode(encoded_img).decode("utf-8")
            self.queuesList[serialCamera.Queue.value].put(
                {
                    "Owner": serialCamera.Owner.value,
                    "msgID": serialCamera.msgID.value,
                    "msgType": serialCamera.msgType.value,
                    "msgValue": image_data_encoded,
                }
            ) 
            # print('Camera: ', time.time()-start)

    # =============================== START ===============================================
    def start(self):
        super(threadCamera, self).start()

    # ================================ INIT CAMERA ========================================
    def _init_camera(self):
        """This function will initialize the camera object. It will make this camera object have two chanels "lore" and "main"."""
        self.camera = picamera2.Picamera2()
        self.camera.video_configuration.controls.FrameRate = 60.0
        camera_config = self.camera.create_still_configuration(buffer_count=30, queue=False, main={"format": "XRGB8888", "size": (320,240)})
        self.camera.configure(camera_config)
        self.camera.start()
    
    def _init_cv_camera(self):
        self.camera = cv2.VideoCapture(0, cv2.CAP_GSTREAMER)
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 30)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        if not self.camera.isOpened():
            print("Capture failed")