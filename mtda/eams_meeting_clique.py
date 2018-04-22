import logging
from collections import namedtuple


class Meeting_Clique():
    def __init__(self):
       
        self.MTYPE = []
        self.mtdesc = namedtuple('Meeting_Type', 'MTW MA MCA MLS')
        #=======================================================================   
        # List of Meeting Clique     
        # Meeting_Type(MTW=(66, 81, 162, 177), MA=15, MCA=['6153', '2425', '895'], MLS=[1])
        # Meeting_Type(MTW=(66, 81, 162, 177), MA=15, MCA=['6153', '2425', '895', '1068'], MLS=[2])
        # Meeting_Type(MTW=(66, 81, 162, 177), MA=15, MCA=['6153', '1068'], MLS=[3])
        # Meeting_Type(MTW=(66, 81, 162, 177), MA=15, MCA=[], MLS=[4, 9])
        # Meeting_Type(MTW=(66, 81), MA=15, MCA=[], MLS=[6, 8])
        # Meeting_Type(MTW=(162, 177), MA=15, MCA=[], MLS=[0, 5, 7])
        #=======================================================================
        
        self.CALS = {}
        #=======================================================================
        # List of Conflicting Meetings follow the sequence of self.ML
        # eg. For ML[1] is conflict with ML[2] because of attendee['6153', '2425', '895']
        # 0 :  {}
        # 1 :  {2: ['6153', '2425', '895'], 3: ['6153']}
        # 2 :  {1: ['6153', '2425', '895'], 3: ['1068', '6153']}
        # 3 :  {1: ['6153'], 2: ['1068', '6153']}
        #=======================================================================

    def _getConflictAttendees(self, m):
        return self.CALS[m].values()
    
    def _populateMeetingConflicts(self):
        """Which meeting is conflict with m, and who are the attendee that cause the conflict"""
         
        self.CALS = {}
        for mx in xrange(len(self.CURR_M)):
            for my in xrange(mx+1, len(self.CURR_M)):  
                oa = set(self.CURR_M[mx].Attendees) & set(self.CURR_M[my].Attendees)
                if oa:
                    if mx in self.CALS:
                        self.CALS.get(mx).update({my:list(oa)})
                    else:
                        self.CALS[mx]={my:list(oa)}
                        
                    if my in self.CALS:
                        self.CALS.get(my).update({mx:list(oa)})
                    else:
                        self.CALS[my]={mx:list(oa)}

#                 for k, v in self.CALS.iteritems():
#                     print k, ": ", v
#                 print ""
                
        # Add empty set for meetings w/o conflicts!
        no_conflict = list(set(list(xrange(len(self.CURR_M)))).difference(set(self.CALS.keys())))
        for i in xrange(len(no_conflict)):
            self.CALS[no_conflict[i]] = {}
            
            
    def _group_based_on_attendee_conflict(self):
        logging.debug("Within group of same time window & same num attendee group, Re-group based on attendee conflict... ")
        
        self._populateMeetingConflicts()
        
        new_mtype = []     
        for i in xrange(len(self.MTYPE)):
            mls = self.MTYPE[i].MLS 
            logging.debug("Evaluating MTYPE %d: %s" %(i, mls))
            tmp_mtype = []   
            for x in xrange(len(mls)):
                m = mls[x]
                mca = self._getConflictAttendees(m)
                
                # Get a unique list of conflict attendee for all meetings in MLS. Eg {19585,83499,3} and {19585,83499} = {19585,83499}
                uniq_mca = []
                for a in xrange(len(mca)):
                    for b in xrange(len(mca[a])):
                        if mca[a][b] not in uniq_mca:
                            uniq_mca.append(mca[a][b])
                logging.debug(uniq_mca)
                
                # If stat==False, create a new mtype with the uniq_mca. Else append to existing tmp_mtype.
                stat = False
                for y in xrange(len(tmp_mtype)):
