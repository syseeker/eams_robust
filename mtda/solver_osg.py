import json
import logging
import numpy as np
from datetime import timedelta, datetime

from eams_error import EAMS_Error
from eams_sche_master import Sche_Master
from eams_meeting_generator import Meeting_Generator
from solver_milp import Solver_MILP
from solver_lns import Solver_LNS
from plot_asatsaqe import plotMultiRooms


class Solver_OS_Greedy:
    def __init__(self, EAMS, fn, runcfg, casecfg, lns_limit, mip_limit, update_interval, lns_seed, mode='DEF', slack=0, delta=0, probguar=0):
        self.EAMS = EAMS
        self.GUROBI_LOGFILE = fn
        self.RUNCFG = runcfg
        self.CASECFG = casecfg
        self.LNS_TIME_LIMIT = lns_limit
        self.MIP_TIME_LIMIT = mip_limit
        self.ONLINE_UPDATE_INTERVAL = update_interval
        self.LNS_SEED = lns_seed
        
        self.OSG_LOG_RESULT = 0
        
        self.OSG_LOG_WARMSTART = 1
        self.OSG_LOG_WARMSTART_ORACLE = 0
        self.OSG_LOG_TEMPERATURE = 1
#         if "cvs1440" in runcfg:             # TODO: hardcode to log warmstart when cvs is 1440s
#             self.OSG_LOG_WARMSTART = 0
        
        self.DYNBOUND_MODE = mode            
        self.DYNBOUND_FIXED_SLACK = slack
        self.DYNBOUND_DELTA = delta
        self.DYNBOUND_PROBGUAR = probguar
        if mode is not 'DEF':            
            logging.info("Set mode to %s, slack to %s, delta to %s, prob_guarantee to %s" %(self.DYNBOUND_MODE, self.DYNBOUND_FIXED_SLACK, self.DYNBOUND_DELTA, self.DYNBOUND_PROBGUAR))
            
        
#==================================================================
#   Initialization
#==================================================================
    def _initialize(self):
        self._init_master_schedule()
        self._init_meeting_generator()
        self.CURRENT_SCHEDULING_CLOCK = self.EAMS.SCHEDULING_START_DATETIME        
     
    def _init_master_schedule(self):
        self.SCHE_MASTER = Sche_Master(self.EAMS.ML,
                                       self.EAMS.TS, 
                                        self.EAMS.SH,
                                        self.EAMS.RL, 
                                        self.EAMS.STANDBY_MODE)
                
    def _init_meeting_generator(self):
        self._MEETING_GEN = Meeting_Generator(self.EAMS.ML,
                                              self.ONLINE_UPDATE_INTERVAL)

    def _continue_schedule(self):
        if self.CURRENT_SCHEDULING_CLOCK < self.EAMS.SCHEDULING_END_DATETIME:
            self.CURRENT_SCHEDULING_CLOCK = self.CURRENT_SCHEDULING_CLOCK + timedelta(minutes=self.ONLINE_UPDATE_INTERVAL)
            return True
        else:
            return False
      
    
