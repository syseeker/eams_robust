from math import sqrt
import numpy as np
import logging
from solver_milp import Solver_MILP

from gurobipy import *

class Solver_MILP_Robust_OA(Solver_MILP):
    def __init__(self, MSTR_SCHE, EAMS, fn, curr_k, mtype, uniq_cmt, occ_k, case, lns_seed, timelimit, sche_mode, slack, delta, prob_guar):        
        logging.info("Loading Solver_OS_Greedy_RB_OuterApproximation")
        Solver_MILP.__init__(self, MSTR_SCHE, EAMS, fn, curr_k, mtype, uniq_cmt, occ_k, case, lns_seed, timelimit, sche_mode)
        
        self.MAX_SLACK = 5
        self.FIXED_SLACK = slack
        self.DELTA = delta
        self.PROB_GUAR = prob_guar
        logging.info("FIXED_SLACK: %s, DELTA: %s, PROB GUARANTEE: %s" %(self.FIXED_SLACK, self.DELTA, self.PROB_GUAR))
        
        self.OAT_DIFF_DICT = {}
        self.M_OAT_DIFF_DICT = {}
        if self.FIXED_SLACK == 0:  # OATA 
            self._populate_oatdiff()
            self._populate_meeting_oatdiff()
            
    def _populate_oatdiff(self):  
        for k in xrange(self.NUM_SLOT):            
            temperature = float(self.EAMS.OAT.values()[self.CURR_K+k])
            if temperature >= 18 and temperature < 20.5:
                diff = abs(20.5 - temperature)
            elif temperature > 23.5 and temperature <= 26:
                diff = abs(temperature - 23.5)
            elif temperature >= 20.5 and temperature <= 23.5:
                diff = 0.5
            else:
                diff = 3.0
                
            if diff > 3.0:
                diff = 3.0
                
            self.OAT_DIFF_DICT[self.CURR_K+k] = diff
            
        
    def _populate_meeting_oatdiff(self):
        meeting_list = []
        for m in xrange(self.NUM_MEETING_TYPE):
            if self.SCHE_MODE == 1:
                mtype_id = self.CURR_DESTROY_MTYPE[m]
                offset = self.MTYPE_ID.index(mtype_id)
                mid = self.MTYPE[offset].MLS[0] 
            else:
                mtype_id = self.MTYPE_ID[m]
                mid = self.MTYPE[m].MLS[0]            
            meeting_list.append(mid)
            
        for (dl, dk) in self.MSTR_SCHE.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse.keys():            
            if dk >= self.CURR_K and dk < self.CURR_K+self.NUM_SLOT:
                mtype_id = self.MSTR_SCHE.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse.get(tuple([dl,dk]))
                meeting_list.append(mtype_id)
                    
        for m in meeting_list:
            oat = []
            diff_oat = []
            [start, end] = self.EAMS.ML[m].TimeWindowsOffset[0]
            for i in range(start, end+1):
                temperature = float(self.EAMS.OAT.values()[i])
                if temperature < 20.5:
                    diff = abs(20.5 - temperature)
                elif temperature > 23.5:
                    diff = abs(temperature - 23.5)
                else:
                    diff = 0.5
                
                if diff > 3:
                    diff = 3
                oat.append(temperature)
                diff_oat.append(diff)
                    
            logging.info("_calc_prob_guarantee, temperature: %s" %(oat))
            logging.info("_calc_prob_guarantee, diff_oat:  %s" %(diff_oat))
            logging.info("_calc_prob_guarantee, sorted diff_oat:  %s" %sorted(diff_oat, reverse=True))
            
            self.M_OAT_DIFF_DICT[m] = sorted(diff_oat, reverse=True)
        
        
    def _createAuxVarSchedule(self):
        logging.info("_createAuxVarSchedule()")       
        self._createCAV_RoomTemperature_MSlack()
        self._createCAV_RoomTemperature_MSlack_PrevSes()
        
        
    def _createAuxVarHVAC(self):
        logging.debug("_createAuxVarHVAC()")        
        self._createCAV_RoomTemperature_Slack_LB()  
        self._createCAV_RoomTemperature_Slack_UB()
        
        
    def _createAuxCstrHVAC(self):
        logging.debug("_createAuxCstrHVAC()")
        self._createCSTR_MeetingBasedRoomTemperature_Slack()
        self._createCSTR_MeetingBasedRoomTemperature_Slack_PrevSes()
        
        self._createCSTR_RoomTemperature_MSlack_to_Slack()
        self._createCSTR_RoomTemperature_MSlack_to_Slack_PrevSes()
         
        self._createCSTR_RoomTemperature_X_to_Slack()

                
        
    def _updMSTR_AuxHVAC(self):
        logging.info("_updMSTR_AuxHVAC()")         
        self._updMSTR_T_SLACK()
        self._updMSTR_T_MSLACK() 
        
        
