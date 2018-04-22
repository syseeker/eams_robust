import math
import logging
from datetime import datetime
from operator import itemgetter
from collections import namedtuple
from configobj import ConfigObj, ConfigObjError
from random import shuffle
from eams_error import EAMS_Error

class Meeting:        
    # Meeting class consists of {Key, TimeWindows, Duration, Room, Attendees}
    def __init__(self):        
        self.mlist = []
        self.meetings = {}
        self.mdesc = namedtuple('Meeting_Desc', 'ID Key MType TimeWindows TimeWindowsOffset Duration Room Attendees CreateTime')
        
    def loadMeetings(self, mfile):
        """Load meeting requests from MEETINGS_CONFIG"""
        self.MEETINGS_CONFIG = mfile
        logging.info("Loading meeting requests from %s" %self.MEETINGS_CONFIG)
        
        try:
            meetings = ConfigObj(self.MEETINGS_CONFIG,  file_error=True)
              
            #TODO: any validation required? Eg. Faulty datetime (end time earlier than start time etc), non-exists room, same people at same meeting time etc...
            self.meetings = meetings    
        except (ConfigObjError, IOError), e:        
            logging.error('%s' % (e))
            return EAMS_Error().eams_config_meeting_err()
        
        return 0
        
    def _validateOverlappedTimeWindows(self, twlist, s, e):
        for i in xrange(len(twlist)):
            if twlist[i][0] == s and twlist[i][1] == e:
                return EAMS_Error().eams_meeting_overlapped_time_windows()
        return 0
    
    def _roundUpNearestInterval(self, val):
        return int(math.ceil(float(val) / self.UPDATE_INTERVAL)) * self.UPDATE_INTERVAL
    
    def populateMeetingsForRoomAllocNSchedule(self, TSC):
        """Populate meetings from configuration files"""
        num_m = 0
        for k, v in self.meetings.iteritems():
            tw = []
            for sk, sv in v.iteritems():                
                if sk.startswith("W"):
                    st = datetime.strptime(sv.get('Start'), "%Y-%m-%d %H:%M")
                    et = datetime.strptime(sv.get('End'), "%Y-%m-%d %H:%M")
                    if et < st:
                        logging.critical("Meeting[%s] Invalid time windows [%s]. End Time earlier than Start Time." %(k,sk))
                        return EAMS_Error().eams_meeting_invalid_time_windows()
                    elif self._validateOverlappedTimeWindows(tw, st, et) < 0:
                        logging.critical("Meeting[%s] Invalid time windows [%s]. Duplicate time windows." %(k,sk))
                        return EAMS_Error().eams_meeting_overlapped_time_windows()
                    else:
                        tw.append([st,et])      
            
            stw = sorted(tw, key=itemgetter(0))
            tw_offset = []
            for i in xrange(len(stw)):
                sidx = TSC.getTimeSlotIdxByDatetime(stw[i][0])
                eidx = TSC.getTimeSlotIdxByDatetime(stw[i][1])-1
                tw_offset.append([sidx, eidx])
                logging.debug("Meeting %s start at %s[slot %d], deadline at %s[slot %d], duration of %s slot(s)" %(k, stw[i][0], sidx, stw[i][1], eidx, int(v['Duration'])))
                
                
            if 'Preferred_Room' in v:
                self.mlist.append(self.mdesc(num_m, k, None, stw, tw_offset, int(v['Duration']), v['Preferred_Room'], v['Attendees'], datetime.strptime(v['CreateTime'], "%Y-%m-%d %H:%M")))                
            else:
                self.mlist.append(self.mdesc(num_m, k, None, stw, tw_offset, int(v['Duration']), "", v['Attendees'], datetime.strptime(v['CreateTime'], "%Y-%m-%d %H:%M")))
            num_m += 1
            
        logging.debug(self.mlist)   
        return 0
    
    def getMeetingsList(self):
        # Randomize meeting input sequence (instead of following meeting start time)
#         self.shuffleMeetingList()
        return self.mlist

    def shuffleMeetingList(self):
        logging.info("MeetingList Before Shuffle: %s" %(self.mlist))        
        shuffle(self.mlist)
        logging.info("MeetingList After Shuffle: %s" %(self.mlist))
        
        
            