#==================================================================
#   Internal Func
#================================================================== 
    def _get_mtype(self, M):
        mtype_key = []
        mtype = []
        mtype_mid = {}
        for i in xrange(len(M)):
            idx = M[i].MType
            if idx not in mtype_key:
                mtype_key.append(idx)
                mtype.append(self._MEETING_GEN.MTYPE[idx])
                mtype_mid[idx] =  [M[i].ID]
            else:
                mtype_mid[idx].append(M[i].ID)
            
        return [mtype_key, mtype, mtype_mid] 
    
    def _get_cmt(self, MTYPE_ID, MTYPE):
        #TODO: also need to get cmt for meetings which has been scheduled earlier.
        
        logging.debug("Get list of meeting type with conflict attendee for current set of mtype")
        logging.debug("current MTYPE_ID: %s" %(MTYPE_ID))
        attendees = []
        conflict_mtype = []
        
        for i in xrange(len(MTYPE)):
            attendees.extend(MTYPE[i].MCA)
        logging.debug("conflict attendee: %s" %attendees)
        
        uniq_attendees = set()
        for x in attendees:
            if not x in uniq_attendees:
                uniq_attendees.add(x)
        logging.debug("unique conflict attendee: %s" %uniq_attendees)
        
        uniq_attendees = list(uniq_attendees)
        for i in xrange(len(uniq_attendees)):
            attendee_id = uniq_attendees[i]
            conflict_mtype_by_attendee = self._MEETING_GEN.CMT.get(attendee_id)
            if conflict_mtype_by_attendee not in conflict_mtype:
                conflict_mtype.append(conflict_mtype_by_attendee)
        logging.debug("conflict mtype: %s" %conflict_mtype)
        
        uniq_conflict_mtype = []
        for x in conflict_mtype:
            mt = list(set(x).intersection(set(MTYPE_ID)))
            if mt not in uniq_conflict_mtype:
                uniq_conflict_mtype.append(mt)            
        logging.debug("uniq_conflict_mtype (mtype which exists in CURR_MTYPE_ID only): %s" %(uniq_conflict_mtype))
        
        return [conflict_mtype, uniq_conflict_mtype]
        
        
    def _get_occupied_K_by_conflict_meetings(self, CMT, mtype_ls):
        """All K that has been occupied by conflicted meetings should be excluded in the model"""
        logging.debug("Get occupied K....")
        occupied_dict = {}
        for mt in xrange(len(mtype_ls)):
            mtype_id = mtype_ls[mt]
            conflict_m = []
            mt_occupied_k = []
            for i in xrange(len(CMT)):
                logging.debug("mtype_id: %d  vs  CMT[%d]: %s" %(mtype_id, i, CMT[i]))
                if mtype_id in CMT[i]:                         # Get conflict meeting types of mtype_id
                    for j in xrange(len(CMT[i])):
                        conflict_mtype_id = CMT[i][j]          # Get meeting ID under all conflict mtype (Note: this includes meetings of the given mtype_id)
                        mls = self._MEETING_GEN.MTYPE[conflict_mtype_id].MLS
                        logging.debug("conflict_mtype_id: %s, MLS: %s" %(conflict_mtype_id, mls))
                        conflict_m = set(conflict_m).union(mls)
                        logging.debug("conflict_m: %s" %(conflict_m))
                        
            logging.debug("final conflict_m: %s" %(conflict_m))
            conflict_m = list(conflict_m)
            for i in xrange(len(conflict_m)):
                mid = conflict_m[i]
                lk = self.SCHE_MASTER.MSTR_BDV_x_MLK_MeetingMap.get(mid) 
                if lk is not None:   # If conflict_m[i]  has been scheduled
                    occupied_slots = range(lk[1], (lk[1]+self.EAMS.ML[mid].Duration))  # Get starting slot[1] only, no need location[0]
                    mt_occupied_k.extend(occupied_slots)
                    logging.debug("meeting %d has occupied [%s]" %(mid, occupied_slots))

            if len(mt_occupied_k)>0:
                occupied_dict[mtype_id] = mt_occupied_k
            
        for k,v in occupied_dict.iteritems():
            logging.debug("mtype_id %d should not occupied k: %s" %(k,v))
                    
        return occupied_dict
        