# #==================================================================
# #   Schedule
# #==================================================================
    
    def _createCAV_RoomTemperature_MSlack(self):
        self.CAV_T_MSLACK_LB_MK = [] 
        self.CAV_T_MSLACK_UB_MK = [] 
        self.CAV_T_MSLACK_MK_Dict = {}
        self.CAV_T_MSLACK_MK_ReverseDict = {}
        
        for m in xrange(self.NUM_MEETING_TYPE):  
            self.CAV_T_MSLACK_LB_MK.append([])
            self.CAV_T_MSLACK_UB_MK.append([])

            if self.SCHE_MODE == 1:
                mtype_id = self.CURR_DESTROY_MTYPE[m]
                offset = self.MTYPE_ID.index(mtype_id)
                mid = self.MTYPE[offset].MLS[0] 
            else:
                mtype_id = self.MTYPE_ID[m]
                mid = self.MTYPE[m].MLS[0]
                           
            mk = 0                                      
            for k in xrange(self.NUM_SLOT):
                if (self.EAMS.isInOngoingTimeWindows(mid, self.CURR_K+k) > 0 and
                    self._is_K_available(mtype_id, self.CURR_K+k) 
                    ):
                    logging.debug("M_K_%d_%d = in array offset(%d, %d)" %(mtype_id,self.CURR_K+k, m,mk))
                    
                    name = ['CAV_T_MSLACK_LB_MK', str(mtype_id), str(self.CURR_K+k)]                            
                    name = '_'.join(name)         
                    self.CAV_T_MSLACK_LB_MK[m].append(self.model.addVar(lb=0.0, ub=self.OAT_DIFF_DICT.get(self.CURR_K+k), vtype=GRB.CONTINUOUS, name=name))
                    self.CAV_T_MSLACK_MK_Dict[tuple([mtype_id,self.CURR_K+k])] = [m,mk]   
                    self.CAV_T_MSLACK_MK_ReverseDict[tuple([m,mk])] = [mtype_id,self.CURR_K+k]              
                    
                    name = ['CAV_T_MSLACK_UB_MK', str(mtype_id), str(self.CURR_K+k)]                            
                    name = '_'.join(name)         
                    self.CAV_T_MSLACK_UB_MK[m].append(self.model.addVar(lb=0.0, ub=self.OAT_DIFF_DICT.get(self.CURR_K+k), vtype=GRB.CONTINUOUS, name=name))
                    
                    mk = mk+1
                                    
        self.model.update()                           
        logging.debug("CAV_T_MSLACK_LB_MK:\n %s" %self.CAV_T_MSLACK_LB_MK)
        logging.debug("CAV_T_MSLACK_UB_MK:\n %s" %self.CAV_T_MSLACK_UB_MK)
        logging.debug("CAV_T_MSLACK_MK_Dict:\n %s" %self.CAV_T_MSLACK_MK_Dict)
        logging.debug("CAV_T_MSLACK_MK_ReverseDict:\n %s" %self.CAV_T_MSLACK_MK_ReverseDict)
        
         
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
            if self.SCHE_MODE == 0 or (self.SCHE_MODE == 1 and v[0] in self.CURR_DESTROY_LOCATION):
                self.CAV_T_MSLACK_LB_PREVSES_MK.append([])
                self.CAV_T_MSLACK_UB_PREVSES_MK.append([])
                slot = 0      
                for dl, dk in v:
                    name = ['CAV_T_MSLACK_LB_MK', str(mtype_id), str(dk)]                            
                    name = '_'.join(name)                  
                    self.CAV_T_MSLACK_LB_PREVSES_MK[m].append(self.model.addVar(lb=0.0, ub=self.OAT_DIFF_DICT.get(dk), vtype=GRB.CONTINUOUS, name=name))
                     
                    name = ['CAV_T_MSLACK_UB_MK', str(mtype_id), str(dk)]                            
                    name = '_'.join(name)                  
                    self.CAV_T_MSLACK_UB_PREVSES_MK[m].append(self.model.addVar(lb=0.0, ub=self.OAT_DIFF_DICT.get(dk), vtype=GRB.CONTINUOUS, name=name))
                      
                    self.CAV_T_MSLACK_PREVSES_MK_Dict[tuple([mtype_id,dk])] = [m, slot]
                    self.CAV_T_MSLACK_PREVSES_MK_ReverseDict[tuple([m, slot])] = [mtype_id,dk]
                    slot += 1                   
                m += 1
            
        self.model.update()                           
        logging.debug("CAV_T_MSLACK_LB_PREVSES_MK:\n %s" %self.CAV_T_MSLACK_LB_PREVSES_MK)
        logging.debug("CAV_T_MSLACK_UB_PREVSES_MK:\n %s" %self.CAV_T_MSLACK_UB_PREVSES_MK)

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
                self.CAV_T_SLACK_LB_LK[l].append(self.model.addVar(lb=0.0, ub=self.MAX_SLACK, vtype=GRB.CONTINUOUS, name=name))
                 
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
                self.CAV_T_SLACK_UB_LK[l].append(self.model.addVar(lb=0.0, ub=self.MAX_SLACK, vtype=GRB.CONTINUOUS, name=name))
                 
        self.model.update()
        logging.debug("CAV_T_SLACK_UB_LK:\n %s" %self.CAV_T_SLACK_UB_LK)


