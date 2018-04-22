import sys
import logging
from time import time
from datetime import datetime
from random import randrange, sample, uniform
from solver_milp import Solver_MILP
from solver_milp_rb_euclidean import Solver_MILP_Robust_EU
from solver_milp_rb_outerapprox import Solver_MILP_Robust_OA
# from solver_milp_rb_precalc import Solver_MILP_Robust_PC
from solver_error import SOLVER_LNS_Error
from eams_error import EAMS_Error

class Solver_LNS():
    def __init__(self, MSTR_SCHE, EAMS, fn, lns_limit, mip_limit, curr_k, mtype, uniq_cmt, occ_k, case, lns_seed, mode='DEF', slack=0, delta=0, prob_guar=0):    
        self.err = SOLVER_LNS_Error()    
        self.EAMS = EAMS
        self.CASECFG = case
        self.CURR_K = curr_k
        self.SCHE_MSTR = MSTR_SCHE
                
        self.MIP_TIMELIMIT_SEC = 1 #mip_limit # 8.5 sec
        self.LNS_DESTROY_2_PCT = 0.64 
        self.LNS_DESTROY_3_PCT = 0.28
        self.LNS_DESTROY_4_PCT = 0.08        
        self._calcRoomDestroyDist()
                                
        self.MIP_DEFAULT_NOTIMELIMIT = 1e+100
        self.LNS_TIMELIMIT_SEC = 1 #lns_limit * 60   
        self.LOG_LNS_TRACE = 0
        self.LOG_LNS_SUMMARY = 0
                        
        self.SCHE_MODE = 0              # 0: full schedule, 1: partial schedule
        self.STATUS = ['', 'LOADED', 'OPTIMAL', 'INFEASIBLE', 'INF_OR_UNBD', 'UNBOUNDED', 'CUTOFF', 'ITERATION_LIMIT', 'NODE_LIMIT', 'TIME_LIMIT', 'SOLUTION_LIMIT', 'INTERRUPTED', 'NUMERIC', 'SUBOPTIMAL']
                                     
        logging.info("=====================================================")
        logging.info("    Initialize LNS    ")
        logging.info("=====================================================")
        logging.info("LNS_SEED: %f" %(lns_seed))
        logging.info("LNS time limit: %f" %(self.LNS_TIMELIMIT_SEC))
        logging.info("MIP time limit: %f" %(self.MIP_TIMELIMIT_SEC))
        logging.info("LNS Destroy 2 rooms probability: %f - %g" %(self.LNS_DESTROY_2_PCT, self.LNS_DESTROY_2_PCT_PRIME))
        logging.info("LNS Destroy 3 rooms probability: %f - %g" %(self.LNS_DESTROY_3_PCT, self.LNS_DESTROY_3_PCT_PRIME))
        logging.info("LNS Destroy 4 rooms probability: %f - %g" %(self.LNS_DESTROY_4_PCT, 1-(self.LNS_DESTROY_2_PCT_PRIME + self.LNS_DESTROY_3_PCT_PRIME)))
                         
        if mode == 'EU_RB':
            self.milp_solver = Solver_MILP_Robust_EU(MSTR_SCHE, EAMS, fn, curr_k, mtype, uniq_cmt, occ_k, case, lns_seed, -1, self.SCHE_MODE, slack, delta)
        elif mode == 'OA_RB':
            self.milp_solver = Solver_MILP_Robust_OA(MSTR_SCHE, EAMS, fn, curr_k, mtype, uniq_cmt, occ_k, case, lns_seed, -1, self.SCHE_MODE, slack, delta, prob_guar)
