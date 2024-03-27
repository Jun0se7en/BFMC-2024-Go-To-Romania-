import cv2
import threading
import base64
import time
import numpy as np
import os
import matplotlib.pyplot as plt
from collections import Counter
from multiprocessing import Pipe
from src.utils.messages.allMessages import (
    MiddlePoint,
    Points,
    Intersection,
    Segmentation,
    LaneDetectionMsg,
    Record,
    Config,
)
from src.templates.threadwithstop import ThreadWithStop
from src.imageProcessing.laneDetection.utils import utils_action
from src.imageProcessing.laneDetection import ImagePreprocessing
from src.imageProcessing.laneDetection import IntersectionDetection
from src.imageProcessing.laneDetection import LaneDetection

# Use this thread for LaneLine Segmentation
class threadSegmentation(ThreadWithStop):
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
        super(threadSegmentation, self).__init__()
        self.queuesList = queuesList
        self.logger = logger
        self.pipeRecvConfig = pipeRecv
        self.pipeSendConfig = pipeSend
        pipeRecvRecord, pipeSendRecord = Pipe(duplex=False)
        self.pipeRecvRecord = pipeRecvRecord
        self.pipeSendRecord = pipeSendRecord
        self.subscribe()
        self.Configs()
        self._init_segment()
        # print('Initialize camera thread!!!')

    def subscribe(self):
        """Subscribe function. In this function we make all the required subscribe to process gateway"""
        self.queuesList["Config"].put(
            {
                "Subscribe/Unsubscribe": "subscribe",
                "Owner": Record.Owner.value,
                "msgID": Record.msgID.value,
                "To": {"receiver": "threadSegmentation", "pipe": self.pipeSendRecord},
            }
        )
        self.queuesList["Config"].put(
            {
                "Subscribe/Unsubscribe": "subscribe",
                "Owner": Config.Owner.value,
                "msgID": Config.msgID.value,
                "To": {"receiver": "threadSegmentation", "pipe": self.pipeSendConfig},
            }
        )

    # =============================== STOP ================================================
    def stop(self):
        # cv2.destroyAllWindows()
        super(threadSegmentation, self).stop()

    # =============================== CONFIG ==============================================
    def Configs(self):
        """Callback function for receiving configs on the pipe."""
        while self.pipeRecvConfig.poll():
            message = self.pipeRecvConfig.recv()
            message = message["value"]
            print(message)
        threading.Timer(1, self.Configs).start()

    def display_points(self, points, image, color):     # For lane highlighting
        if color == 0:
            if points is not None:
                for point in points:
                    point_tp = tuple(point)
                    image = cv2.circle(image, point_tp, 1, (255, 0, 0), -1)    #blue
            return image
        if color == 1:
            if points is not None:
                for point in points:
                    point_tp = tuple(point)
                    image = cv2.circle(image, point_tp, 1, (0, 0, 255), -1)    #red
            return image
    # ================================ RUN ================================================
    def run(self):
        """This function will run while the running flag is True. It captures the image from camera and make the required modifies and then it send the data to process gateway."""
        var = True
        while self._running:
            if var:
                img = {"msgValue": 1}
                while type(img["msgValue"]) != type(":text"):
                    img = self.queuesList["SegmentCamera"].get()    # Get image from camera
                image_data = base64.b64decode(img["msgValue"])
                img = np.frombuffer(image_data, dtype=np.uint8)     
                image = cv2.imdecode(img, cv2.IMREAD_COLOR)
                check_thresh = self.opt['INTERSECT_DETECTION']
                crop_ratio = float(check_thresh['crop_ratio'])
                height = self.opt["IMAGE_SHAPE"]["height"]

                crop_height_value =  int(height * crop_ratio)
                im_cut = image[crop_height_value:, :]   # crop half of image for intersection det
                # Intersection detection
                hlane_det = self.ImageProcessor.process_image2(im_cut)
                check_intersection = self.IntersectFinder.detect(hlane_det)
                

                # Lane detection
                new_im = np.copy(image)
                lane_det, grayIm = self.ImageProcessor.process_image(image)
                left_points, right_points, _, _ = self.LaneLine.find_left_right_lane(lane_det)  # Find left, right laneline

                self.queuesList[Points.Queue.value].put(
                {
                    "Owner": Points.Owner.value,
                    "msgID": Points.msgID.value,
                    "msgType": Points.msgType.value,
                    "msgValue": {'Left': left_points, 'Right': right_points, 'Image': image},
                })
                
                max_lines = check_intersection[1]['max_points']
                new_im = self.display_points((left_points), image, 0)
                new_im = self.display_points((right_points), image, 1)
                for i in max_lines:
                    cv2.circle(new_im, (i[0], i[1] + crop_height_value), 1, (0, 255, 0), -1)
                    
                # Send image to queue
                _, encoded_img = cv2.imencode(".jpg", new_im)
                image_data_encoded = base64.b64encode(encoded_img).decode("utf-8")

                self.queuesList[Intersection.Queue.value].put(
                {
                    "Owner": Intersection.Owner.value,
                    "msgID": Intersection.msgID.value,
                    "msgType": Intersection.msgType.value,
                    "msgValue": check_intersection[0],
                })
                # Send image segmentation
                self.queuesList[Segmentation.Queue.value].put(
                    {
                        "Owner": Segmentation.Owner.value,
                        "msgID": Segmentation.msgID.value,
                        "msgType": Segmentation.msgType.value,
                        "msgValue": image_data_encoded,
                    }
                )
            var = not var

    # =============================== START ===============================================
    def start(self):
        super(threadSegmentation, self).start()

    def _init_segment(self):
        self.opt = utils_action.load_config_file("main_rc.json")
        self.ImageProcessor = ImagePreprocessing.ImagePreprocessing(self.opt)
        self.IntersectFinder = IntersectionDetection.IntersectionDetection(self.opt, debug=True)
        self.LaneLine = LaneDetection.LaneDetection(self.opt)