# #==================================================================
# #   Constraints 
# #==================================================================        
# #==================================================================
# #   HVAC 
# #==================================================================   

# max delta    p(m)
# 1                  0.49
# 1.414213562        0.74
# 1.732050808        0.86
# 2                  0.93
# 2.236067977        0.96
# 2.449489743        0.98
# 2.645751311        0.99
# 2.828427125        1.00
    def calc_oat_slack(self, mid):
        delta = -1
        a_bar = 0
#         a_hat = 0.5
        sorted_diff_oat = self.M_OAT_DIFF_DICT.get(mid)
        prob = self.PROB_GUAR
        dm = self.EAMS.ML[mid].Duration
        [start, end] = self.EAMS.ML[mid].TimeWindowsOffset[0]
                
        if len(sorted_diff_oat) == 1:
            if prob > 0:
#                 print sorted_diff_oat[0] - prob * sorted_diff_oat[0]
                return prob * sorted_diff_oat[0]
            else:
#                 print sorted_diff_oat[0]
                return sorted_diff_oat[0]
            
        if prob == 0.75:
            delta = 1.414213562
            slack = self._calc_slack(delta, len(sorted_diff_oat)*[a_bar], sorted_diff_oat)
        elif prob== 0.5:
            delta = 1            
            slack = self._calc_slack(delta, len(sorted_diff_oat)*[a_bar], sorted_diff_oat)
        elif prob == 0:
            slack = sum(sorted_diff_oat)
            
        if (end - start + dm) > 0:
            denom = (end - start + dm)
        else:
            denom = 1
        
        proportional_slack = slack * (float(dm)/denom)
        
        if prob > 0:    
            default_slack = sum(sorted_diff_oat) * (float(dm)/denom)
            final_slack = default_slack - proportional_slack        
#             print default_slack, " ", proportional_slack, " ", final_slack
#             print ""
        else:
            final_slack = proportional_slack
#             print final_slack
#             print ""
        
        return final_slack


    def _calc_slack(self, delta, a_bar, a_hat):
        ret = self.procedure(delta, a_bar, a_hat)
        if ret == -1:
            logging.critical("Proc failed to calc slack")
            return 0
        else:
            return ret
                
        
    def procedure(self, delta, a_bar, a_hat):
        S = []
        n = len(a_hat)        
        k = 1
        
        if delta > np.sqrt(len(a_hat)):
            logging.critical("%s, %s,  Error: delta > np.sqrt(len(a)) --- , %s > %s" %(a_hat, delta, delta, np.sqrt(len(a_hat))))
            return -1
            
        while k < n-1:
            numer = np.sqrt(delta**2 - len(S)) * abs(a_hat[k-1])
            denom = np.sqrt(np.sum([(x**2) for x in a_hat[k-1:]]))
                                      
            if numer/denom <= 1:                
                break
            else:
                S.append(k)
                k = k+1