#                     print "tmp_mtype[y].MCA:", tmp_mtype[y].MCA
#                     print "uniq_mca:", uniq_mca
#                     print tmp_mtype[y].MCA == uniq_mca
                    if tmp_mtype[y].MCA == uniq_mca:
                        tmp_mtype[y].MLS.append(m)
                        stat = True
                        break
                if stat == False:   
                    tmp_mtype.append(self.mtdesc(self.MTYPE[i].MTW, self.MTYPE[i].MA, uniq_mca, [m]))
                
            for j in xrange(len(tmp_mtype)):
                new_mtype.append(tmp_mtype[j]) 
        
        
        logging.info("Number of new MTYPE:%d" %len(new_mtype))
        for i in xrange(len(new_mtype)):
            logging.info("MTYPE[%d]:%s" %(i, str(new_mtype[i])))
                
        # Overwrite MTYPE
        self.MTYPE = new_mtype
                
                
                
        
    def _group_based_on_attendee_num(self):
        logging.debug("Group based on attendee number... ")
        logging.debug("For simplicity, meetings are grouped based on 2-5, 6-15, 16-30 ppl")
        
        tmp_mtype = []
        for i in xrange(len(self.MTYPE)):
            num_attendee_dict = {5:[],15:[],30:[], 100:[]}  # a dict of based on number of attendee (num attendee less than 'key')       
            for j in xrange(len(self.MTYPE[i].MLS)):
                mid = self.MTYPE[i].MLS[j]
                num_attendee = len(self.CURR_M[mid].Attendees)
                
                if num_attendee <= 5:
                    num_attendee_dict.get(5).append(mid)
                elif num_attendee <= 15:
                    num_attendee_dict.get(15).append(mid)
                elif num_attendee <= 30:
                    num_attendee_dict.get(30).append(mid)
                else:
                    num_attendee_dict.get(100).append(mid)
                    
            for k, v in num_attendee_dict.iteritems():
                if len(v):
                    tmp_mtype.append(self.mtdesc(self.MTYPE[i].MTW, k, None, v))
                    
#         logging.debug("%s" %tmp_mtype)
        self.MTYPE = tmp_mtype
    
       
    def _group_based_on_time_window(self):
        logging.debug("Group based on time window... ")
        
        tmp_mtype = []
        timewindow_dict = {}
        for i in xrange(len(self.CURR_M)):
            # create tuple for timewindow offset [[66, 81], [114, 129]] --> (66, 81, 114, 129)
            key = ()                                                    
            for j in xrange(len(self.CURR_M[i].TimeWindowsOffset)):
                key += tuple(self.CURR_M[i].TimeWindowsOffset[j])
            
            # IMPORTANT:  i  refers to offset of meetings as CURR_M, not ML_FULL
            if key in timewindow_dict:
                timewindow_dict[key].append(i)
#                 timewindow_dict[key].append(self.CURR_M[i].Key)
            else:
                timewindow_dict[key] = [i]
#                 timewindow_dict[key] = [self.CURR_M[i].Key]
        
        for k, v in timewindow_dict.iteritems():
            tmp_mtype.append(self.mtdesc(k, None, None, v))
        
#         logging.debug("%s" %tmp_mtype)
        self.MTYPE = tmp_mtype
        
        
    #==================================================================
    #     API
    #==================================================================  
                
    # TODO: For simplicity, we do not classify meeting further based on duration and room.
    def get_meeting_clique(self, m):
        
        self.MTYPE = []         # reinitialize MTYPE everytime
        self.CURR_M = m         # current group of meetings
        
        # Group based on time window
        self._group_based_on_time_window()
        
        # Re-group based on number of attendee
        self._group_based_on_attendee_num()
        
        # Re-group based on attendee conflict
        self._group_based_on_attendee_conflict()
        
        # Re-group based on preferred meeting room
    
        return self.MTYPE
    

    #==================================================================
    def get_meeting_type_nogrouping(self, m):
        
        self.MTYPE = []         # reinitialize MTYPE everytime
        self.CURR_M = m
        
        for i in xrange(len(self.CURR_M)):
            tw = ()
            for j in xrange(len(self.CURR_M[i].TimeWindowsOffset)):
                tw += tuple(self.CURR_M[i].TimeWindowsOffset[j])
            
            if len(self.CURR_M[i].Attendees) <= 5:
                num_attendee = 5
            elif len(self.CURR_M[i].Attendees) <= 15:
                num_attendee = 15
            elif len(self.CURR_M[i].Attendees) <= 30:
                num_attendee = 30
            else:
                num_attendee = 100
            
            self._populateMeetingConflicts()
            mca = self._getConflictAttendees(i)
            uniq_mca = []
            for ca in mca:
                for cid in ca:                
                    uniq_mca.append(cid)
                        
            self.MTYPE.append(self.mtdesc(tw, num_attendee, uniq_mca, [i]))
        
        
        logging.info("Number of new MTYPE:%d" %len(self.MTYPE))
        for i in xrange(len(self.MTYPE)):
            logging.info("MTYPE[%d]:%s" %(i, str(self.MTYPE[i])))
            
        return self.MTYPE
            