#==================================================================
#   Main loop
#================================================================== 
    def init_room_temperature(self):
        solver = Solver_MILP(self.SCHE_MASTER,
                             self.EAMS,
                             self.GUROBI_LOGFILE,
                             0,
                             [[],[],[]],
                             [],
                             None,
                             self.CASECFG,
                             0,
                             -1,
                             0)
        ret = solver.solve()
        if ret == EAMS_Error().eams_infeasible(): 
            if self.OSG_LOG_RESULT:
                self.logCaseEnergy(0, '*')
            print "initial model infeasible"
        else:
            if self.OSG_LOG_RESULT:
                self.SCHE_MASTER.calcEnergyConsumption(self.EAMS.SCHEDULING_INTERVAL)
                self.logCaseEnergy(0, 
                                   str(round(np.sum(self.SCHE_MASTER.MSTR_power),2)),
                                   str(round(np.sum(self.SCHE_MASTER.MSTR_energy_kWh),2)),
                                   0,
                                   0
                                   )
                logging.info("MSTR_CAV_T_LK: %s" %self.SCHE_MASTER.MSTR_CAV_T_LK)
                logging.info("MSTR_CDV_T_SA_LK: %s" %self.SCHE_MASTER.MSTR_CDV_T_SA_LK)
                logging.info("MSTR_CDV_A_SA_LK: %s" %self.SCHE_MASTER.MSTR_CDV_A_SA_LK)
            
            
    def run(self):        
        is_infea = 0        
        logging.info("\n\n\n===============================================================")
        logging.info("Online Scheduling Start...")
        logging.info("===============================================================")   
        case_start_time = datetime.now()   
        self._initialize()
         
        # Initialize room temperature (assume no meeting)
        self.ck = '_init'  
        self.init_room_temperature()
                 
        # Start scheduling
        while True:
            # get a list of recently arrived meetings
            CURR_M = self._MEETING_GEN.get_meetings(self.CURRENT_SCHEDULING_CLOCK)
            if CURR_M == None:
                if not self._continue_schedule():
                    break
                else:
                    continue
            else:
                logging.info("======================================================")
                logging.info("Scheduling for %s " %(self.CURRENT_SCHEDULING_CLOCK))
                logging.info("======================================================")
                 
                start_time = datetime.now()
                delta = self._MEETING_GEN._roundUpNearestInterval(self.CURRENT_SCHEDULING_CLOCK.minute, self.EAMS.SCHEDULING_INTERVAL) - self.CURRENT_SCHEDULING_CLOCK.minute
                curr_timeslot = self.CURRENT_SCHEDULING_CLOCK + timedelta(minutes=delta)
                curr_k = self.EAMS.TSC.getTimeSlotIdxByDatetime(curr_timeslot)
                logging.info("curr k time: %s [%d]" %(curr_timeslot, curr_k))
                self.ck = curr_k
                                   
                logging.info("CURR_M: %s" %CURR_M)
                [CURR_MTYPE_ID, CURR_MTYPE, CURR_MTYPE_MID] = self._get_mtype(CURR_M)
                logging.info("CURR_MTYPE_ID: %s" %CURR_MTYPE_ID)
                logging.info("CURR_MTYPE: %s" %CURR_MTYPE)
                logging.info("CURR_MTYPE_MID: %s" %CURR_MTYPE_MID)
                   
                [CURR_CMT, CURR_UNIQ_CMT] = self._get_cmt(CURR_MTYPE_ID, CURR_MTYPE)
                logging.info("CURR_CMT: %s" %CURR_CMT)
                logging.info("CURR_UNIQ_CMT: %s" %CURR_UNIQ_CMT)    
                  
                CURR_OCCUPIED_K = self._get_occupied_K_by_conflict_meetings(CURR_CMT, CURR_MTYPE_ID)
                                  
                solver = Solver_LNS(self.SCHE_MASTER,
                                     self.EAMS,
                                     self.GUROBI_LOGFILE,
                                     self.LNS_TIME_LIMIT,
                                     self.MIP_TIME_LIMIT,
                                     curr_k,
                                     [CURR_MTYPE_ID, CURR_MTYPE, CURR_MTYPE_MID],
                                     CURR_UNIQ_CMT,
                                     CURR_OCCUPIED_K,
                                     self.CASECFG,
                                     self.LNS_SEED,
                                     self.DYNBOUND_MODE,
                                     self.DYNBOUND_FIXED_SLACK,
                                     self.DYNBOUND_DELTA,
                                     self.DYNBOUND_PROBGUAR
                                     )
                ret = solver.run()
                run_time = ((datetime.now()-start_time).total_seconds())
                logging.info("Current round takes %d s" %(run_time))
                if ret == EAMS_Error().eams_infeasible():
                    is_infea = 1
                    if self.OSG_LOG_RESULT:
                        self.logCaseEnergy(curr_k, '*', '*', '*', '*')
                    break
                else:
                    if self.OSG_LOG_RESULT:
                        self.logAlloc(0)
                        self.SCHE_MASTER.calcEnergyConsumption(self.EAMS.SCHEDULING_INTERVAL)
                        self.SCHE_MASTER.calcThermalComfortViolation(float(self.EAMS.TEMPERATURE_UNOCC_MIN) + float(self.EAMS.TEMPERATURE_OCC_COMFORT_RANGE_INCR),
                                                             float(self.EAMS.TEMPERATURE_UNOCC_MAX) - float(self.EAMS.TEMPERATURE_OCC_COMFORT_RANGE_DECR))
                        self.logCaseEnergy(curr_k, 
                                   str(round(np.sum(self.SCHE_MASTER.MSTR_power),2)),
                                   str(round(np.sum(self.SCHE_MASTER.MSTR_energy_kWh),2)),
                                   str(round(self.SCHE_MASTER.MSTR_max_comfort_violation,2)),
                                   str(round(self.SCHE_MASTER.MSTR_comfort_violation,2))
                                   )                    
                        self.SCHE_MASTER.diagnose()
 
            if not self._continue_schedule():
                break
         
        case_run_time = ((datetime.now()-case_start_time).total_seconds())
        logging.info("Total run takes %d s" %(case_run_time))
                             
        if is_infea:
            if self.DYNBOUND_MODE is not 'DEF':
                self.logResults(self.CASECFG, '*', '*','*', '*', case_run_time, self.DYNBOUND_FIXED_SLACK, self.DYNBOUND_DELTA, self.DYNBOUND_PROBGUAR)
            else:
                self.logResults(self.CASECFG, '*', '*','*', '*', case_run_time)
             
            if self.OSG_LOG_WARMSTART:
                self._log_for_warmstart(0)
                self._log_infea_currk(self.CASECFG, curr_k)
                
            if self.OSG_LOG_TEMPERATURE:
                self._log_temperature(0)
                 
        else:
            self.logAlloc(0)  # To write to separate file, set to logAlloc(1)
            self.SCHE_MASTER.calcEnergyConsumption(self.EAMS.SCHEDULING_INTERVAL)
            self.SCHE_MASTER.calcThermalComfortViolation(float(self.EAMS.TEMPERATURE_UNOCC_MIN) + float(self.EAMS.TEMPERATURE_OCC_COMFORT_RANGE_INCR),
                                                         float(self.EAMS.TEMPERATURE_UNOCC_MAX) - float(self.EAMS.TEMPERATURE_OCC_COMFORT_RANGE_DECR))
             
            if self.DYNBOUND_MODE is not 'DEF':
                self.logResults(self.CASECFG, 
                            str(round(np.sum(self.SCHE_MASTER.MSTR_power),2)), 
                            str(round(np.sum(self.SCHE_MASTER.MSTR_energy_kWh),2)),
                            str(round(self.SCHE_MASTER.MSTR_max_comfort_violation,2)),
                            str(round(self.SCHE_MASTER.MSTR_comfort_violation,2)),
                            case_run_time,
                            self.DYNBOUND_FIXED_SLACK,
                            self.DYNBOUND_DELTA,
                            self.DYNBOUND_PROBGUAR                            
                            )
            else:
                self.logResults(self.CASECFG, 
                            str(round(np.sum(self.SCHE_MASTER.MSTR_power),2)), 
                            str(round(np.sum(self.SCHE_MASTER.MSTR_energy_kWh),2)),
                            str(round(self.SCHE_MASTER.MSTR_max_comfort_violation,2)),
                            str(round(self.SCHE_MASTER.MSTR_comfort_violation,2)),
                            case_run_time
                            )            
            self.SCHE_MASTER.diagnose()
             
            if self.OSG_LOG_WARMSTART:
                self._log_for_warmstart(1)
                self._log_infea_currk(self.CASECFG, '*')
                
            if self.OSG_LOG_TEMPERATURE:
                self._log_temperature()
             
         