#         print S
          
        a_hat_sum = 0
        for i in S:
            a_hat_sum += a_hat[i-1]
            
        slack = np.sum(a_bar) + a_hat_sum + np.sqrt(
                                     (delta**2-len(S))*
                                     np.sum([(x**2) for x in a_hat[len(S):]])
                                     )        
        return slack
    
    
    def _createCSTR_MeetingBasedRoomTemperature_Slack(self):
        """Sum of all slack should be less than delta for each meeting"""
        self.CSTR_T_SLACK_M = []
         
        for m in xrange(len(self.CAV_T_MSLACK_LB_MK)):
            if self.SCHE_MODE == 1:
                mtype_id = self.CURR_DESTROY_MTYPE[m]                
            else:
                mtype_id = self.MTYPE_ID[m]
                            
            if self.FIXED_SLACK == 0:
                slack = self.calc_oat_slack(mtype_id)
            else:
                slack = 0                
            logging.info("Meeting ID: %s, slack: %s" %(mtype_id, slack))
                 
            lcstr = 0
            for k in xrange(len(self.CAV_T_MSLACK_LB_MK[m])):
                lcstr += self.CAV_T_MSLACK_LB_MK[m][k] 
                lcstr += self.CAV_T_MSLACK_UB_MK[m][k]
            
            name = ['CSTR_T_SLACK_M', str(mtype_id)]
            name = '_'.join(name)
            self.CSTR_T_SLACK_M.append(self.model.addConstr(lcstr <= slack, name))
            
        self.model.update()
        logging.debug("CSTR_T_SLACK_M:\n %s" %self.CSTR_T_SLACK_M)
        
        
    
    def _createCSTR_MeetingBasedRoomTemperature_Slack_PrevSes(self):
        """Sum of all slack should be less than delta for each meeting. For ongoing meeting, sum of all slack should be less than (DELTA_SQ - those that has been used)."""
        self.CSTR_T_SLACK_PREVSES_M = []
                
        for m in xrange(len(self.CAV_T_MSLACK_LB_PREVSES_MK)):            
            [mtype_id,_] = self.CAV_T_MSLACK_PREVSES_MK_ReverseDict.get(tuple([m, 0]))
            [sl, sk] = self.MSTR_SCHE.MSTR_BDV_x_MLK_MeetingMap.get(mtype_id)
                        
            if self.FIXED_SLACK == 0:
                slack = self.calc_oat_slack(mtype_id)
            else:
                slack = 0                
            logging.info("Meeting ID: %s, slack: %s" %(mtype_id, slack))
                            
            if self.SCHE_MODE == 0 or (self.SCHE_MODE == 1 and sl in self.CURR_DESTROY_LOCATION):
                # if meeting has started before self.CURR_K, and is still ongoing. 
                # Check T_SLACK used. Sum of new T_MSLACK should be DELTA_SQ - those that has been used.
                if sk < self.CURR_K:
                    logging.info("Meeting %s has started at slot %s and still ongoing.." %(m, sk))
                    used_slack_lb = 0
                    used_slack_ub = 0
                    for k in xrange(sk, self.CURR_K):
                        used_slack_lb += self.MSTR_SCHE.MSTR_CAV_T_MSLACK_LB.get(tuple([mtype_id, k])) 
                        used_slack_ub += self.MSTR_SCHE.MSTR_CAV_T_MSLACK_UB.get(tuple([mtype_id, k]))
                    rcstr = slack - used_slack_lb - used_slack_ub
                else:
                    rcstr = slack
                
                lcstr = 0
                for s in xrange(len(self.CAV_T_MSLACK_LB_PREVSES_MK[m])):
                    lcstr += self.CAV_T_MSLACK_LB_PREVSES_MK[m][s] 
                    lcstr += self.CAV_T_MSLACK_UB_PREVSES_MK[m][s]
                
                name = ['CSTR_T_SLACK_M', str(mtype_id)]
                name = '_'.join(name)
                self.CSTR_T_SLACK_PREVSES_M.append(self.model.addConstr(lcstr <= rcstr, name))
                          
        self.model.update()
        logging.debug("CSTR_T_SLACK_PREVSES_M:\n %s" %self.CSTR_T_SLACK_PREVSES_M)
        
    
    def is_not_alloc_prev_sess(self, l, k):
        m = self.MSTR_SCHE.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse.get(tuple([l, k]))
        if m is None or m in self.MTYPE_ID:
            return True
        else:
            return False


    def get_x(self, dl, k, mid):
        k_m = []
        rcstr = 0
        k_m = self.EAMS.getFeasibleStartTime(mid, k)
        if k_m:               
            for fk in k_m:        
                alloc = self.BDV_x_MLK_Dict.get(tuple([mid, dl, fk]))
                if alloc:
                    [xm, xl, xk] = alloc
                    rcstr += self.BDV_x_MLK[xm][xl][xk]
                   
        return rcstr
    
        
    def _createCSTR_RoomTemperature_MSlack_to_Slack(self):
        self.CSTR_MSlack_to_Slack_LB_leq = []
        self.CSTR_MSlack_to_Slack_LB_geq = []
        self.CSTR_MSlack_to_Slack_UB_leq = []
        self.CSTR_MSlack_to_Slack_UB_geq = []
        
        for m in xrange(len(self.CAV_T_MSLACK_LB_MK)):
            self.CSTR_MSlack_to_Slack_LB_leq.append([])
            self.CSTR_MSlack_to_Slack_LB_geq.append([])
            self.CSTR_MSlack_to_Slack_UB_leq.append([])
            self.CSTR_MSlack_to_Slack_UB_geq.append([])
            
            for k in xrange(len(self.CAV_T_MSLACK_LB_MK[m])):
                self.CSTR_MSlack_to_Slack_LB_leq[m].append([])
                self.CSTR_MSlack_to_Slack_LB_geq[m].append([])
                self.CSTR_MSlack_to_Slack_UB_leq[m].append([])
                self.CSTR_MSlack_to_Slack_UB_geq[m].append([])
                
                [dm, dk] = self.CAV_T_MSLACK_MK_ReverseDict.get(tuple([m,k]))
                for l in xrange(self.NUM_ROOM):
                    if self.SCHE_MODE == 1:
                        dl = self.CURR_DESTROY_LOCATION[l]
                    else:
                        dl = l
                        
                    if self.is_not_alloc_prev_sess(dl, dk):
                        x_cstr = self.get_x(dl, dk, dm)
                        t_slack_k = dk - self.CURR_K
                        lcstr_lb = self.CAV_T_SLACK_LB_LK[l][t_slack_k]
                        lcstr_ub = self.CAV_T_SLACK_UB_LK[l][t_slack_k]
                        
                        # For LEQ
                        rcstr_lb_leq = self.CAV_T_MSLACK_LB_MK[m][k] + (1-x_cstr)*self.MAX_SLACK
                        name = ['CSTR_MSlack_to_Slack_LB_LEQ', str(dm), str(dl), str(dk)]
                        name = '_'.join(name)
                        self.CSTR_MSlack_to_Slack_LB_leq[m][k].append(self.model.addConstr(lcstr_lb <= rcstr_lb_leq, name))
                        
                        # For GEQ   
                        rcstr_lb_geq = self.CAV_T_MSLACK_LB_MK[m][k] - (1-x_cstr)*self.MAX_SLACK
                        name = ['CSTR_MSlack_to_Slack_LB_GEQ', str(dm), str(dl), str(dk)]
                        name = '_'.join(name)
                        self.CSTR_MSlack_to_Slack_LB_geq[m][k].append(self.model.addConstr(lcstr_lb >= rcstr_lb_geq, name))
                        
                        # For LEQ
                        rcstr_ub_leq = self.CAV_T_MSLACK_UB_MK[m][k] + (1-x_cstr)*self.MAX_SLACK
                        name = ['CSTR_MSlack_to_Slack_UB_LEQ', str(dm), str(dl), str(dk)]
                        name = '_'.join(name)
                        self.CSTR_MSlack_to_Slack_UB_leq[m][k].append(self.model.addConstr(lcstr_ub <= rcstr_ub_leq, name))
                        
                        # For GEQ   
                        rcstr_ub_geq = self.CAV_T_MSLACK_UB_MK[m][k] - (1-x_cstr)*self.MAX_SLACK
                        name = ['CSTR_MSlack_to_Slack_UB_GEQ', str(dm), str(dl), str(dk)]
                        name = '_'.join(name)
                        self.CSTR_MSlack_to_Slack_UB_geq[m][k].append(self.model.addConstr(lcstr_ub >= rcstr_ub_geq, name))
        
        self.model.update()                           
        logging.debug("CSTR_MSlack_to_Slack_LB_leq:\n %s" %self.CSTR_MSlack_to_Slack_LB_leq)
        logging.debug("CSTR_MSlack_to_Slack_LB_geq:\n %s" %self.CSTR_MSlack_to_Slack_LB_geq)
        logging.debug("CSTR_MSlack_to_Slack_UB_leq:\n %s" %self.CSTR_MSlack_to_Slack_UB_leq)
        logging.debug("CSTR_MSlack_to_Slack_UB_geq:\n %s" %self.CSTR_MSlack_to_Slack_UB_geq)
        
        
    def _createCSTR_RoomTemperature_MSlack_to_Slack_PrevSes(self):
        self.CSTR_Prevses_MSlack_to_Slack_LB_leq = []
        self.CSTR_Prevses_MSlack_to_Slack_LB_geq = []
        self.CSTR_Prevses_MSlack_to_Slack_UB_leq = []
        self.CSTR_Prevses_MSlack_to_Slack_UB_geq = []
        
        for m in xrange(len(self.CAV_T_MSLACK_LB_PREVSES_MK)):
            [mid,_] = self.CAV_T_MSLACK_PREVSES_MK_ReverseDict.get(tuple([m, 0]))
            [dl, _] = self.MSTR_SCHE.MSTR_BDV_x_MLK_MeetingMap.get(mid)
                        
            if self.SCHE_MODE == 0 or (self.SCHE_MODE == 1 and dl in self.CURR_DESTROY_LOCATION):                
                self.CSTR_Prevses_MSlack_to_Slack_LB_leq.append([])
                self.CSTR_Prevses_MSlack_to_Slack_LB_geq.append([])
                self.CSTR_Prevses_MSlack_to_Slack_UB_leq.append([])
                self.CSTR_Prevses_MSlack_to_Slack_UB_geq.append([])
                
                for s in xrange(len(self.CAV_T_MSLACK_LB_PREVSES_MK[m])):
                    [dm, dk] = self.CAV_T_MSLACK_PREVSES_MK_ReverseDict.get(tuple([m, s]))
                        
                    x_cstr = self.get_x(dl, dk, dm)
                    t_slack_k = dk - self.CURR_K
                    if self.SCHE_MODE == 1:
                        l = self.CURR_DESTROY_LOCATION.index(dl)
                    else:
                        l = dl
                    lcstr_lb = self.CAV_T_SLACK_LB_LK[l][t_slack_k]
                    lcstr_ub = self.CAV_T_SLACK_UB_LK[l][t_slack_k]
                    
                    # For LEQ
                    rcstr_lb_leq = self.CAV_T_MSLACK_LB_PREVSES_MK[m][s] + (1-x_cstr)*self.MAX_SLACK
                    name = ['CSTR_MSlack_to_Slack_LB_LEQ', str(dm), str(dl), str(dk)]
                    name = '_'.join(name)
                    self.CSTR_Prevses_MSlack_to_Slack_LB_leq[m].append(self.model.addConstr(lcstr_lb <= rcstr_lb_leq, name))
                    
                    # For GEQ   
                    rcstr_lb_geq = self.CAV_T_MSLACK_LB_PREVSES_MK[m][s] - (1-x_cstr)*self.MAX_SLACK
                    name = ['CSTR_MSlack_to_Slack_LB_GEQ', str(dm), str(dl), str(dk)]
                    name = '_'.join(name)
                    self.CSTR_Prevses_MSlack_to_Slack_LB_geq[m].append(self.model.addConstr(lcstr_lb >= rcstr_lb_geq, name))
                    
                    # For LEQ
                    rcstr_ub_leq = self.CAV_T_MSLACK_UB_PREVSES_MK[m][s] + (1-x_cstr)*self.MAX_SLACK
                    name = ['CSTR_MSlack_to_Slack_UB_LEQ', str(dm), str(dl), str(dk)]
                    name = '_'.join(name)
                    self.CSTR_Prevses_MSlack_to_Slack_UB_leq[m].append(self.model.addConstr(lcstr_ub <= rcstr_ub_leq, name))
                    
                    # For GEQ   
                    rcstr_ub_geq = self.CAV_T_MSLACK_UB_PREVSES_MK[m][s] - (1-x_cstr)*self.MAX_SLACK
                    name = ['CSTR_MSlack_to_Slack_UB_GEQ', str(dm), str(dl), str(dk)]
                    name = '_'.join(name)
                    self.CSTR_Prevses_MSlack_to_Slack_UB_geq[m].append(self.model.addConstr(lcstr_ub >= rcstr_ub_geq, name))
                    
        self.model.update()
        logging.debug("CSTR_Prevses_MSlack_to_Slack_LB_leq:\n %s" %self.CSTR_Prevses_MSlack_to_Slack_LB_leq)
        logging.debug("CSTR_Prevses_MSlack_to_Slack_LB_geq:\n %s" %self.CSTR_Prevses_MSlack_to_Slack_LB_geq)
        logging.debug("CSTR_Prevses_MSlack_to_Slack_UB_leq:\n %s" %self.CSTR_Prevses_MSlack_to_Slack_UB_leq)
        logging.debug("CSTR_Prevses_MSlack_to_Slack_UB_geq:\n %s" %self.CSTR_Prevses_MSlack_to_Slack_UB_geq)
        
        
    def _createCSTR_RoomTemperature_X_to_Slack(self):
        self.CSTR_X_to_Slack_LB = []
        self.CSTR_X_to_Slack_UB = []
                
        for l in xrange(self.NUM_ROOM):
            self.CSTR_X_to_Slack_LB.append([])
            self.CSTR_X_to_Slack_UB.append([])
            
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
            
            for k in xrange(self.NUM_SLOT):
                xctr = 0
                
                # For pre-alloc meeting
                if self.MSTR_SCHE.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse.get(tuple([dl,self.CURR_K+k])) is not None:
                    rcstr = self.OAT_DIFF_DICT.get(self.CURR_K+k)    # Just set {lk} to Tu if it is occupied
                # For new meeting
                else:
                    for m in xrange(self.NUM_MEETING_TYPE):
                        if self.SCHE_MODE == 1:
                            mtype_id = self.CURR_DESTROY_MTYPE[m]
                            offset = self.MTYPE_ID.index(mtype_id)
                            mid = self.MTYPE[offset].MLS[0] 
                        else:
                            mtype_id = self.MTYPE_ID[m]
                            mid = self.MTYPE[m].MLS[0]
                        xctr += self.OAT_DIFF_DICT.get(self.CURR_K+k) * self.get_x(dl, self.CURR_K+k, mid)
                    rcstr = xctr
                
                lcstr_lb = self.CAV_T_SLACK_LB_LK[l][k]
                name = ['CSTR_X_to_Slack_LB', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)    
                self.CSTR_X_to_Slack_LB[l].append(self.model.addConstr(lcstr_lb <= rcstr, name))
                
                lcstr_ub = self.CAV_T_SLACK_UB_LK[l][k]
                name = ['CSTR_X_to_Slack_UB', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)    
                self.CSTR_X_to_Slack_UB[l].append(self.model.addConstr(lcstr_ub <= rcstr, name))
                 
        self.model.update()
        logging.debug("CSTR_X_to_Slack_LB:\n %s" %self.CSTR_X_to_Slack_LB)
        logging.debug("CSTR_X_to_Slack_UB:\n %s" %self.CSTR_X_to_Slack_UB)
        
        
   
   
   
