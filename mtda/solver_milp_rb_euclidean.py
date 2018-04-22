import logging
from solver_milp import Solver_MILP

from gurobipy import *

class Solver_MILP_Robust_EU(Solver_MILP):
    def __init__(self, MSTR_SCHE, EAMS, fn, curr_k, mtype, uniq_cmt, occ_k, case, lns_seed, timelimit, sche_mode, slack, delta):        
        logging.info("Loading Solver_OS_Greedy_RB_Euclidean")
        Solver_MILP.__init__(self, MSTR_SCHE, EAMS, fn, curr_k, mtype, uniq_cmt, occ_k, case, lns_seed, timelimit, sche_mode)
        
        self.FIXED_SLACK = slack
        self.DELTA_SQ = delta**2
        
        
    def _createAuxVarSchedule(self):
        logging.info("_createAuxVarSchedule()")        
        self._createCAV_RoomTemperature_MSlack_LB()
        self._createCAV_RoomTemperature_MSlack_UB()
        self._createCAV_RoomTemperature_MSlack_PrevSes()

        
    def _createAuxVarHVAC(self):
        logging.info("_createAuxVarHVAC()")        
        self._createCAV_RoomTemperature_Slack_LB()  
        self._createCAV_RoomTemperature_Slack_UB()
                
        
    def _createAuxCstrHVAC(self):
        logging.info("_createAuxCstrHVAC()")
        self._createCSTR_MeetingBasedRoomTemperature_Slack()
        self._createCSTR_RoomTemperature_MSlack_from_ScheX_LB()        
        self._createCSTR_RoomTemperature_MSlack_from_ScheX_UB()
        self._createCSTR_RoomTemperature_MSlack_to_Slack_LB()
        self._createCSTR_RoomTemperature_MSlack_to_Slack_UB()

        self._createCSTR_MeetingBasedRoomTemperature_Slack_PrevSes()
        self._createCSTR_RoomTemperature_MSlack_from_ScheX_PrevSes()
        
    def _updMSTR_AuxHVAC(self):
        logging.info("_updMSTR_AuxHVAC()")         
        self._updMSTR_T_SLACK()   
    
