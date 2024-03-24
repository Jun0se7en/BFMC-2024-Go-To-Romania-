import time
from src.utils.CarControl.CarControl import CarControl
class SignTrafficHandler:
    def __init__(self, queueslist, Speed, Steer):
        self.intersection_check = False
        self.speed = 0
        self.angle = 0
        self.done_event = False
        self.queueslist = queueslist
        self.Speed = Speed
        self.Steer = Steer
        self.control = CarControl(self.queueslist, self.Speed, self.Steer)
    
    def Queue_Sending(self):
        self.control.setSpeed(self.speed)
        self.control.setAngle(self.angle)
    # classes = ['Car', 'CrossWalk', 'Greenlight', 'HighwayEnd', 'HighwayEntry', 'NoEntry', 'OneWay',
    # 'Parking', 'Pedestrian', 'PriorityRoad', 'Redlight', 'Roundabout', 'Stop', 'Yellowlight']   
    def check_area(self, obj_msg, area):
        if obj_msg == 'Stop' and area >= 1200:
            return True
        if obj_msg == 'PriorityRoad' and area >= 2000:
            return True
        # if obj_msg == 'Car' and area >= 12000:
        #     return True
        else: 
            return False
    def check_special_sign(self, obj_msg, area):
        # if obj_msg == 'Stop' and area >= 1500:
        #     return True
        # if obj_msg == 'PriorityRoad' and area >= 2000:
        #     return True
        if obj_msg == 'HighwayEntry' and area >= 1800:
            return True
        if obj_msg == 'HighwayEnd' and area >= 1800:
            return True
        if obj_msg == 'CrossWalk' and area >= 2000:
            return True
        if obj_msg == 'Pedestrian' and area >= 8000:
            return True
        if obj_msg == 'Greenlight' and area >= 2000:
            return True
        if obj_msg == 'Yellowlight' and area >= 2000:
            return True
        if obj_msg == 'Redlight' and area >= 6000:
            return True
        if obj_msg == 'Parking' and area >= 4000:
            return True
        if obj_msg == 'NoEntry' and area >= 700:
            return True
        if obj_msg == 'Roundabout' and area >= 2000:
            return True
        if obj_msg == 'Car' and area >= 13000:
            return True
        else:
            return False 
    def swap_case(self, obj_msg):
        if obj_msg == 'Stop':
            self.stop_sign()
        if obj_msg == 'PriorityRoad':
            self.priority_sign()
        if obj_msg == 'NoEntry':
            self.no_entry_sign()
        # if obj_msg == 'OneWay':
        #     self.one_way_sign()
        if obj_msg == 'Parking':
            self.parking()
        if obj_msg == 'Roundabout':
            self.roundabout()
        if obj_msg == 'Car':
            self.car()
            
    def stop_sign(self):
        # self.speed = 25
        # self.angle = 0
        # self.control.setControl(self.speed,self.angle,1)
        # time.sleep(0.2)
        
        self.speed = 0
        self.angle = 0
        self.control.setControl(self.speed,self.angle,1)
        time.sleep(4)
        
        self.speed = 25
        self.angle = -14
        self.control.setControl(self.speed,self.angle,1)
        time.sleep(4)
        
    def priority_sign(self):
        # self.speed = 25
        # self.angle = 0
        # self.control.setControl(self.speed,self.angle,1)
        # time.sleep(0.2)
        
        self.speed = 25
        self.angle = 15
        self.control.setControl(self.speed,self.angle,0.5)
        time.sleep(0.5)
        
        self.speed = 25
        self.angle = 20
        self.control.setControl(self.speed,self.angle,1)
        time.sleep(2)
        
    def car(self):
        self.speed = 25
        self.angle = -20
        self.control.setControl(self.speed,self.angle,1)
        time.sleep(2)
        
        self.speed = 25
        self.angle = 20
        self.control.setControl(self.speed,self.angle,1)
        time.sleep(3.5)
        
        self.speed = 25
        self.angle = -15
        self.control.setControl(self.speed,self.angle,1)
        time.sleep(1)
        
    def roundabout(self):
        self.speed = 25
        self.angle = 0
        self.control.setControl(self.speed,self.angle,1)
        time.sleep(1)
        
        self.speed = 25
        self.angle = 20
        self.control.setControl(self.speed,self.angle,0.7) 
        time.sleep(1)
        
        self.speed = 25
        self.angle = 0
        self.control.setControl(self.speed,self.angle,0.7)
        time.sleep(0.7)
        
        self.speed = 25
        self.angle = 20
        self.control.setControl(self.speed,self.angle,1) ############# 2.2
        time.sleep(2.5)
        
        # self.speed = 25
        # self.angle = 0
        # self.control.setControl(self.speed,self.angle,0.5)
        # time.sleep(0.5)
        
        self.speed = 25
        self.angle = -20
        self.control.setControl(self.speed,self.angle,1)
        time.sleep(9)
    
    def stop_special(self):  
        self.speed = 0
        self.angle = 0
        self.control.setControl(self.speed,self.angle,1)
        time.sleep(4)
        
        self.speed = 25
        self.angle = 20
        self.control.setControl(self.speed,self.angle,1)
        time.sleep(2.5)
        

        
        
    def no_entry_sign(self):
        # self.speed = 0
        # self.angle = 0
        # self.control.setControl(self.speed, self.angle, 1)
        # time.sleep(0.5)
        
        self.speed = 25
        self.angle = -20
        self.control.setControl(self.speed,self.angle,1)
        time.sleep(4)
        
        # self.speed = 25
        # self.angle = -10
        # self.control.setControl(self.speed,self.angle,1)
        # time.sleep(1)
        
        # self.speed = 25
        # self.angle = 10
        # self.control.setControl(self.speed,self.angle,1)
        # time.sleep(1.2)

        
    def parking(self):
        print('parking')
        self.speed = 25
        self.angle = 0
        self.control.setControl(self.speed,self.angle,1)
        time.sleep(3)
        
        self.speed = 0
        self.angle = 0
        self.control.setControl(self.speed,self.angle,1)
        time.sleep(1)
        
        self.speed = -30
        self.angle = 20
        self.control.setControl(self.speed,self.angle,1)
        time.sleep(4)
        
        self.speed = -30
        self.angle = -20
        self.control.setControl(self.speed,self.angle,1)
        time.sleep(3)
        
        self.speed = 0
        self.angle = 0
        self.control.setControl(self.speed,self.angle,1)
        time.sleep(0.5)
        
        self.speed = 20
        self.angle = 15
        self.control.setControl(self.speed,self.angle,1)
        time.sleep(1)
        # Done parking
        self.speed = 0
        self.angle = 0
        self.control.setControl(self.speed,self.angle,1)
        time.sleep(10)
        
        # self.speed = -30
        # self.angle = 0
        # self.control.setControl(self.speed,self.angle,1)
        # time.sleep(2)
        
        # self.speed = 0
        # self.angle = 0
        # self.control.setControl(self.speed,self.angle,1)
        # time.sleep(1)
        
        # self.speed = 25
        # self.angle = 20
        # self.control.setControl(self.speed,self.angle,1)
        # time.sleep(2)
        
        # self.speed = 25
        # self.angle = 20
        # self.control.setControl(self.speed,self.angle,1)
        # time.sleep(1)
        
        # self.speed = 0
        # self.angle = 0
        # self.control.setControl(self.speed,self.angle,1)
        # time.sleep(10)