# #==================================================================
# #   Overloading Function in solver_milp
# #==================================================================
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
                rcstr = float(self.EAMS.TEMPERATURE_UNOCC_MIN) + (float(self.EAMS.TEMPERATURE_OCC_COMFORT_RANGE_INCR) * self.BAV_z_LK[l][k]) - self.CAV_T_SLACK_LB_LK[l][k]
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
                rcstr = float(self.EAMS.TEMPERATURE_UNOCC_MAX) - (float(self.EAMS.TEMPERATURE_OCC_COMFORT_RANGE_DECR)*self.BAV_z_LK[l][k]) + self.CAV_T_SLACK_UB_LK[l][k]
                self.CSTR_T_LK_ub[l].append(self.model.addConstr(lcstr <= rcstr, name))
             
        self.model.update()
        logging.debug("CSTR_T_LK_ub:\n %s" %self.CSTR_T_LK_ub)
        

    def _updMSTR_T_SLACK(self):
        logging.info("_updMSTR_T_SLACK   solver_milp_rb_oa")
        for l in xrange(len(self.CAV_T_SLACK_LB_LK)):
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
            for k in xrange(len(self.CAV_T_SLACK_LB_LK[l])):
                dk = self.CURR_K + k
                if self.MSTR_SCHE.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse.get(tuple([dl,dk])) is not None:    
                    self.MSTR_SCHE.updMSTR_CAV_T_SLACK_LK_SlackMap(dl, dk, self.CAV_T_SLACK_UB_LK[l][k].x, self.CAV_T_SLACK_LB_LK[l][k].x)
        logging.info("MSTR_CAV_T_SLACK_UB: %s" %self.MSTR_SCHE.MSTR_CAV_T_SLACK_UB)
        logging.info("MSTR_CAV_T_SLACK_LB: %s" %self.MSTR_SCHE.MSTR_CAV_T_SLACK_LB)            
                          
    def _updMSTR_T_MSLACK(self):
        logging.info("_updMSTR_T_MSLACK   solver_milp_rb_oa")
        for m in xrange(len(self.CAV_T_MSLACK_LB_MK)):
            for k in xrange(len(self.CAV_T_MSLACK_LB_MK[m])):
                [dmtype_id, dk] = self.CAV_T_MSLACK_MK_ReverseDict.get(tuple([m,k]))