#==================================================================
#   Results Logging
#==================================================================      
    def _log_temperature(self, mode=1):
        """populate temperature data  (m,l,k): (xi_lb, t, xi_ub)}"""
        
        data = {}
        try:    
            if mode:
                for key, m in self.SCHE_MASTER.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse.iteritems():      # MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse: {(2, 403): 1
                    #                     if self.DYNBOUND_MODE is not 'DEF':                    
#                         t_slack_lb = self.SCHE_MASTER.MSTR_CAV_T_SLACK_LB.get(key)
#                         t_slack_ub = self.SCHE_MASTER.MSTR_CAV_T_SLACK_UB.get(key)
#                     else:
#                         t_slack_lb = 0
#                         t_slack_ub = 0
                    [l, k] = key
                    t = self.SCHE_MASTER.MSTR_CAV_T_LK[l][k]
#                     data[tuple([m,l,k])] = tuple([t_slack_lb, t, t_slack_ub])
                    data[tuple([m,l,k])] = t
            
            fstr = 'Output/' + self.RUNCFG + "_temperature"
            f = open(fstr,'a')
            if mode:
                json.dump({str(k): v for k, v in data.iteritems()}, f)
            else:
                json.dump("*", f)
            f.write("\n")
            f.close()    
            
        except (ValueError), e:
            logging.critical('%s' % (e))    
  
    def _log_for_warmstart(self, mode=1):
        try:
            if self.OSG_LOG_WARMSTART_ORACLE:
                case_name = self.RUNCFG.split("_")
                case = case_name[0] + "_" + case_name[1] + "_" + case_name[2] + "_cvsf_" + case_name[4] + "_" + case_name[5] + "_" + case_name[6]
            else:
                case = self.RUNCFG  
            
            fstr = 'Input/Warmstart/' + case
            f = open(fstr,'a')            
            if mode:
                json.dump(self.SCHE_MASTER.MSTR_BDV_x_MLK_MeetingMap, f)
            else:
                json.dump("*", f)
            f.write("\n")
            f.close()    
        except (ValueError), e:
            logging.critical('%s' % (e))    
            
    def _log_infea_currk(self, case, curr_k):
        data = [case, curr_k]        
        try:
            fstr = 'Input/Warmstart/' + self.RUNCFG + "_Infea_K"
            f = open(fstr,'a')
            f.write(",".join(map(str, data)))            
            f.write("\n")
            f.close()    
        except (ValueError), e:
            logging.critical('%s' % (e)) 
        
    
    def logResults(self, case, power, energy, max_thermal_violation, thermal_violation, case_run_time, t_slack=0, slack_bound=0, prob_guar=0):
        if self.DYNBOUND_MODE is not 'DEF':
            data = [case, power, energy, max_thermal_violation,  thermal_violation, case_run_time, t_slack, slack_bound, prob_guar]
        else:
            data = [case, power, energy, max_thermal_violation, thermal_violation, case_run_time]
        try:
            fstr = 'Output/' + self.RUNCFG + "_" + self.DYNBOUND_MODE
            f = open(fstr,'a')
            f.write(",".join(map(str, data)))            
            f.write("\n")
            f.close()    
        except (ValueError), e:
            logging.critical('%s' % (e))   
            
    def logCaseEnergy(self, k, power, energy, max_thermal_violation, thermal_violation):
        data = [k, power, energy, max_thermal_violation, thermal_violation]
        try:
            fstr = 'Output/run_energy_' + self.CASECFG
            f = open(fstr,'a')
            f.write(",".join(map(str, data)))            
            f.write("\n")
            f.close()    
        except (ValueError), e:
            logging.critical('%s' % (e))   
            
    def logAlloc(self, mode):
        data = self.SCHE_MASTER.MSTR_BDV_x_MLK_MeetingMap
        tbl = {}
        key = []
        for k, v in data.iteritems():
            slot = v[1]
            loc = v[0]
            if slot not in key:
                key.append(slot)
                tbl[slot] = {}
                for i in xrange(len(self.EAMS.RL)):
                    tbl[slot][i] = '*'
                    
            sub_tbl = tbl.pop(slot)
            sub_tbl.pop(loc)
            sub_tbl[loc] = k
            tbl[slot] = sub_tbl
        sortedkey = sorted(key)
        
        print_tbl = []
        for i in xrange(len(sortedkey)):
            s = sortedkey[i]
            sub_tbl = tbl.get(s)
            alloc = []
            for j in xrange(4):
                mid = sub_tbl.get(j)
                if mid is None:
                    alloc.append("*")
                else:
                    alloc.append(mid)
            print_tbl.append(alloc)
        transpose_tbl = np.transpose(print_tbl)
             
        logging.info("%s" %("l " + " ".join(map(str, sortedkey))))
        for i in xrange(len(transpose_tbl)):
            logging.info("%s" %(str(i) + " " + " ".join(map(str, transpose_tbl[i]))))
        
        if mode == 1:
            try:
                fstr = 'Output/run_alloc_' + self.RUNCFG
                f = open(fstr,'a')
                
                f.write(self.CASECFG)
                f.write("\n")
                dstr = " ".join(map(str, sortedkey))
                a = ["l", dstr]
                f.write(" ".join(map(str, a)))
                f.write("\n")
                for i in xrange(len(transpose_tbl)):
                    dstr = " ".join(map(str, transpose_tbl[i]))
                    a = [i, dstr]
                    f.write(" ".join(map(str, a)))
                    f.write("\n")
                f.write("\n")
                f.close()  
            except (ValueError), e:
                logging.critical('%s' % (e))   

                
            
            
