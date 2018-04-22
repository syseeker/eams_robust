import logging
from datetime import datetime
from datetime import timedelta

#TODO: form working hour timeslot only

class TimeSlot:    
    def __init__(self, start, end, interval):   
        self.start = start  
        self.end = end
        self.interval = interval
        self.timeslots = {}
        self.hash_timeslots = {}
        self._createTimeSlot()
    
    def _createTimeSlot(self):
        logging.info("Populate timeslot between %s and %s for %s mins interval" %(self.start, self.end, self.interval))
        curr_time = self.start
        self.timeslots[0] = curr_time
        self.hash_timeslots[curr_time] = 0
        idx = 1         
        while curr_time < self.end:          
            curr_time = curr_time + timedelta(minutes=self.interval)
            self.timeslots[idx] = curr_time
            self.hash_timeslots[curr_time] = idx
            idx = idx+1
            
    def getTimeSlots(self):
        return self.timeslots
        
#     def getTimeSlotIdxByString(self, dts):        
#         for k, v in self.timeslots.iteritems():
#             if v == datetime.strptime(dts, "%Y-%m-%d %H:%M:%S"):
#                 return k 
#         return None
    
    def getTimeSlotIdxByDatetime(self, dt):
        return self.hash_timeslots[dt]      
#         for k, v in self.timeslots.iteritems():
#             if v == dt:
#                 return k 
#         return None
    
    
            
        