#                 for l in xrange(self.NUM_ROOM):
#                     if self.SCHE_MODE == 1:
#                         dl = self.CURR_DESTROY_LOCATION[l]
#                     else:
#                         dl = l                
#                 mid = self.MSTR_SCHE.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse.get(tuple([dl,dk]))
#                 if (mid is not None) and (mid == dmtype_id):    
                self.MSTR_SCHE.updMSTR_CAV_T_MSLACK_MK_SlackMap(dmtype_id, dk, self.CAV_T_MSLACK_UB_MK[m][k].x, self.CAV_T_MSLACK_LB_MK[m][k].x)
        logging.info("MSTR_CAV_T_MSLACK_UB: %s" %self.MSTR_SCHE.MSTR_CAV_T_MSLACK_UB)
        logging.info("MSTR_CAV_T_MSLACK_LB: %s" %self.MSTR_SCHE.MSTR_CAV_T_MSLACK_LB)  
                 
    def _init_destroyAuxHVAC(self):
        logging.info("_init_destroyAuxHVAC   solver_milp_rb_oa")
        self.DESTROY_MSTR_CAV_T_SLACK_UB = {}
        self.DESTROY_MSTR_CAV_T_SLACK_LB = {}
        self.DESTROY_MSTR_CAV_T_MSLACK_UB = {}
        self.DESTROY_MSTR_CAV_T_MSLACK_LB = {}
        
           
    def _destroyAuxHVAC(self, l, k, duration):
        logging.info("_destroyAuxHVAC   solver_milp_rb_oa")
        for i in xrange(k, k+duration):
            try:
                key = tuple([l, i])
                self.DESTROY_MSTR_CAV_T_SLACK_UB[key] = self.MSTR_SCHE.MSTR_CAV_T_SLACK_UB.get(key)
                self.DESTROY_MSTR_CAV_T_SLACK_LB[key] = self.MSTR_SCHE.MSTR_CAV_T_SLACK_LB.get(key)
                del self.MSTR_SCHE.MSTR_CAV_T_SLACK_UB[key]
                del self.MSTR_SCHE.MSTR_CAV_T_SLACK_LB[key]                
                
                mid = self.MSTR_SCHE.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse.get(tuple([l,i]))
                key = tuple([mid, i])
                self.DESTROY_MSTR_CAV_T_MSLACK_UB[key] = self.MSTR_SCHE.MSTR_CAV_T_MSLACK_UB.get(key)
                self.DESTROY_MSTR_CAV_T_MSLACK_LB[key] = self.MSTR_SCHE.MSTR_CAV_T_MSLACK_LB.get(key)
                del self.MSTR_SCHE.MSTR_CAV_T_MSLACK_UB[key]
                del self.MSTR_SCHE.MSTR_CAV_T_MSLACK_LB[key]                
            except (KeyError), e:        
                logging.critical('%s' % (e))
                logging.critical('DESTROY_MSTR_CAV_T_MSLACK_UB: %s' %(self.DESTROY_MSTR_CAV_T_MSLACK_UB))
                logging.critical('MSTR_SCHE.MSTR_CAV_T_MSLACK_UB: %s' %(self.MSTR_SCHE.MSTR_CAV_T_MSLACK_UB))
                  
            
        
    def _rollbackAuxHVAC(self):
        logging.info("_rollbackAuxVAC   solver_milp_rb_oa")
        for k, v in self.DESTROY_MSTR_CAV_T_SLACK_UB.iteritems():
            self.MSTR_SCHE.MSTR_CAV_T_SLACK_UB[k] = v
        for k, v in self.DESTROY_MSTR_CAV_T_SLACK_LB.iteritems():
            self.MSTR_SCHE.MSTR_CAV_T_SLACK_LB[k] = v
            
        for k, v in self.DESTROY_MSTR_CAV_T_MSLACK_UB.iteritems():
            self.MSTR_SCHE.MSTR_CAV_T_MSLACK_UB[k] = v
        for k, v in self.DESTROY_MSTR_CAV_T_MSLACK_LB.iteritems():
            self.MSTR_SCHE.MSTR_CAV_T_MSLACK_LB[k] = v
            
            
    def _diagAuxHVAC(self):
        logging.info("DESTROY_MSTR_CAV_T_SLACK_UB : %s" %(self.DESTROY_MSTR_CAV_T_SLACK_UB))
        logging.info("DESTROY_MSTR_CAV_T_SLACK_LB : %s" %(self.DESTROY_MSTR_CAV_T_SLACK_LB))
        logging.info("DESTROY_MSTR_CAV_T_MSLACK_UB : %s" %(self.DESTROY_MSTR_CAV_T_MSLACK_UB))
        logging.info("DESTROY_MSTR_CAV_T_MSLACK_LB : %s" %(self.DESTROY_MSTR_CAV_T_MSLACK_LB))

# #==================================================================
# #   Diagnose
# #==================================================================                
    def diagnose(self):
        pass
#         self.diagCAV_T_MSLACK()
#         self.diagCAV_T_SLACK()
#         self.diagCSTR_RoomTemperature()
        
        
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
                                                                                
    def diagCSTR_RoomTemperature(self):
        for l in xrange(self.NUM_ROOM):
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l                
            for k in xrange(self.NUM_SLOT):
                t = self.CAV_T_LK[l][k].x
                lb = float(self.EAMS.TEMPERATURE_UNOCC_MIN) + (float(self.EAMS.TEMPERATURE_OCC_COMFORT_RANGE_INCR) * self.BAV_z_LK[l][k].x) - self.CAV_T_SLACK_LB_LK[l][k].x  
                ub = float(self.EAMS.TEMPERATURE_UNOCC_MAX) - (float(self.EAMS.TEMPERATURE_OCC_COMFORT_RANGE_DECR) * self.BAV_z_LK[l][k].x) + self.CAV_T_SLACK_UB_LK[l][k].x
                logging.info("CSTR_T_LK [%s][%s] :  %s <=  %s <= %s" %(dl, self.CURR_K+k, lb, t, ub))    

   
            