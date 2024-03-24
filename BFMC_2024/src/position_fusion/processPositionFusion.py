if __name__ == "__main__":
    import sys

    sys.path.insert(0, "../../..")
import logging
from multiprocessing import Pipe

import serial

from src.hardware.serialhandler.threads.filehandler import FileHandler
from src.position_fusion.threads.threadLocalisation import threadLocalisation
from src.position_fusion.threads.threadUKF import threadUKF
from src.templates.workerprocess import WorkerProcess
from src.utils.CarControl.CarControl import CarControl


class processPositionFusion(WorkerProcess):
    """This process handle position fusion.\n
    Args:
        queueList (dictionar of multiprocessing.queues.Queue): Dictionar of queues where the ID is the type of messages.
        logging (logging object): Made for debugging.
        debugging (bool, optional): A flag for debugging. Defaults to False.
        example (bool, optional): A flag for running the example. Defaults to False.
    """

    # ===================================== INIT =========================================
    def __init__(self, queueList, Speed, Steer, logging, debugging=False):
        self.CarControl = CarControl(queueList, Speed, Steer)
        self.queuesList = queueList
        self.debugging = debugging
        # logging.basicConfig(
        #     level=logging.DEBUG,
        #     filename="app.log",
        #     filemode="w",
        #     format="%(name)s - %(levelname)s - %(message)s",
        # )
        self.logger = logging
        self.Speed = Speed
        self.Steer = Steer
        # self.logger.info("Started")
        super(processPositionFusion, self).__init__(self.queuesList)

    # ===================================== STOP ==========================================
    def stop(self):
        """Function for stopping threads and the process."""
        for thread in self.threads:
            thread.stop()
            thread.join()
        super(processPositionFusion, self).stop()

    # ===================================== RUN ==========================================
    def run(self):
        """Apply the initializing methods and start the threads."""
        super(processPositionFusion, self).run()

    # ===================================== INIT TH =================================
    def _init_threads(self):
        """Initializes the read and the write thread."""
        pipeRecvLocs, pipeSendLocs = Pipe(duplex=False)
        UKFthread = threadUKF(
            self.queuesList,
            pipeSendLocs,
            self.logger,
            self.Speed,
            self.Steer,
            self.debugging,
        )
        Localisationthread = threadLocalisation(
            self.queuesList,
            pipeRecvLocs,
            self.logger,
            self.Speed,
            self.Steer,
        )
        self.threads.append(UKFthread)
        self.threads.append(Localisationthread)


if __name__ == "__main__":
    pass
    # # Example of usage
