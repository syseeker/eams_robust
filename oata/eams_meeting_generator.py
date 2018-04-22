import math
import logging
from datetime import timedelta
from collections import namedtuple

from eams_meeting_clique import Meeting_Clique
# read USC data jan12
# [Optional] create time window [do later with jan12, create timewindow with different flex]
# init num_room
# select random number of room
# 


class Meeting_Generator:
    def __init__(self, meetings, update_interval):
        self.MTYPE = []
        self.ML_GROUP = {}   # group _BY_CREATE_TIME       
        self.ML_CLIQUE = Meeting_Clique()
        
        self.CMT = {}
        #=======================================================================   
        # List of Conflicting Meeting Type because of an attendee
        # Key: Attendee ID, Value: Follow offset of Meeting Type in self.MTYPE
        # {'1068': [1, 2], '6153': [0, 1, 2], '2425': [0, 1], '895': [0, 1]}
        #=======================================================================
        
        self.ML_FULL = meetings
        self.UPDATE_INTERVAL = update_interval 
        
        self._create_meeting_clique()                               # Assume all meetings are known up-front, and therefore meeting types are pre-clustered
        self._group_meetings_based_on_creation_time()               # Also to speed up search, meetings are first group based on their creation time
        self._populate_conflict_meeting_types_basedon_attendee()    # Meeting conflicts are determined up-front too.
        
#==================================================================
#     Meeting clique
#==================================================================        
    def _create_meeting_clique(self):
        logging.info("Creating meeting clique")
        # Option 1: Group meeting into cliques of MTYPE
#         self.MTYPE = self.ML_CLIQUE.get_meeting_clique(self.ML_FULL)
        # Option 2: No notion of meeting cliques, just create each meeting as one MTYPE
        self.MTYPE = self.ML_CLIQUE.get_meeting_type_nogrouping(self.ML_FULL)
        
        self._update_meeting_mtype()
        
    def _update_meeting_mtype(self):
        logging.info("Updating meeting mtype")
        for i in xrange(len(self.MTYPE)):
            mls = self.MTYPE[i].MLS
            for j in xrange(len(mls)):
                mid = mls[j]
                self.ML_FULL[mid] = self.ML_FULL[mid]._replace(MType=i)
                
        for i in xrange(len(self.ML_FULL)):
            logging.info(self.ML_FULL[i])   
            
    def _populate_conflict_meeting_types_basedon_attendee(self):
        self.CMT = {}        
        for i in xrange(len(self.MTYPE)): 
            for j in xrange(len(self.MTYPE[i].MCA)):
                aid = self.MTYPE[i].MCA[j]
                if aid not in self.CMT.keys():
                    self.CMT[aid] = [i]
                else:
                    self.CMT.get(aid).append(i)
                    
        logging.debug("ConflictMeetingTypes: %s" %self.CMT)
            
#==================================================================
#     Group meetings
#==================================================================        
    def _roundUpNearestInterval(self, val, interval):
        return int(math.ceil(float(val) / interval)) * interval
    
    def _group_meetings_based_on_creation_time(self):
        """Group meetings based on creation time """ 
        for i in xrange(len(self.ML_FULL)):
            delta = self._roundUpNearestInterval(self.ML_FULL[i].CreateTime.minute, self.UPDATE_INTERVAL) - self.ML_FULL[i].CreateTime.minute
            grp_key = self.ML_FULL[i].CreateTime + timedelta(minutes=delta)
#             print self.ML_FULL[i].CreateTime, " ", grp_key  , " ", self.ML_FULL[i].CreateTime.minute, " ", self._roundUpNearestInterval(self.ML_FULL[i].CreateTime.minute)
            if self.ML_GROUP.get(grp_key) is not None:
                self.ML_GROUP[grp_key].append(self.ML_FULL[i])
            else:
                self.ML_GROUP[grp_key] = [self.ML_FULL[i]]
                
        for k,v in self.ML_GROUP.iteritems():
            logging.info("Meeting Group based on Create Time %s : %s : %s" %(k,len(v), v))
           
#==================================================================
#     API
#==================================================================
    def get_meetings(self, sche_time):
        M = self.ML_GROUP.get(sche_time)
        if M is not None:
            return M
        return None
        
            
            
            
        