#==================================================================
#   Graph
#==================================================================    
    def plotGraph(self):
        # Trigger energy calculation only to plot graph
        self.SCHE_MASTER.calcEnergyConsumption(self.EAMS.SCHEDULING_INTERVAL)
        self.SCHE_MASTER.calcHeatGain(self.EAMS)
        
        self.NOTE = self.CASECFG 
        self.FNAME = self.CASECFG + "_" + str(self.ck)
        
        fdir = "Output/"
        fname = self.FNAME
        self.pinterval = 2
        self.pstep = 1
        
        pslot = [v for k,v in self.EAMS.TS.iteritems() if k < len(self.SCHE_MASTER.MSTR_CAV_T_LK[0])]
        ptoa = self.EAMS.OAT.values()[:len(self.SCHE_MASTER.MSTR_CAV_T_LK[0])]
                                
        arr_total = []        
        arr_tsa = []
        arr_asa = []
        arr_qp = []
        arr_qs = []
        arr_t = []
        for i in xrange(len(self.SCHE_MASTER.MSTR_CAV_T_LK)):
            arr_t.append(self.SCHE_MASTER.MSTR_CAV_T_LK[i])
            arr_total.append(self.SCHE_MASTER.MSTR_energy_kWh[i])        
            arr_tsa.append(self.SCHE_MASTER.MSTR_CDV_T_SA_LK[i])
            arr_asa.append(self.SCHE_MASTER.MSTR_CDV_A_SA_LK[i])
            arr_qp.append(self.SCHE_MASTER.MSTR_Q_PEOPLE[i])
            arr_qs.append(self.SCHE_MASTER.MSTR_Q_SOLAR[i])
           
        plotMultiRooms(fdir, fname, self.pinterval, self.pstep, pslot, arr_t, arr_tsa, ptoa, arr_asa, arr_qp, arr_qs, arr_total, self.NOTE)
            
            
            
            
            
    
        