# #==================================================================
# #   HVAC
# #==================================================================

    def _createCAV_RoomTemperature_Slack_LB(self):
        """For each location at each timestep, create an auxiliary variable that provides slack to temperature lower bound"""
         
        self.CAV_T_SLACK_LB_LK = []        
        for l in xrange(self.NUM_ROOM):
            self.CAV_T_SLACK_LB_LK.append([])
            
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
                
            for k in xrange(self.NUM_SLOT):                
                name = ['CAV_T_SLACK_LB_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)    
                self.CAV_T_SLACK_LB_LK[l].append(self.model.addVar(lb=0, ub=1, vtype=GRB.CONTINUOUS, name=name))
                 
        self.model.update()
        logging.debug("CAV_T_SLACK_LB_LK:\n %s" %self.CAV_T_SLACK_LB_LK)
        
    def _createCAV_RoomTemperature_Slack_UB(self):
        """For each location at each timestep, create an auxiliary variable that provides slack to temperature upper bound"""
         
        self.CAV_T_SLACK_UB_LK = []        
        for l in xrange(self.NUM_ROOM):
            self.CAV_T_SLACK_UB_LK.append([])
            
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
            
            for k in xrange(self.NUM_SLOT):                
                name = ['CAV_T_SLACK_UB_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)    
                self.CAV_T_SLACK_UB_LK[l].append(self.model.addVar(lb=0, ub=1, vtype=GRB.CONTINUOUS, name=name))
                 
        self.model.update()
        logging.debug("CAV_T_SLACK_UB_LK:\n %s" %self.CAV_T_SLACK_UB_LK)

    
    def _createCAV_RoomTemperature_MSlack_LB(self):
        """For each location at each timestep, create an auxiliary variable that bound slack to meeting-based tolerance"""
         
        self.CAV_T_MSLACK_LB_MK = [] 
        self.CAV_T_MSLACK_MK_Dict = {}
        self.CAV_T_MSLACK_MK_ReverseDict = {}        
        
        for m in xrange(self.NUM_MEETING_TYPE):  
            self.CAV_T_MSLACK_LB_MK.append([])
                
            if self.SCHE_MODE == 1:
                mtype_id = self.CURR_DESTROY_MTYPE[m]
                offset = self.MTYPE_ID.index(mtype_id)
                mid = self.MTYPE[offset].MLS[0] 
#                 mdur = self.EAMS.ML[mid].Duration
            else:
                mtype_id = self.MTYPE_ID[m]
                mid = self.MTYPE[m].MLS[0]
#                 mdur = self.EAMS.ML[mid].Duration
                  
            mk = 0                                      
            for k in xrange(self.NUM_SLOT):
                if (self.EAMS.isInOngoingTimeWindows(mid, self.CURR_K+k) > 0 and
                    self._is_K_available(mtype_id, self.CURR_K+k) 
                    ):
                    logging.debug("M_K_%d_%d = in array offset(%d, %d)" %(mtype_id,self.CURR_K+k, m,mk))
                    
                    name = ['CAV_T_MSLACK_LB_MK', str(mtype_id), str(self.CURR_K+k)]                            
                    name = '_'.join(name)         
                    self.CAV_T_MSLACK_LB_MK[m].append(self.model.addVar(lb=0.0, ub=1.0, vtype=GRB.CONTINUOUS, name=name))
                    self.CAV_T_MSLACK_MK_Dict[tuple([mtype_id,self.CURR_K+k])] = [m,mk]   
                    self.CAV_T_MSLACK_MK_ReverseDict[tuple([m,mk])] = [mtype_id,self.CURR_K+k]              
                    mk = mk+1
                    
                
        self.model.update()                           
        logging.debug("CAV_T_MSLACK_LB_MK:\n %s" %self.CAV_T_MSLACK_LB_MK)
        logging.debug("CAV_T_MSLACK_MK_Dict:\n %s" %self.CAV_T_MSLACK_MK_Dict)
        logging.debug("CAV_T_MSLACK_MK_ReverseDict:\n %s" %self.CAV_T_MSLACK_MK_ReverseDict)
        
        
    def _createCAV_RoomTemperature_MSlack_UB(self):
        """For each location at each timestep, create an auxiliary variable that bound slack to meeting-based tolerance"""
         
        self.CAV_T_MSLACK_UB_MK = [] 
        
        for m in xrange(self.NUM_MEETING_TYPE):  
            self.CAV_T_MSLACK_UB_MK.append([])
                
            if self.SCHE_MODE == 1:
                mtype_id = self.CURR_DESTROY_MTYPE[m]
                offset = self.MTYPE_ID.index(mtype_id)
                mid = self.MTYPE[offset].MLS[0] 
#                 mdur = self.EAMS.ML[mid].Duration
            else:
                mtype_id = self.MTYPE_ID[m]
                mid = self.MTYPE[m].MLS[0]
#                 mdur = self.EAMS.ML[mid].Duration
                                
            mk = 0                                      
            for k in xrange(self.NUM_SLOT):
                if (self.EAMS.isInOngoingTimeWindows(mid, self.CURR_K+k) > 0 and
                    self._is_K_available(mtype_id, self.CURR_K+k)
                    ):
                    logging.debug("M_K_%d_%d = in array offset(%d, %d)" %(mtype_id,self.CURR_K+k, m,mk))
                    
                    name = ['CAV_T_MSLACK_UB_MK', str(mtype_id), str(self.CURR_K+k)]                            
                    name = '_'.join(name)         
                    self.CAV_T_MSLACK_UB_MK[m].append(self.model.addVar(lb=0.0, ub=1.0, vtype=GRB.CONTINUOUS, name=name))
                    mk = mk+1
                                    
        self.model.update()                           
        logging.debug("CAV_T_MSLACK_UB_MK:\n %s" %self.CAV_T_MSLACK_UB_MK)
         
         
    def _createCAV_RoomTemperature_MSlack_PrevSes(self):
        """For meetings that was scheduled in prev session, adjust the temperature tolerance with ongoing new incoming meetings"""
                 
        self.CAV_T_MSLACK_LB_PREVSES_MK = []
        self.CAV_T_MSLACK_UB_PREVSES_MK = []  
        self.CAV_T_MSLACK_PREVSES_MK_Dict = {}
        self.CAV_T_MSLACK_PREVSES_MK_ReverseDict = {} 
        
        self.TMP_DICT = {}
        
        for (dl, dk) in self.MSTR_SCHE.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse.keys():            
            if dk >= self.CURR_K and dk < self.CURR_K+self.NUM_SLOT:
                mtype_id = self.MSTR_SCHE.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse.get(tuple([dl,dk]))
                logging.info("location %s time %s has been occupied by m %s" %(dl, dk, mtype_id))
                
                if self.TMP_DICT.get(mtype_id) is None:
                    self.TMP_DICT[mtype_id] = [(dl, dk)]
                else:
                    self.TMP_DICT.get(mtype_id).append((dl, dk))
        logging.info("self.TMP_DICT: %s" %(self.TMP_DICT))
                    
        m = 0
        for mtype_id, v in self.TMP_DICT.iteritems():
            self.CAV_T_MSLACK_LB_PREVSES_MK.append([])
            self.CAV_T_MSLACK_UB_PREVSES_MK.append([])      
            slot = 0      
            for dl, dk in v:
                name = ['CAV_T_MSLACK_LB_MK', str(mtype_id), str(dk)]                            
                name = '_'.join(name)                  
                self.CAV_T_MSLACK_LB_PREVSES_MK[m].append(self.model.addVar(lb=0.0, ub=1.0, vtype=GRB.CONTINUOUS, name=name))
                 
                name = ['CAV_T_MSLACK_UB_MK', str(mtype_id), str(dk)]                            
                name = '_'.join(name)                  
                self.CAV_T_MSLACK_UB_PREVSES_MK[m].append(self.model.addVar(lb=0.0, ub=1.0, vtype=GRB.CONTINUOUS, name=name))
                 
                self.CAV_T_MSLACK_PREVSES_MK_Dict[tuple([mtype_id,dk])] = [m, slot]
                self.CAV_T_MSLACK_PREVSES_MK_ReverseDict[tuple([m, slot])] = [mtype_id,dk]
                slot += 1                   
            m += 1
            
        self.model.update()                           
        logging.debug("CAV_T_MSLACK_LB_PREVSES_MK:\n %s" %self.CAV_T_MSLACK_LB_PREVSES_MK)
        logging.debug("CAV_T_MSLACK_UB_PREVSES_MK:\n %s" %self.CAV_T_MSLACK_UB_PREVSES_MK)
        logging.debug("CAV_T_MSLACK_PREVSES_MK_Dict:\n %s" %self.CAV_T_MSLACK_PREVSES_MK_Dict)
        logging.debug("CAV_T_MSLACK_PREVSES_MK_ReverseDict:\n %s" %self.CAV_T_MSLACK_PREVSES_MK_ReverseDict)
        
#==================================================================
    def _createCSTR_RoomTemperature_MSlack_from_ScheX_LB(self):
        """Bound MSlack to zero if meeting has not started at M,L,K' """
        
        self.CSTR_MSlack_from_ScheX_LB = []
        
        for m in xrange(len(self.CAV_T_MSLACK_LB_MK)):
            self.CSTR_MSlack_from_ScheX_LB.append([])
            for k in xrange(len(self.CAV_T_MSLACK_LB_MK[m])):
                [dmtype_id, dk] = self.CAV_T_MSLACK_MK_ReverseDict.get(tuple([m,k]))
                
                if self.SCHE_MODE == 1:
                    offset = self.MTYPE_ID.index(dmtype_id)
                    mid = self.MTYPE[offset].MLS[0]
                else:
                    mid = self.MTYPE[m].MLS[0]
                    
                k_m = []
                k_m = self.EAMS.getFeasibleStartTime(mid, dk)
                if k_m:   
                    rcstr = 0
                    for fk in k_m:
                        for l in xrange(self.NUM_ROOM):
                            if self.SCHE_MODE == 1:
                                dl = self.CURR_DESTROY_LOCATION[l]
                            else:
                                dl = l                                
                            alloc = self.BDV_x_MLK_Dict.get(tuple([dmtype_id, dl, fk]))
                            if alloc:
                                [xm, xl, xk] = alloc
                                rcstr += self.BDV_x_MLK[xm][xl][xk]
                        
                lcstr = self.CAV_T_MSLACK_LB_MK[m][k]
                name = ['CSTR_MSlack_from_ScheX_LB', str(dmtype_id), str(dk)]
                name = '_'.join(name)
                self.CSTR_MSlack_from_ScheX_LB[m].append(self.model.addConstr(lcstr <= rcstr, name))
        
        self.model.update()                           
        logging.debug("CSTR_MSlack_from_ScheX_LB:\n %s" %self.CSTR_MSlack_from_ScheX_LB)
        
        
    def _createCSTR_RoomTemperature_MSlack_from_ScheX_UB(self):
        """Bound MSlack to zero if meeting has not started at M,L,K' """
        
        self.CSTR_MSlack_from_ScheX_UB = []
        
        for m in xrange(len(self.CAV_T_MSLACK_UB_MK)):
            self.CSTR_MSlack_from_ScheX_UB.append([])
            for k in xrange(len(self.CAV_T_MSLACK_UB_MK[m])):
                [dmtype_id, dk] = self.CAV_T_MSLACK_MK_ReverseDict.get(tuple([m,k]))
                
                if self.SCHE_MODE == 1:
                    offset = self.MTYPE_ID.index(dmtype_id)
                    mid = self.MTYPE[offset].MLS[0]
                else:
                    mid = self.MTYPE[m].MLS[0]
                    
                k_m = []
                k_m = self.EAMS.getFeasibleStartTime(mid, dk)
                if k_m:   
                    rcstr = 0
                    for fk in k_m:
                        for l in xrange(self.NUM_ROOM):
                            if self.SCHE_MODE == 1:
                                dl = self.CURR_DESTROY_LOCATION[l]
                            else:
                                dl = l 
                            alloc = self.BDV_x_MLK_Dict.get(tuple([dmtype_id, dl, fk]))
                            if alloc:
                                [xm, xl, xk] = alloc
                                rcstr += self.BDV_x_MLK[xm][xl][xk]
                            
                    lcstr = self.CAV_T_MSLACK_UB_MK[m][k]
                    name = ['CSTR_MSlack_from_ScheX_UB', str(dmtype_id), str(dk)]
                    name = '_'.join(name)
                    self.CSTR_MSlack_from_ScheX_UB[m].append(self.model.addConstr(lcstr <= rcstr, name))
        
        self.model.update()                           
        logging.debug("CSTR_MSlack_from_ScheX_UB:\n %s" %self.CSTR_MSlack_from_ScheX_UB)
        
        
    def _createCSTR_RoomTemperature_MSlack_to_Slack_LB(self):        
        self.CSTR_MSlack_to_Slack_LB = []    
        alloc = {}
        alloc_prev = {}
        for m in xrange(len(self.CAV_T_MSLACK_LB_MK)):
            for k in xrange(len(self.CAV_T_MSLACK_LB_MK[m])):
                [_, dk] = self.CAV_T_MSLACK_MK_ReverseDict.get(tuple([m,k]))
                if alloc.get(tuple([dk])) is None:
                    alloc[tuple([dk])] = [tuple([m,k])]
                else:
                    alloc.get(tuple([dk])).append(tuple([m,k]))
                        
        for m in xrange(len(self.CAV_T_MSLACK_LB_PREVSES_MK)):  
            for s in xrange(len(self.CAV_T_MSLACK_LB_PREVSES_MK[m])):       
                [_, dk] = self.CAV_T_MSLACK_PREVSES_MK_ReverseDict.get(tuple([m, s]))
                if alloc_prev.get(tuple([dk])) is None:
                    alloc_prev[tuple([dk])] = [tuple([m,s])]
                else:
                    alloc_prev.get(tuple([dk])).append(tuple([m,s]))
             
        for l in xrange(self.NUM_ROOM):
            self.CSTR_MSlack_to_Slack_LB.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
                
            for k in xrange(self.NUM_SLOT):
                dk = self.CURR_K+k
                rcstr = 0
                if (alloc.get(tuple([dk])) is not None and
                    self.is_not_alloc_prev_sess(dl, dk)):
                        for [sm, sk] in alloc.get(tuple([dk])):
                            rcstr += self.CAV_T_MSLACK_LB_MK[sm][sk]
                if alloc_prev.get(tuple([dk])) is not None:
                    for [sm, ss] in alloc_prev.get(tuple([dk])):
                        [mtype_id, _] = self.CAV_T_MSLACK_PREVSES_MK_ReverseDict.get(tuple([sm, ss]))
                        [sl, _] = self.MSTR_SCHE.MSTR_BDV_x_MLK_MeetingMap.get(mtype_id) 
                        if sl == dl:
                            rcstr += self.CAV_T_MSLACK_LB_PREVSES_MK[sm][ss]
                         
                lcstr = self.CAV_T_SLACK_LB_LK[l][k]
                name = ['CSTR_MSlack_to_Slack_LB', str(dl), str(dk)]
                name = '_'.join(name)
                self.CSTR_MSlack_to_Slack_LB[l].append(self.model.addConstr(lcstr == rcstr, name))   
                
        self.model.update()                           
        logging.debug("CSTR_MSlack_to_Slack_LB:\n %s" %self.CSTR_MSlack_to_Slack_LB)
        
        
    def _createCSTR_RoomTemperature_MSlack_to_Slack_UB(self):        
        self.CSTR_MSlack_to_Slack_UB = []    
        alloc = {}
        alloc_prev = {}
        for m in xrange(len(self.CAV_T_MSLACK_UB_MK)):
            for k in xrange(len(self.CAV_T_MSLACK_UB_MK[m])):
                [_, dk] = self.CAV_T_MSLACK_MK_ReverseDict.get(tuple([m,k]))
                if alloc.get(tuple([dk])) is None:
                    alloc[tuple([dk])] = [tuple([m,k])]
                else:
                    alloc.get(tuple([dk])).append(tuple([m,k]))
                        
        for m in xrange(len(self.CAV_T_MSLACK_UB_PREVSES_MK)):  
            for s in xrange(len(self.CAV_T_MSLACK_UB_PREVSES_MK[m])):       
                [_, dk] = self.CAV_T_MSLACK_PREVSES_MK_ReverseDict.get(tuple([m, s]))
                if alloc_prev.get(tuple([dk])) is None:
                    alloc_prev[tuple([dk])] = [tuple([m,s])]
                else:
                    alloc_prev.get(tuple([dk])).append(tuple([m,s]))
                        
        for l in xrange(self.NUM_ROOM):
            self.CSTR_MSlack_to_Slack_UB.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
                
            for k in xrange(self.NUM_SLOT):
                dk = self.CURR_K+k
                rcstr = 0
                if (alloc.get(tuple([dk])) is not None and
                    self.is_not_alloc_prev_sess(dl, dk)):
                        for [sm, sk] in alloc.get(tuple([dk])):
                            rcstr += self.CAV_T_MSLACK_LB_MK[sm][sk]
                if alloc_prev.get(tuple([dk])) is not None:
                    for [sm, ss] in alloc_prev.get(tuple([dk])):
                        [mtype_id, _] = self.CAV_T_MSLACK_PREVSES_MK_ReverseDict.get(tuple([sm, ss]))
                        [sl, _] = self.MSTR_SCHE.MSTR_BDV_x_MLK_MeetingMap.get(mtype_id)  
                        if sl == dl:
                            rcstr += self.CAV_T_MSLACK_LB_PREVSES_MK[sm][ss]
                                         
                lcstr = self.CAV_T_SLACK_UB_LK[l][k]
                name = ['CSTR_MSlack_to_Slack_UB', str(dl), str(dk)]
                name = '_'.join(name)
                self.CSTR_MSlack_to_Slack_UB[l].append(self.model.addConstr(lcstr == rcstr, name))   
                
        self.model.update()                           
        logging.debug("CSTR_MSlack_to_Slack_UB:\n %s" %self.CSTR_MSlack_to_Slack_UB)
        
    def is_not_alloc_prev_sess(self, l, k):
        m = self.MSTR_SCHE.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse.get(tuple([l, k]))
        if m is None or m in self.MTYPE_ID:
            return True
        else:
            return False

    def _createCSTR_MeetingBasedRoomTemperature_Slack(self):
        """Sum of all slack should be less than delta for each meeting"""
        self.CSTR_T_MSLACK_M = []
         
        for m in xrange(len(self.CAV_T_MSLACK_LB_MK)):
            if self.SCHE_MODE == 1:
                mtype_id = self.CURR_DESTROY_MTYPE[m]
            else:
                mtype_id = self.MTYPE_ID[m]
                
            name = ['CSTR_T_MSLACK_M', str(mtype_id)]
            name = '_'.join(name)
            
            lcstr = 0
            for k in xrange(len(self.CAV_T_MSLACK_LB_MK[m])):
                lcstr += (self.CAV_T_MSLACK_LB_MK[m][k] * self.CAV_T_MSLACK_LB_MK[m][k])
                lcstr += (self.CAV_T_MSLACK_UB_MK[m][k] * self.CAV_T_MSLACK_UB_MK[m][k])
                    
            self.CSTR_T_MSLACK_M.append(self.model.addConstr(lcstr <= self.DELTA_SQ, name))
         
        self.model.update()
        logging.debug("CSTR_T_MSLACK_M:\n %s" %self.CSTR_T_MSLACK_M)
        
        
    def _createCSTR_RoomTemperature_LB(self):
        logging.debug("_createCSTR_RoomTemperature_LB   solver_milp_rb_eu")
        for l in xrange(self.NUM_ROOM):
            self.CSTR_T_LK_lb.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
                
            for k in xrange(self.NUM_SLOT):                
                name = ['CSTR_T_LK_lb', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)                
                  
                lcstr = self.CAV_T_LK[l][k]
                rcstr = float(self.EAMS.TEMPERATURE_UNOCC_MIN) + (float(self.EAMS.TEMPERATURE_OCC_COMFORT_RANGE_INCR) * self.BAV_z_LK[l][k]) - self.FIXED_SLACK * self.CAV_T_SLACK_LB_LK[l][k]  
                self.CSTR_T_LK_lb[l].append(self.model.addConstr(lcstr >= rcstr, name))
              
        self.model.update()
        logging.debug("CSTR_T_LK_lb:\n %s" %self.CSTR_T_LK_lb)
        
    
    def _createCSTR_RoomTemperature_UB(self):
        logging.debug("_createCSTR_RoomTemperature_UB   solver_milp_rb_eu")
        for l in xrange(self.NUM_ROOM):
            self.CSTR_T_LK_ub.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
            for k in xrange(self.NUM_SLOT):                
                name = ['CSTR_T_LK_ub', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)                
                 
                lcstr = self.CAV_T_LK[l][k]
                rcstr = float(self.EAMS.TEMPERATURE_UNOCC_MAX) - (float(self.EAMS.TEMPERATURE_OCC_COMFORT_RANGE_DECR)*self.BAV_z_LK[l][k]) + self.FIXED_SLACK * self.CAV_T_SLACK_UB_LK[l][k]
                self.CSTR_T_LK_ub[l].append(self.model.addConstr(lcstr <= rcstr, name))
             
        self.model.update()
        logging.debug("CSTR_T_LK_ub:\n %s" %self.CSTR_T_LK_ub)


#----------------------------------------------------------------

    def _createCSTR_MeetingBasedRoomTemperature_Slack_PrevSes(self):
        """Sum of all slack should be less than delta for each meeting. For ongoing meeting, sum of all slack should be less than (DELTA_SQ - those that has been used)."""
        self.CSTR_T_MSLACK_PREVSES_M = []
        
        for m in xrange(len(self.CAV_T_MSLACK_LB_PREVSES_MK)):            
            [mtype_id,_] = self.CAV_T_MSLACK_PREVSES_MK_ReverseDict.get(tuple([m, 0]))
            
            # if meeting has started before self.CURR_K, and is still ongoing. 
            # Check T_SLACK used. Sum of new T_MSLACK should be DELTA_SQ - those that has been used.
            
            [sl, sk] = self.MSTR_SCHE.MSTR_BDV_x_MLK_MeetingMap.get(mtype_id)
            if sk < self.CURR_K:
                logging.info("Meeting %s has started at slot %s and still ongoing.." %(m, sk))
                used_slack = 0
                for k in xrange(sk, self.CURR_K):
                    used_slack += self.MSTR_SCHE.MSTR_CAV_T_SLACK_UB.get(tuple([sl, k])) * self.MSTR_SCHE.MSTR_CAV_T_SLACK_UB.get(tuple([sl, k]))
                    used_slack += self.MSTR_SCHE.MSTR_CAV_T_SLACK_LB.get(tuple([sl, k])) * self.MSTR_SCHE.MSTR_CAV_T_SLACK_LB.get(tuple([sl, k]))
                rcstr = self.DELTA_SQ - used_slack                    
            else:
                rcstr = self.DELTA_SQ
            
            
            name = ['CSTR_T_MSLACK_M', str(mtype_id)]
            name = '_'.join(name)
            
            lcstr = 0
            for s in xrange(len(self.CAV_T_MSLACK_LB_PREVSES_MK[m])):
                lcstr += self.CAV_T_MSLACK_LB_PREVSES_MK[m][s] * self.CAV_T_MSLACK_LB_PREVSES_MK[m][s]
                lcstr += self.CAV_T_MSLACK_UB_PREVSES_MK[m][s] * self.CAV_T_MSLACK_UB_PREVSES_MK[m][s]
                
            self.CSTR_T_MSLACK_PREVSES_M.append(self.model.addConstr(lcstr <= rcstr, name))
          
        self.model.update()
        logging.debug("CSTR_T_MSLACK_PREVSES_M:\n %s" %self.CSTR_T_MSLACK_PREVSES_M)
            
            
    def _createCSTR_RoomTemperature_MSlack_from_ScheX_PrevSes(self):
        self.CSTR_MSlack_from_ScheX_LB_PREVSES = []
        self.CSTR_MSlack_from_ScheX_UB_PREVSES = []
        
        for m in xrange(len(self.CAV_T_MSLACK_LB_PREVSES_MK)): 
            self.CSTR_MSlack_from_ScheX_LB_PREVSES.append([])
            self.CSTR_MSlack_from_ScheX_UB_PREVSES.append([])
            for s in xrange(len(self.CAV_T_MSLACK_LB_PREVSES_MK[m])):       
                [mtype_id, dk] = self.CAV_T_MSLACK_PREVSES_MK_ReverseDict.get(tuple([m, s]))
                
                lcstr = self.CAV_T_MSLACK_LB_PREVSES_MK[m][s]
                name = ['CSTR_MSlack_from_ScheX_LB', str(mtype_id), str(dk)]
                name = '_'.join(name)
                self.CSTR_MSlack_from_ScheX_LB_PREVSES[m].append(self.model.addConstr(lcstr <= 1, name))
                
                lcstr = self.CAV_T_MSLACK_UB_PREVSES_MK[m][s]
                name = ['CSTR_MSlack_from_ScheX_UB', str(mtype_id), str(dk)]
                name = '_'.join(name)
                self.CSTR_MSlack_from_ScheX_UB_PREVSES[m].append(self.model.addConstr(lcstr <= 1, name))
                
        self.model.update()
        logging.debug("CSTR_MSlack_from_ScheX_LB_PREVSES:\n %s" %self.CSTR_MSlack_from_ScheX_LB_PREVSES)
        logging.debug("CSTR_MSlack_from_ScheX_UB_PREVSES:\n %s" %self.CSTR_MSlack_from_ScheX_UB_PREVSES)
                
            
        

# #==================================================================
# #   Overloading Function in solver_milp
# #==================================================================

    def _updMSTR_T_SLACK(self):
        logging.info("_updMSTR_T_SLACK   solver_milp_rb_eu")
        for l in xrange(len(self.CAV_T_SLACK_LB_LK)):
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
            for k in xrange(len(self.CAV_T_SLACK_LB_LK[l])):
                dk = self.CURR_K + k
                if self.MSTR_SCHE.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse.get(tuple([dl,dk])) is not None:    
                    self.MSTR_SCHE.updMSTR_CAV_T_SLACK_LK_SlackMap(dl, dk, self.CAV_T_SLACK_UB_LK[l][k].x, self.CAV_T_SLACK_LB_LK[l][k].x)
                 
    def _init_destroyAuxHVAC(self):
        logging.info("_init_destroyAuxHVAC   solver_milp_rb_eu")
        self.DESTROY_MSTR_CAV_T_SLACK_UB = {}
        self.DESTROY_MSTR_CAV_T_SLACK_LB = {}
           
    def _destroyAuxHVAC(self, l, k, duration):
        logging.info("_destroyAuxHVAC   solver_milp_rb_eu")
        for i in xrange(k, k+duration):
            key = tuple([l, i])
            self.DESTROY_MSTR_CAV_T_SLACK_UB[key] = self.MSTR_SCHE.MSTR_CAV_T_SLACK_UB.get(key)
            self.DESTROY_MSTR_CAV_T_SLACK_LB[key] = self.MSTR_SCHE.MSTR_CAV_T_SLACK_LB.get(key)
            del self.MSTR_SCHE.MSTR_CAV_T_SLACK_UB[key]
            del self.MSTR_SCHE.MSTR_CAV_T_SLACK_LB[key]
        
    def _rollbackAuxHVAC(self):
        logging.info("_rollbackAuxVAC   solver_milp_rb_eu")
        for k, v in self.DESTROY_MSTR_CAV_T_SLACK_UB.iteritems():
            self.MSTR_SCHE.MSTR_CAV_T_SLACK_UB[k] = v
        for k, v in self.DESTROY_MSTR_CAV_T_SLACK_LB.iteritems():
            self.MSTR_SCHE.MSTR_CAV_T_SLACK_LB[k] = v
            
    def _diagAuxHVAC(self):
        logging.info("DESTROY_MSTR_CAV_T_SLACK_UB : %s" %(self.DESTROY_MSTR_CAV_T_SLACK_UB))
        logging.info("DESTROY_MSTR_CAV_T_SLACK_LB : %s" %(self.DESTROY_MSTR_CAV_T_SLACK_LB))

#########--------------------------------

    def diagnose(self):
#         pass
        self.diagCAV_T_MSLACK()
        self.diagCAV_T_SLACK()
        self.diagCSTR_MeetingBasedRoomTemperature_Slack()
        self.diagCSTR_RoomTemperature()
        
        
    def diagCAV_T_MSLACK(self):
        for m in xrange(len(self.CAV_T_MSLACK_LB_MK)):
            for k in xrange(len(self.CAV_T_MSLACK_LB_MK[m])):
                if self.CAV_T_MSLACK_LB_MK[m][k].x > 0 or self.CAV_T_MSLACK_UB_MK[m][k].x > 0:
                    [dm, dk] = self.CAV_T_MSLACK_MK_ReverseDict.get(tuple([m,k]))
                    logging.info("CAV_T_MSLACK[%d][%d]  lb: %f, ub: %f" %(dm,dk, self.CAV_T_MSLACK_LB_MK[m][k].x, self.CAV_T_MSLACK_UB_MK[m][k].x))
                        
                        
    def diagCAV_T_SLACK(self):
        for l in xrange(len(self.CAV_T_SLACK_LB_LK)):
            for k in xrange(len(self.CAV_T_SLACK_LB_LK[l])):
                if self.CAV_T_SLACK_LB_LK[l][k].x > 0 or self.CAV_T_SLACK_UB_LK[l][k].x > 0:
                    if self.SCHE_MODE == 1:
                        dl = self.CURR_DESTROY_LOCATION[l]
                    else:
                        dl = l
                    
                    logging.info("CAV_T_SLACK[%d][%d]  lb: %f, ub: %f" %(dl,self.CURR_K+k, self.CAV_T_SLACK_LB_LK[l][k].x, self.CAV_T_SLACK_UB_LK[l][k].x))
                        
                        
    def diagCSTR_MeetingBasedRoomTemperature_Slack(self):
        for m in xrange(len(self.CAV_T_MSLACK_LB_MK)):
            if self.SCHE_MODE == 1:
                mtype_id = self.CURR_DESTROY_MTYPE[m]
            else:
                mtype_id = self.MTYPE_ID[m]
                
            lcstr = 0
            for k in xrange(len(self.CAV_T_MSLACK_LB_MK[m])):
                lcstr += self.CAV_T_MSLACK_LB_MK[m][k].x * self.CAV_T_MSLACK_LB_MK[m][k].x
                lcstr += self.CAV_T_MSLACK_UB_MK[m][k].x * self.CAV_T_MSLACK_UB_MK[m][k].x
                
            logging.info("CSTR_T_MSLACK_M [%s] :   %s <= %s" %(mtype_id, lcstr, self.DELTA_SQ))    
                        
                        
    def diagCSTR_RoomTemperature(self):
        for l in xrange(self.NUM_ROOM):
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l                
            for k in xrange(self.NUM_SLOT):
                t = self.CAV_T_LK[l][k].x
                lb = float(self.EAMS.TEMPERATURE_UNOCC_MIN) + (float(self.EAMS.TEMPERATURE_OCC_COMFORT_RANGE_INCR) * self.BAV_z_LK[l][k].x) - self.FIXED_SLACK * self.CAV_T_SLACK_LB_LK[l][k].x  
                ub = float(self.EAMS.TEMPERATURE_UNOCC_MAX) - (float(self.EAMS.TEMPERATURE_OCC_COMFORT_RANGE_DECR) * self.BAV_z_LK[l][k].x) + self.FIXED_SLACK * self.CAV_T_SLACK_UB_LK[l][k].x
                logging.info("CSTR_T_LK [%s][%s] :  %s <=  %s <= %s" %(dl, self.CURR_K+k, lb, t, ub))    