#         elif mode == 'PC_RB':
#             self.milp_solver = Solver_MILP_Robust_PC(MSTR_SCHE, EAMS, fn, curr_k, mtype, uniq_cmt, occ_k, case, lns_seed, -1, self.SCHE_MODE, slack, delta)
        else:
            self.milp_solver = Solver_MILP(MSTR_SCHE, EAMS, fn, curr_k, mtype, uniq_cmt, occ_k, case, lns_seed, -1, self.SCHE_MODE)
      
       
    def run(self):
        self.lns_run_count = 0
        self.curr_best_schedule = []
        self.curr_optval = -1
            
        self.NUM_DESTROY_PER_ROOM = [0] * len(self.EAMS.RL)
        self.NUM_ROOM_DESTROYED_PER_ROUND = []
        self.NUM_MEETING_DESTROY_PER_ROUND = []
        
        # Get Initial Schedule
        start = time()
        logging.info("\n\n==================================================================")
        logging.info("\t\t Initial Schedule, Minimum Room Alloc Per Day")
        logging.info("==================================================================")
        timestart = time()
        status = self.milp_solver.getInitialSchedule() 
        logging.info("Current round takes getInitialSchedule TimeEnd after: %s s" %(time()-timestart))
        if status == self.err.solver_lns_no_initial_solution():
            logging.info("Fail to find an initial schedule.")
            return EAMS_Error().eams_infeasible()
        
        # Initialize HVAC model & optimize HVAC control based on initial schedule
        logging.info("\n\n==================================================================")
        logging.info("\t\t HVAC Control for Initial Schedule")
        logging.info("==================================================================")
        timestart = time()
        self.curr_optval = self.milp_solver.initHVACModelNEnergyObjBasedOnInitialSchedule()
        logging.info("Current round takes initHVACModelNEnergyObjBasedOnInitialSchedule TimeEnd after: %s s" %(time()-timestart))        
        if self.curr_optval == self.err.solver_lns_infeasible_hvac_ctrl():
            logging.info("Fail to find HVAC control for the given initial schedule.")
            return EAMS_Error().eams_infeasible()
        else:
            logging.info("++++++++ OBJVALUE ++++++++ Initial optimal value :  %f" %(self.curr_optval))
            if self.LOG_LNS_TRACE:
                self._log_ObjValue_Neighbourhood(datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"), self.curr_optval, -1)
          
        self.milp_solver.updateGurobiParam(self.MIP_TIMELIMIT_SEC)    # Update this after initial solution (because we don't want to limit initial solution)
        self.start_t = time()
        curr_t = self.start_t
        # Run until system time limit is reached
        while curr_t - self.start_t < self.LNS_TIMELIMIT_SEC:  
            logging.info("\n\n==================================================================")
            logging.info("\t\t Destroy Neighbourhood Run #%d" %(self.lns_run_count))
            logging.info("==================================================================")            
            [locls, timels, mls] = self._destroyNeighbourhood()
                       
            logging.info("\n\n==================================================================")
            logging.info("\t\t Rebuild Neighbourhood")
            logging.info("==================================================================")
            objval_partial = self.milp_solver.rebuildNeighbourhood(self.lns_run_count, locls, timels, mls)
            self.NUM_MEETING_DESTROY_PER_ROUND.append(len(self.milp_solver.DESTROY_MSTR_BDV_x_MLK_MeetingMap.keys()))
            if (objval_partial < 0):  # NOTE: no destroy made or no feasible result for this round...
                curr_t = time()
                self.lns_run_count = self.lns_run_count+1   
                continue
              
            logging.info("\n\n==================================================================")
            logging.info("\t\t Evaluate Neighbourhood")
            logging.info("==================================================================")
            status = self._evaluateNeighbourhood(locls, objval_partial)
            if self.LOG_LNS_TRACE:
                self._log_ObjValue_Neighbourhood(datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"), self.curr_optval, 0)
            if status > 0:
                logging.info("\n\n==================================================================")
                logging.info("\t\t Update Neighbourhood")
                logging.info("==================================================================")
                self._updateNeighbourhood()
            else:
                logging.info("\n\n==================================================================")
                logging.info("\t\t Rollback Neighbourhood")
                logging.info("==================================================================")
                self._rollbackNeighbourhood()
#             self.milp_solver.diagnose()                
#             self.SCHE_MSTR.diagnose()
                       
            if (time() - self.start_t) > self.LNS_TIMELIMIT_SEC:
                break
                      
            curr_t = time()
            logging.info("Last round solve time from the start time: %g sec" %(curr_t - self.start_t))
                        
            self.lns_run_count = self.lns_run_count+1    
            
        self.SCHE_MSTR.resetMSTR_Location_AllocMap()
        end = time()-start
                
        if self.LOG_LNS_SUMMARY:
            logging.info("\n\n==================================================================")
            logging.info("\t\t Summary")
            logging.info("==================================================================")
            logging.info("Total LNS runtime for this round: %g s" %end)
            logging.info("Statistics of destroy per room: %s" %(self.NUM_DESTROY_PER_ROOM))
            logging.info("Number of room destroyed per round: %s" %(self.NUM_ROOM_DESTROYED_PER_ROUND))
            logging.info("Number of meeting destroyed per round: %s" %(self.NUM_MEETING_DESTROY_PER_ROUND))
        
#         self.milp_solver.diagnose()
#         self.SCHE_MSTR.diagnose()        
        return True
        
        
    #===========================================================================
    # LNS Evaluate
    #===========================================================================
    def _evaluateNeighbourhood(self, locls, newobj):
        rooms = set(range(0, len(self.EAMS.RL))).difference(locls) 
        e_nodr = self.milp_solver.getEnergyConsumption(rooms, self.CURR_K)

        if (e_nodr + newobj) < (self.curr_optval): # found a better solution
            self.curr_optval = e_nodr + newobj
            logging.info("++++++++ OBJVALUE ++++++++ New optimal value with (%f + %f) :  %f. Accept" %(e_nodr, newobj, self.curr_optval))
            return 1
        else:
            logging.info("++++++++ OBJVALUE ++++++++ No better solution found with (%f + %f) =    %f (>= %f). Reject." %(e_nodr, newobj, e_nodr + newobj, self.curr_optval))
            return -1
         
    def _updateNeighbourhood(self):
        self.milp_solver.updateNeighbourhood()
        
    def _rollbackNeighbourhood(self):
        self.milp_solver.rollbackNeighbourhood()
             
          
         
    #===========================================================================
    # LNS Destroy
    #===========================================================================
    def _destroyNeighbourhood(self):
        timels = []
        mls = []
         
        self.LNS_DESTROY_MAX_ROOMS = self._getNumRoomToDestroy()
        locls = self._selectArbitraryRoom()
         
        if len(locls) == 0:
            logging.info("No room to destroy")
        else:
            for i in xrange(len(locls)):
                rid = locls[i]
                self.NUM_DESTROY_PER_ROOM[rid] = self.NUM_DESTROY_PER_ROOM[rid] + 1 
         
        return [locls, timels, mls]
         
         
    def _getNumRoomToDestroy(self):                
        num_rooms = 0
        a = uniform(0,1)  # generate random floating number from uniform distribution
         
        if a <= self.LNS_DESTROY_2_PCT_PRIME:
            num_rooms = 2
        elif a <= (self.LNS_DESTROY_2_PCT_PRIME + self.LNS_DESTROY_3_PCT_PRIME):
            num_rooms = 3
        else:
            num_rooms = 4
        logging.info("Randomly generated %g, destroy %d rooms" %(a, num_rooms))
         
        self.NUM_ROOM_DESTROYED_PER_ROUND.append(num_rooms) 
        return num_rooms
        
         
    def _selectArbitraryRoom(self):
        # Option 1:  select all rooms
#         return range(0, len(self.EAMS.RL))
        
        NUM_ROOM = len(self.EAMS.RL)
        locls = xrange(0, NUM_ROOM)
        locls = sample(locls, self.LNS_DESTROY_MAX_ROOMS)        
        num_l = len(locls)
        logging.info("Destroying meeting schedule in ( <%d> locations %s )" %(num_l, locls))
          
        return locls
        
        
    def _calcRoomDestroyDist(self):    
        self.LNS_DESTROY_2_PCT_PRIME = self.LNS_DESTROY_2_PCT / (self.LNS_DESTROY_2_PCT + self.LNS_DESTROY_3_PCT + self.LNS_DESTROY_4_PCT)
        self.LNS_DESTROY_3_PCT_PRIME = self.LNS_DESTROY_3_PCT / (self.LNS_DESTROY_2_PCT + self.LNS_DESTROY_3_PCT + self.LNS_DESTROY_4_PCT)
    
    
        
        
        
#===========================================================================
# Diagnose
#=========================================================================== 
    def _log_ObjValue_Neighbourhood(self, logtime, objvalue, nt):
        data = [logtime, objvalue, nt]
        try:
            fstr = 'Output/' + self.CASECFG + '_' + str(self.CURR_K) + '_LNS_trace'
            f = open(fstr,'a')
            f.write(",".join(map(str, data)))            
            f.write("\n")
            f.close()    
        except (ValueError), e:
            logging.critical('%s' % (e))    
            
            
    
        
        
            
            
            