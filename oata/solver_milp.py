import copy
import logging
from datetime import datetime
from calendar import monthrange
from eams import EAMS
from eams_error import EAMS_Error
from solver_error import SOLVER_LNS_Error

from gurobipy import *

class Solver_MILP:
    def __init__(self, MSTR_SCHE, EAMS, fn, curr_k, mtype, uniq_cmt, occ_k, case, lns_seed, timelimit, sche_mode):
        self.err = SOLVER_LNS_Error()
        self.MSTR_SCHE = MSTR_SCHE
        self.EAMS = EAMS
        self.GUROBI_LOGFILE = fn
        self.GUROBI_SEED = lns_seed
        self.CASECFG = case
        self.CURR_K = curr_k
        [self.MTYPE_ID, self.MTYPE, self.MTYPE_MID] = mtype
        self.UNIQ_CMT = uniq_cmt
        self.CURR_OCCUPIED_K = occ_k
        
        self.SCHE_MODE = sche_mode
        self.TIME_LIMIT = float(timelimit)
        self.SOLUTION_LIMIT = -1  
                
        self.model = Model('EAMS_'+str(curr_k))
        self._init_constant()
        self._init_gurobi_cfg()
        
        self.LOG_LP = 0
        
#==================================================================
#   Initialization
#==================================================================        
        
    def _init_constant(self):        
        self.NUM_SLOT = len(self.EAMS.TS)-1-(self.CURR_K)
        self.NUM_ROOM = len(self.EAMS.RL)
        self.NUM_MEETING_TYPE = len(self.MTYPE)
        logging.info("******************* #k = %d #r = %d  #mtype = %d" %(self.NUM_SLOT, self.NUM_ROOM, self.NUM_MEETING_TYPE))
        
        if self.CURR_K == 0:
            self.INITIAL_TEMPERATURE = [self.EAMS.INITIAL_TEMPERATURE] * self.NUM_ROOM
            self.INITIAL_CAV_T_l_z1_L = [self.EAMS.INITIAL_TEMPERATURE] * self.NUM_ROOM
            self.INITIAL_CAV_T_l_z2_L = [self.EAMS.INITIAL_TEMPERATURE] * self.NUM_ROOM
            self.INITIAL_CAV_T_l_z3_L = [self.EAMS.INITIAL_TEMPERATURE] * self.NUM_ROOM
            self.INITIAL_CAV_T_l_z4_L = [self.EAMS.INITIAL_TEMPERATURE] * self.NUM_ROOM
            self.INITIAL_CAV_T_l_f_L = [self.EAMS.INITIAL_TEMPERATURE] * self.NUM_ROOM
            self.INITIAL_CAV_T_l_c_L = [self.EAMS.INITIAL_TEMPERATURE] * self.NUM_ROOM
            self.INITIAL_CAV_T_z1_l_L = [self.EAMS.INITIAL_TEMPERATURE] * self.NUM_ROOM
            self.INITIAL_CAV_T_z2_l_L = [self.EAMS.INITIAL_TEMPERATURE] * self.NUM_ROOM
            self.INITIAL_CAV_T_z3_l_L = [self.EAMS.INITIAL_TEMPERATURE] * self.NUM_ROOM
            self.INITIAL_CAV_T_z4_l_L = [self.EAMS.INITIAL_TEMPERATURE] * self.NUM_ROOM
        else:
            self.INITIAL_TEMPERATURE = []
            self.INITIAL_CAV_T_l_z1_L = []
            self.INITIAL_CAV_T_l_z2_L = []
            self.INITIAL_CAV_T_l_z3_L = []
            self.INITIAL_CAV_T_l_z4_L = []
            self.INITIAL_CAV_T_l_f_L = []
            self.INITIAL_CAV_T_l_c_L = []
            self.INITIAL_CAV_T_z1_l_L = []
            self.INITIAL_CAV_T_z2_l_L = []
            self.INITIAL_CAV_T_z3_l_L = []
            self.INITIAL_CAV_T_z4_l_L = []
            for l in xrange(self.NUM_ROOM):
                self.INITIAL_TEMPERATURE.append(self.MSTR_SCHE.MSTR_CAV_T_LK[l][self.CURR_K])
                self.INITIAL_CAV_T_l_z1_L.append(self.MSTR_SCHE.MSTR_CAV_T_l_z1_LK[l][self.CURR_K])
                self.INITIAL_CAV_T_l_z2_L.append(self.MSTR_SCHE.MSTR_CAV_T_l_z2_LK[l][self.CURR_K])
                self.INITIAL_CAV_T_l_z3_L.append(self.MSTR_SCHE.MSTR_CAV_T_l_z3_LK[l][self.CURR_K])
                self.INITIAL_CAV_T_l_z4_L.append(self.MSTR_SCHE.MSTR_CAV_T_l_z4_LK[l][self.CURR_K])
                self.INITIAL_CAV_T_l_f_L.append(self.MSTR_SCHE.MSTR_CAV_T_l_f_LK[l][self.CURR_K])
                self.INITIAL_CAV_T_l_c_L.append(self.MSTR_SCHE.MSTR_CAV_T_l_c_LK[l][self.CURR_K])
                self.INITIAL_CAV_T_z1_l_L.append(self.MSTR_SCHE.MSTR_CAV_T_z1_l_LK[l][self.CURR_K])
                self.INITIAL_CAV_T_z2_l_L.append(self.MSTR_SCHE.MSTR_CAV_T_z2_l_LK[l][self.CURR_K])
                self.INITIAL_CAV_T_z3_l_L.append(self.MSTR_SCHE.MSTR_CAV_T_z3_l_LK[l][self.CURR_K])
                self.INITIAL_CAV_T_z4_l_L.append(self.MSTR_SCHE.MSTR_CAV_T_z4_l_LK[l][self.CURR_K])
                
        logging.info("initial temperature: %s" %(self.INITIAL_TEMPERATURE))
        logging.info("initial CAV_T_l_z1_L: %s" %(self.INITIAL_CAV_T_l_z1_L))
        logging.info("initial CAV_T_l_z2_L: %s" %(self.INITIAL_CAV_T_l_z2_L))
        logging.info("initial CAV_T_l_z3_L: %s" %(self.INITIAL_CAV_T_l_z3_L))
        logging.info("initial CAV_T_l_z4_L: %s" %(self.INITIAL_CAV_T_l_z4_L))
        logging.info("initial CAV_T_l_f_L: %s" %(self.INITIAL_CAV_T_l_f_L))
        logging.info("initial CAV_T_l_c_L: %s" %(self.INITIAL_CAV_T_l_c_L))
        logging.info("initial CAV_T_z2_l_L: %s" %(self.INITIAL_CAV_T_z2_l_L))
        logging.info("initial CAV_T_z3_l_L: %s" %(self.INITIAL_CAV_T_z3_l_L))
        logging.info("initial CAV_T_z4_l_L: %s" %(self.INITIAL_CAV_T_z4_l_L))
        
        self.N_OUTDOOR = 1000        
        self.EPSILON = 1.0e-06
        self.STATUS = ['', 'LOADED', 'OPTIMAL', 'INFEASIBLE', 'INF_OR_UNBD', 'UNBOUNDED', 'CUTOFF', 'ITERATION_LIMIT', 'NODE_LIMIT', 'TIME_LIMIT', 'SOLUTION_LIMIT', 'INTERRUPTED', 'NUMERIC', 'SUBOPTIMAL']
    
    def _init_gurobi_cfg(self):
        self.model.setParam(GRB.param.OutputFlag, 0)
        self.model.setParam(GRB.param.LogFile, self.GUROBI_LOGFILE)
        self.model.setParam(GRB.param.LogToConsole, 0)
        
        self.model.setParam(GRB.Param.Threads, 1)
        self.model.setParam(GRB.Param.FeasibilityTol, 1e-9)        
        self.model.setParam(GRB.Param.IntFeasTol, 1e-9)          
        self.model.setParam(GRB.Param.OptimalityTol, 1e-9)        
        self.model.setParam(GRB.Param.Seed, self.GUROBI_SEED)        
        
        if self.TIME_LIMIT > 0:
            self.model.setParam(GRB.Param.TimeLimit, self.TIME_LIMIT) 
                 
        if self.SOLUTION_LIMIT > 0: 
            self.model.setParam(GRB.Param.SolutionLimit, self.SOLUTION_LIMIT)

#==================================================================
#   Schedule 
#================================================================== 
    def _init_schedule_var(self):                
        self.BDV_x_MLK = []                         # Binary Decision variable: The "Starting" slot of a meeting in Meeting x Location x Time
        self.BDV_w_LK = []                          # Binary Decision variable: represent if HVAC is activated from standby mode at location l at time k
        self.BAV_z_LK = []                          # Binary Auxiliary variable: represent if location l is occupied at time k (do not care which meeting)        
        self.DAV_Attendee_LK = []                   # Discrete Auxiliary variable: Number of attendee at room l at time k
                
        self.BDV_x_MLK_Dict = {}                    # d[(m,l,k)] = offset of (m,l,k) in BDV_x_MLK. Record index of meeting x location x time periods
        self.BDV_x_MLK_ReverseDict = {}             # d[offset of (m,l,k) in BDV_x_MLK] = (m,l,k). Basically to avoid search by value using BDV_x_MLK_Dict
        self.BDV_w_LK_Dict = {}                     # d[(l,k)] = offset of (l,k) in BDV_w_LK. Record index of location x time periods
        self.BDV_w_LK_ReverseDict = {}              # d[offset of (l,k) in BDV_w_MLK] = (l,k). Basically to avoid search by value using BDV_w_LK_Dict
                
        self.CSTR_Schedule_Once_M = []              # Constraint: Every meeting must be scheduled to 1 room exactly at its starting time k
        self.CSTR_Schedule_Once_PreBook_M = []      # Constraint: Add constraint for future meetings which has been preset prior to time k
        self.CSTR_LocationTimeOccupied=[]           # Constraint:     set BAV_z_LK to 1 if at least 1 meeting is held at location l at time k
        self.CSTR_NumAttendee = []                  # Constraint: Number of attendee at room l at time k
        self.CSTR_AttendeeConflict = []             # Constraint: Meeting which has similar attendee should not be allocated at the same timeslot
        
        self.BAV_y_LD = []                          # Binary Decision variable: represent if location l is occupied at day D
        self.CSTR_MinRoom = []                      # Constraint: Force meeting allocation into minimum number of room per day
           
    def _createScheduleModel(self):
        self._init_schedule_var()
        
        self._createBDV_x_MLK_MT()
        self._createBAV_z_LK()
        self._createDAV_Attendee_LK()
        self._createAuxVarSchedule()
        
        self._createCSTR_Schedule_Once_MT()
        self._createCSTR_LocationTimeOccupied_MT()
        self._createCSTR_NumAttendee_MT()
        self._createCSTR_AttendeeConflict_MT()    
       
        
#==================================================================
#   HVAC
#==================================================================  
    def _init_hvac_var(self):
        self.CDV_T_SA_LK = []                       # Continuous Decision variable: Supply air temperature
        self.CDV_A_SA_LK = []                       # Continuous Decision variable: air mass flow rate                
        self.CAV_T_LK = []                          # Continuous Auxiliary variable: Room/Zone temperature        
        self.CAV_A_SA_Room_L = []                   # Continuous Auxiliary variable: Minimum air mass flow rate per location
        self.CAV_A_SA_MaxPeople_L = []              # Continuous Auxiliary variable: Minimum air mass flow rate per occupant required
        self.CAV_A_SA_T_z_LK = []                   # Continuous Auxiliary variable:  aT(SA,z)
        self.CAV_A_SA_T_SA_LK = []                  # Continuous Auxiliary variable:  aT(SA,SA)        
        self.CAV_E_FAN_LK = []                      # Auxiliary variable: Energy consumption of fan operation
        self.CAV_E_CONDITIONING_LK = []             # Auxiliary variable: Energy consumption of conditioning operation
        self.CAV_E_HEATING_LK = []                  # Auxiliary variable: Energy consumption of heating operation        
        self.CAV_T_l_z1_LK = []                     # Continuous Auxiliary variable: wall temperature from zone l to zone z1
        self.CAV_T_l_z2_LK = []                     # Continuous Auxiliary variable: wall temperature from zone l to zone z2
        self.CAV_T_l_z3_LK = []                     # Continuous Auxiliary variable: wall temperature from zone l to zone z3
        self.CAV_T_l_z4_LK = []                     # Continuous Auxiliary variable: wall temperature from zone l to zone z4
        self.CAV_T_l_f_LK  = []                     # Continuous Auxiliary variable: wall temperature from zone l to zone f
        self.CAV_T_l_c_LK  = []                     # Continuous Auxiliary variable: wall temperature from zone l to zone c 
        self.CAV_T_z1_l_LK = []                     # Continuous Auxiliary variable: wall temperature from zone z1 to zone l
        self.CAV_T_z2_l_LK = []                     # Continuous Auxiliary variable: wall temperature from zone z2 to zone l
        self.CAV_T_z3_l_LK = []                     # Continuous Auxiliary variable: wall temperature from zone z3 to zone l
        self.CAV_T_z4_l_LK = []                     # Continuous Auxiliary variable: wall temperature from zone z4 to zone l  
        
        self.CSTR_T_SA_LK = []                      # Constraint:     T_CA*BAV_L <= T_SA <= T_SA_HIGH
        self.CSTR_T_LK_lb = []                      # Constraint: lower bound of room temperature
        self.CSTR_T_LK_ub = []                      # Constraint: upper bound of room temperature
        self.CSTR_T_LK = []                         # Constraint: Equation of room/zone temperature
        self.CSTR_T_l_z1_LK = []                    # Constraint: Equation of wall temperature from l to z1  
        self.CSTR_T_l_z2_LK = []                    # Constraint: Equation of wall temperature from l to z2
        self.CSTR_T_l_z3_LK = []                    # Constraint: Equation of wall temperature from l to z3
        self.CSTR_T_l_z4_LK = []                    # Constraint: Equation of wall temperature from l to z4
        self.CSTR_T_l_f_LK = []                     # Constraint: Equation of wall temperature from l to f
        self.CSTR_T_l_c_LK = []                     # Constraint: Equation of wall temperature from l to c
        self.CSTR_T_z1_l_LK = []                    # Constraint: Equation of wall temperature from z1 to l  
        self.CSTR_T_z2_l_LK = []                    # Constraint: Equation of wall temperature from z2 to l
        self.CSTR_T_z3_l_LK = []                    # Constraint: Equation of wall temperature from z3 to l
        self.CSTR_T_z4_l_LK = []                    # Constraint: Equation of wall temperature from z4 to l

        self.CSTR_A_SA_LB_LK = []                   # Constraint: lower bound of air mass flow rate
        self.CSTR_A_SA_UB_LK = []                   # Constraint: upper bound of air mass flow rate
        self.CSTR_T_SA_LB_LK = []                   # Constraint: lower bound of T_SA
        self.CSTR_T_SA_UB_LK = []                   # Constraint: upper bound of T_SA

        self.CSTR_A_SA_T_z_1_LK = []                # Constraint: MacCormick relaxation for A_SA x T
        self.CSTR_A_SA_T_z_2_LK = []                # Constraint: MacCormick relaxation for A_SA x T
        self.CSTR_A_SA_T_z_3_LK = []                # Constraint: MacCormick relaxation for A_SA x T
        self.CSTR_A_SA_T_z_4_LK = []                # Constraint: MacCormick relaxation for A_SA x T
                
        self.CSTR_A_SA_T_SA_1_LK = []                 # Constraint: MacCormick relaxation for A_SA x T_SA
        self.CSTR_A_SA_T_SA_2_LK = []                 # Constraint: MacCormick relaxation for A_SA x T_SA
        self.CSTR_A_SA_T_SA_3_LK = []                 # Constraint: MacCormick relaxation for A_SA x T_SA
        self.CSTR_A_SA_T_SA_4_LK = []                 # Constraint: MacCormick relaxation for A_SA x T_SA
        
        self.CSTR_E_FAN_LK = []                     # Constraint: Equation of energy consumption of fan operation
        self.CSTR_E_CONDITIONING_LK = []            # Constraint: Equation of energy consumption of air-conditioning operation
        self.CSTR_E_HEATING_LK = []                 # Constraint: Equation of energy consumption of heating operation

       
    def _createHVACModel(self):
        self._init_hvac_var()
                
        self._createCDV_SupplyAirTemperature()
        self._createCDV_AirMassFlowRate()
        self._createCAV_RoomTemperature()
        self._createCAV_T_z1_l()
        self._createCAV_T_z2_l()  
        self._createCAV_T_z3_l()  
        self._createCAV_T_z4_l()  
        self._createCAV_T_l_z1()          
        self._createCAV_T_l_z2()
        self._createCAV_T_l_z3()
        self._createCAV_T_l_z4()
        self._createCAV_T_l_f()
        self._createCAV_T_l_c()
        self._createCAV_A_SA_T_z_LK()
        self._createCAV_A_SA_T_SA_LK()    
        self._createAuxVarHVAC()        # Use for robust optimization
                
        self._createCSTR_RoomTemperature_LB()
        self._createCSTR_RoomTemperature_UB()
        self._createCSTR_RoomTemperature()
        self._createCSTR_T_z1_l()
        self._createCSTR_T_z2_l()  
        self._createCSTR_T_z3_l()  
        self._createCSTR_T_z4_l()  
        self._createCSTR_T_l_z1()          
        self._createCSTR_T_l_z2()
        self._createCSTR_T_l_z3()
        self._createCSTR_T_l_z4()
        self._createCSTR_T_l_f()
        self._createCSTR_T_l_c()
        self._createAuxCstrHVAC()        # Use for robust optimization
#                 
        if self.EAMS.STANDBY_MODE == '0':
            # HVAC mode - options - enable either 1 set
            # option 1: no standby mode. HVAC is OFF after standard working hours
            logging.info("HVAC running on non-standby mode... HVAC is off at night.")
            self._createHVAC_CSTR_noStandbyMode()
        else:
            # option 2: has standby mode. HVAC will be automatically turned on/off after standard working hours.
            logging.info("HVAC running on standby mode... HVAC can be turned on at night.")
            self._createHVAC_CSTR_hasStandbyMode()        
#             
        self._createHVAC_CSTR_Energy()      
        
        
    def _createAuxVarSchedule(self):
        pass
    
    def _createAuxVarHVAC(self):
        pass
    
    def _createAuxCstrHVAC(self):
        pass
    
#--------------------------------------------------------------------------------- 
    def _createHVAC_CSTR_noStandbyMode(self):
        self._createCSTR_SupplyAirTemperature_LB_noStandbyMode()        
        self._createCSTR_SupplyAirFlowRate_LB_noStandbyMode()  
        self._createHVAC_CSTR_A_SA_T_SA_noStandbyMode()
        self._createHVAC_CSTR_A_SA_T_z_with_LooseBoundedT_noStandbyMode()
        
    def _createHVAC_CSTR_A_SA_T_SA_noStandbyMode(self):
        self._createCSTR_A_SA_T_SA_1_LK_noStandbyMode()
        self._createCSTR_A_SA_T_SA_2_LK_noStandbyMode()
        self._createCSTR_A_SA_T_SA_3_LK_noStandbyMode()
        self._createCSTR_A_SA_T_SA_4_LK_noStandbyMode()
        
    def _createHVAC_CSTR_A_SA_T_z_with_LooseBoundedT_noStandbyMode(self):
        self._createCSTR_A_SA_T_z_1_LK_looseboundedT_noStandbyMode()
        self._createCSTR_A_SA_T_z_2_LK_looseboundedT_noStandbyMode()
        self._createCSTR_A_SA_T_z_3_LK_looseboundedT_noStandbyMode()
        self._createCSTR_A_SA_T_z_4_LK_looseboundedT_noStandbyMode()
        
#---------------------------------------------------------------------------------         
    def _createHVAC_CSTR_hasStandbyMode(self):
        self._createBDV_w_LK()
        self._createCSTR_SupplyAirTemperature_LB_hasStandbyMode()
        self._createCSTR_SupplyAirTemperature_UB_hasStandbyMode()
        self._createCSTR_SupplyAirFlowRate_LB_hasStandbyMode()
        self._createCSTR_SupplyAirFlowRate_UB_hasStandbyMode()   
        self._createHVAC_CSTR_A_SA_T_SA_hasStandbyMode()
        self._createHVAC_CSTR_A_SA_T_z_with_LooseBoundedT_hasStandbyMode()     
        
    def _createHVAC_CSTR_A_SA_T_SA_hasStandbyMode(self):
        self._createCSTR_A_SA_T_SA_1_LK_hasStandbyMode()
        self._createCSTR_A_SA_T_SA_2_LK_hasStandbyMode()
        self._createCSTR_A_SA_T_SA_3_LK_hasStandbyMode()
        self._createCSTR_A_SA_T_SA_4_LK_hasStandbyMode()
        
    def _createHVAC_CSTR_A_SA_T_z_with_LooseBoundedT_hasStandbyMode(self):
        self._createCSTR_A_SA_T_z_1_LK_looseboundedT_hasStandbyMode()
        self._createCSTR_A_SA_T_z_2_LK_looseboundedT_hasStandbyMode()
        self._createCSTR_A_SA_T_z_3_LK_looseboundedT_hasStandbyMode()
        self._createCSTR_A_SA_T_z_4_LK_looseboundedT_hasStandbyMode()

#---------------------------------------------------------------------------------         
    def _createHVAC_CSTR_Energy(self):
        self._createCAV_EnergyConsumption_Fan()
        self._createCAV_EnergyConsumption_Conditioning()
        self._createCAV_EnergyConsumption_Heating()
        
        self._createCSTR_EnergyConsumption_Fan()
        self._createCSTR_EnergyConsumption_Conditioning()
        self._createCSTR_EnergyConsumption_Heating()
        
    #===========================================================================
    # Decision Variables
    #===========================================================================
    def _is_LK_available(self, l, k, mdur):
        """if LK has been occupied by other meetings (including those with and without conflicts"""        
        for slot in xrange(k, k+mdur):
            lk = tuple([l,slot])
            if self.MSTR_SCHE.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse.has_key(lk):
                return 0
        return 1
            
    def _is_K_available(self, mtype_id, k):
        """if K has been occupied by conflicted meetings"""
        
        if (self.CURR_OCCUPIED_K is None or 
            self.CURR_OCCUPIED_K.get(mtype_id) is None or
            len(self.CURR_OCCUPIED_K.get(mtype_id))==0):
            return True
        
        if k in self.CURR_OCCUPIED_K.get(mtype_id):
            return False
        else:
            return True
             
    def _createBDV_x_MLK_MT(self):
        """For each meeting type x feasible location x feasible time, create a decision variable  (M x L_m x K_m)"""
        
        for m in xrange(self.NUM_MEETING_TYPE):  
            self.BDV_x_MLK.append([])
                
            if self.SCHE_MODE == 1:
                mtype_id = self.CURR_DESTROY_MTYPE[m]
                offset = self.MTYPE_ID.index(mtype_id)
                mid = self.MTYPE[offset].MLS[0] 
                mdur = self.EAMS.ML[mid].Duration
            else:
                mtype_id = self.MTYPE_ID[m]
                mid = self.MTYPE[m].MLS[0]
                mdur = self.EAMS.ML[mid].Duration
                                
            for l in xrange(self.NUM_ROOM):
                if self.SCHE_MODE == 1:
                    dl = self.CURR_DESTROY_LOCATION[l]
                else:
                    dl = l
                    
                if dl in self.EAMS.MR[mid]:    # TODO: assume all meetings of the same type can access the same room. Re-group required if not!
                    self.BDV_x_MLK[m].append([])  
                    mk = 0                                      
                    for k in xrange(self.NUM_SLOT):
                        if (self.EAMS.isInStartTimeWindows(mid, self.CURR_K+k) > 0 and
                            self._is_K_available(mtype_id, self.CURR_K+k) and
                            self._is_LK_available(dl, self.CURR_K+k, mdur)):
                            logging.debug("M_L_K_%d_%d_%d = in array offset(%d, %d, %d)" %(mtype_id,dl,self.CURR_K+k, m,l,mk))
                            
                            name = ['BDV_x_MLK', str(mtype_id), str(dl), str(self.CURR_K+k)]                            
                            name = '_'.join(name)         
                            self.BDV_x_MLK[m][l].append(self.model.addVar(lb=0.0, ub=1.0, vtype=GRB.BINARY, name=name))                            
                            self.BDV_x_MLK_Dict[tuple([mtype_id,dl,self.CURR_K+k])] = [m,l,mk]   
                            self.BDV_x_MLK_ReverseDict[tuple([m,l,mk])] = [mtype_id,dl,self.CURR_K+k]                         
                            mk = mk+1
                    l = l+1
                
        self.model.update()                           
        logging.debug("BDV_x_MLK:\n %s" %self.BDV_x_MLK)
        logging.debug("BDV_x_MLK_Dict:\n %s" %self.BDV_x_MLK_Dict)
        logging.debug("BDV_x_MLK_ReverseDict:\n %s" %self.BDV_x_MLK_ReverseDict) 
        
    def _createBDV_w_LK(self):
        """For each time k, where k falls on non-standard working hour, create a decision variable  (L x K)"""
        
        for l in xrange(self.NUM_ROOM):
            self.BDV_w_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
            mk = 0
            for k in xrange(self.NUM_SLOT):
                if self.EAMS.SH[self.CURR_K+k] == 0:
                    name = ['BDV_w_LK', str(dl), str(self.CURR_K+k)]
                    name = '_'.join(name)         
                    self.BDV_w_LK[l].append(self.model.addVar(vtype=GRB.BINARY, name=name))
                    self.BDV_w_LK_Dict[tuple([dl,self.CURR_K+k])] = [l,mk]
                    self.BDV_w_LK_ReverseDict[tuple([l,mk])] = [dl,self.CURR_K+k]
                    mk = mk+1
    
        self.model.update()
        logging.debug("BDV_w_LK:\n %s" %self.BDV_w_LK)
        logging.debug("BDV_w_LK_Dict:\n %s" %self.BDV_w_LK_Dict)
        
    def _createCDV_SupplyAirTemperature(self):
        """For each location at each timestep, create a decision variable of TSA, i.e. TSA(k,l)"""
        
        T_SA_UB = self.EAMS.TEMPERATURE_SUPPLY_AIR_HIGH
        for l in xrange(self.NUM_ROOM):
            self.CDV_T_SA_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
            for k in xrange(self.NUM_SLOT):                
                name = ['CDV_T_SA_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)                
                
                self.CDV_T_SA_LK[l].append(self.model.addVar(lb=0, ub=T_SA_UB, vtype=GRB.CONTINUOUS, name=name))
                
        self.model.update()
        logging.debug("CDV_T_SA_LK:\n %s" %self.CDV_T_SA_LK)
        
    def _createCDV_AirMassFlowRate(self):
        """For each location at each timestep, create a decision variable of aSA, i.e. aSA(k,l)"""
        
        A_SA_UB = self.EAMS.MASS_AIR_FLOW_SUPPLY_AIR_MAX
        for l in xrange(self.NUM_ROOM):
            self.CDV_A_SA_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
            for k in xrange(self.NUM_SLOT):                
                name = ['CDV_A_SA_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)                
                
                self.CDV_A_SA_LK[l].append(self.model.addVar(lb=0, ub=A_SA_UB, vtype=GRB.CONTINUOUS, name=name))
                
        self.model.update()
        logging.debug("CDV_A_SA_LK:\n %s" %self.CDV_A_SA_LK)
            
    
    #===========================================================================
    # Auxiliary Variables
    #===========================================================================
    
    #===========================================================================
    # Auxiliary Variables: Room Alloc
    #===========================================================================   
    def _createBAV_z_LK(self):
        """For each location at timeslot k, create an auxiliary variable"""
        
        for l in xrange(self.NUM_ROOM):
            self.BAV_z_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l            
            for k in xrange(self.NUM_SLOT):
                name = ['BAV_z_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)         
                self.BAV_z_LK[l].append(self.model.addVar(lb=0, ub=1, vtype=GRB.CONTINUOUS, name=name))
             
        self.model.update()
        logging.debug("BAV_z_LK:\n %s" %self.BAV_z_LK)
         
    def _createDAV_Attendee_LK(self):
        """For each location at each timestamp, create an auxiliary variable representing number of attendee"""
         
        for l in xrange(self.NUM_ROOM):
            self.DAV_Attendee_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l             
            for k in xrange(self.NUM_SLOT):
                name = ['DAV_Attendee_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)         
                self.DAV_Attendee_LK[l].append(self.model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=name))                 
        self.model.update()
        logging.debug("DAV_Attendee_LK:\n %s" %self.DAV_Attendee_LK)
        
    #===========================================================================
    # Auxiliary Variables: HVAC
    #===========================================================================
    
    def _createCAV_RoomTemperature(self):
        """For each location at each timestep, create an auxiliary variable of room temperature T(k, l)"""
        for l in xrange(self.NUM_ROOM):
            self.CAV_T_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l 
            for k in xrange(self.NUM_SLOT):
                name = ['CAV_T_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)         
                
                self.CAV_T_LK[l].append(self.model.addVar(vtype=GRB.CONTINUOUS, name=name))
                
        self.model.update()
        logging.debug("CAV_T_LK:\n %s" %self.CAV_T_LK)
        
    def _createCAV_T_z1_l(self):
        for l in xrange(self.NUM_ROOM):
            self.CAV_T_z1_l_LK.append([])  
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l          
            if self.EAMS.RNL[dl][0] == self.N_OUTDOOR:
                for k in xrange(self.NUM_SLOT):
                    name = ['CAV_T_z1_l_LK', str(dl), str(self.CURR_K+k)]                
                    name = '_'.join(name)   
                    self.CAV_T_z1_l_LK[l].append(self.model.addVar(vtype=GRB.CONTINUOUS, name=name))
                
        self.model.update()
        logging.debug("CAV_T_z1_l_LK:\n %s" %self.CAV_T_z1_l_LK)
        
    def _createCAV_T_z2_l(self):
        for l in xrange(self.NUM_ROOM):
            self.CAV_T_z2_l_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l              
            if self.EAMS.RNL[dl][1] == self.N_OUTDOOR:
                for k in xrange(self.NUM_SLOT):
                    name = ['CAV_T_z2_l_LK', str(dl), str(self.CURR_K+k)]
                    name = '_'.join(name)   
                    self.CAV_T_z2_l_LK[l].append(self.model.addVar(vtype=GRB.CONTINUOUS, name=name))
                
        self.model.update()
        logging.debug("CAV_T_z2_l_LK:\n %s" %self.CAV_T_z2_l_LK)
        
    def _createCAV_T_z3_l(self):
        for l in xrange(self.NUM_ROOM):
            self.CAV_T_z3_l_LK.append([])   
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l           
            if self.EAMS.RNL[dl][2] == self.N_OUTDOOR:
                for k in xrange(self.NUM_SLOT):
                    name = ['CAV_T_z3_l_LK', str(dl), str(self.CURR_K+k)]
                    name = '_'.join(name)                            
                    self.CAV_T_z3_l_LK[l].append(self.model.addVar(vtype=GRB.CONTINUOUS, name=name))
                
        self.model.update()
        logging.debug("CAV_T_z3_l_LK:\n %s" %self.CAV_T_z3_l_LK)
        
    def _createCAV_T_z4_l(self):
        for l in xrange(self.NUM_ROOM):
            self.CAV_T_z4_l_LK.append([])    
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l          
            if self.EAMS.RNL[dl][3] == self.N_OUTDOOR:
                for k in xrange(self.NUM_SLOT):
                    name = ['CAV_T_z4_l_LK', str(dl), str(self.CURR_K+k)]
                    name = '_'.join(name)  
                    self.CAV_T_z4_l_LK[l].append(self.model.addVar(vtype=GRB.CONTINUOUS, name=name))
                
        self.model.update()
        logging.debug("CAV_T_z4_l_LK:\n %s" %self.CAV_T_z4_l_LK)
        
    def _createCAV_T_l_z1(self):
        for l in xrange(self.NUM_ROOM):
            self.CAV_T_l_z1_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l  
            if self.EAMS.RNL[dl][0] == self.N_OUTDOOR:
                for k in xrange(self.NUM_SLOT):
                    name = ['CAV_T_l_z1_LK', str(dl), str(self.CURR_K+k)]                
                    name = '_'.join(name)       
                    self.CAV_T_l_z1_LK[l].append(self.model.addVar(vtype=GRB.CONTINUOUS, name=name))
                
        self.model.update()
        logging.debug("CAV_T_l_z1_LK:\n %s" %self.CAV_T_l_z1_LK)
        
    def _createCAV_T_l_z2(self):
        for l in xrange(self.NUM_ROOM):
            self.CAV_T_l_z2_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l  
            if self.EAMS.RNL[dl][1] == self.N_OUTDOOR:
                for k in xrange(self.NUM_SLOT):
                    name = ['CAV_T_l_z2_LK', str(dl), str(self.CURR_K+k)]
                    name = '_'.join(name)
                    self.CAV_T_l_z2_LK[l].append(self.model.addVar(vtype=GRB.CONTINUOUS, name=name))
                
        self.model.update()
        logging.debug("CAV_T_l_z2_LK:\n %s" %self.CAV_T_l_z2_LK)
        
    def _createCAV_T_l_z3(self):
        for l in xrange(self.NUM_ROOM):
            self.CAV_T_l_z3_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l  
            if self.EAMS.RNL[dl][2] == self.N_OUTDOOR:
                for k in xrange(self.NUM_SLOT):
                    name = ['CAV_T_l_z3_LK', str(dl), str(self.CURR_K+k)]
                    name = '_'.join(name)
                    self.CAV_T_l_z3_LK[l].append(self.model.addVar(vtype=GRB.CONTINUOUS, name=name))
                
        self.model.update()
        logging.debug("CAV_T_l_z3_LK:\n %s" %self.CAV_T_l_z3_LK)
        
    def _createCAV_T_l_z4(self):
        for l in xrange(self.NUM_ROOM):
            self.CAV_T_l_z4_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l  
            if self.EAMS.RNL[dl][3] == self.N_OUTDOOR:
                for k in xrange(self.NUM_SLOT):
                    name = ['CAV_T_l_z4_LK', str(dl), str(self.CURR_K+k)]
                    name = '_'.join(name)
                    self.CAV_T_l_z4_LK[l].append(self.model.addVar(vtype=GRB.CONTINUOUS, name=name))
                
        self.model.update()
        logging.debug("CAV_T_l_z4_LK:\n %s" %self.CAV_T_l_z4_LK)
        
    def _createCAV_T_l_f(self):
        for l in xrange(self.NUM_ROOM):
            self.CAV_T_l_f_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l  
            for k in xrange(self.NUM_SLOT):
                name = ['CAV_T_l_f_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name) 
                self.CAV_T_l_f_LK[l].append(self.model.addVar(vtype=GRB.CONTINUOUS, name=name))
                
        self.model.update()
        logging.debug("CAV_T_l_f_LK:\n %s" %self.CAV_T_l_f_LK)
        
    def _createCAV_T_l_c(self):
        for l in xrange(self.NUM_ROOM):
            self.CAV_T_l_c_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l  
            for k in xrange(self.NUM_SLOT):
                name = ['CAV_T_l_c_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)         
                
                self.CAV_T_l_c_LK[l].append(self.model.addVar(vtype=GRB.CONTINUOUS, name=name))
                
        self.model.update()
        logging.debug("CAV_T_l_c_LK:\n %s" %self.CAV_T_l_c_LK)
        
    def _createCAV_A_SA_T_z_LK(self):
        """For each location at each timestep, create an auxiliary variable of aT(SA, z)"""
        for l in xrange(self.NUM_ROOM):
            self.CAV_A_SA_T_z_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l  
            for k in xrange(self.NUM_SLOT):
                name = ['CAV_A_SA_T_z_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)  
                self.CAV_A_SA_T_z_LK[l].append(self.model.addVar(vtype=GRB.CONTINUOUS, name=name))
                
        self.model.update()
        logging.debug("CAV_A_SA_T_z_LK:\n %s" %self.CAV_A_SA_T_z_LK)
        
    def _createCAV_A_SA_T_SA_LK(self):
        """For each location at each timestep, create an auxiliary variable of aT(SA, SA)"""
        for l in xrange(self.NUM_ROOM):
            self.CAV_A_SA_T_SA_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l  
            for k in xrange(self.NUM_SLOT):
                name = ['CAV_A_SA_T_SA_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)     
                self.CAV_A_SA_T_SA_LK[l].append(self.model.addVar(vtype=GRB.CONTINUOUS, name=name))
                
        self.model.update()
        logging.debug("CAV_A_SA_T_SA_LK:\n %s" %self.CAV_A_SA_T_SA_LK)
        
    #===========================================================================
    # Auxiliary Variables: Energy Consumption
    #===========================================================================
    def _createCAV_EnergyConsumption_Fan(self):
        """For each location at each timestep, create an auxiliary variable of e_fan(k, l)"""
        
        for l in xrange(self.NUM_ROOM):
            self.CAV_E_FAN_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l  
            for k in xrange(self.NUM_SLOT):
                name = ['CAV_E_FAN_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)         
                self.CAV_E_FAN_LK[l].append(self.model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=name))
                
        self.model.update()
        logging.debug("CAV_E_FAN_LK:\n %s" %self.CAV_E_FAN_LK)
        
    def _createCAV_EnergyConsumption_Conditioning(self):
        """For each location at each timestep, create an auxiliary variable of e_conditioning(k, l)"""
        
        for l in xrange(self.NUM_ROOM):
            self.CAV_E_CONDITIONING_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l  
            for k in xrange(self.NUM_SLOT):
                name = ['CAV_E_CONDITIONING_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)         
                self.CAV_E_CONDITIONING_LK[l].append(self.model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=name))
                
        self.model.update()
        logging.debug("CAV_E_CONDITIONING_LK:\n %s" %self.CAV_E_CONDITIONING_LK)
    
    def _createCAV_EnergyConsumption_Heating(self):
        """For each location at each timestep, create an auxiliary variable of e_heating(k, l)"""
        
        for l in xrange(self.NUM_ROOM):
            self.CAV_E_HEATING_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l  
            for k in xrange(self.NUM_SLOT):
                name = ['CAV_E_HEATING_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)         
                self.CAV_E_HEATING_LK[l].append(self.model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=name))
                
        self.model.update()
        logging.debug("CAV_E_HEATING_LK:\n %s" %self.CAV_E_HEATING_LK)
        
    #===========================================================================
    # Constraints
    #===========================================================================   
    
    #===========================================================================
    # Constraints: Room Alloc Based on Meeting Type
    #===========================================================================    
    def _createCSTR_Schedule_Once_MT(self):
        """Every meeting type must be scheduled to start at one feasible location exactly once within their respective time window."""
        
        for m in xrange(self.NUM_MEETING_TYPE):
            if self.SCHE_MODE == 1:
                mtype_id = self.CURR_DESTROY_MTYPE[m]
                num_meeting = self.CURR_DESTROY_MTYPE_NUM[m]
            else:
                mtype_id = self.MTYPE_ID[m]
                num_meeting = len(self.MTYPE_MID.get(mtype_id))
             
            self.CSTR_Schedule_Once_M.append([])                
            lcstr = 0
            for l in xrange(len(self.BDV_x_MLK[m])):                                    
                for k in xrange(len(self.BDV_x_MLK[m][l])):
                    lcstr += self.BDV_x_MLK[m][l][k] 
            
            name = ['CSTR_Schedule_Once_M', str(mtype_id)]
            name = '_'.join(name)
            self.CSTR_Schedule_Once_M[m].append(self.model.addConstr(lcstr == num_meeting, name))
            
        self.model.update()
        logging.debug("CSTR_Schedule_Once_M:\n %s" %self.CSTR_Schedule_Once_M)  
        
    def _createCSTR_LocationTimeOccupied_MT(self):
        """Set BAV_z_LK=1 at all time periods k if meeting type m is allocated in room L"""
        
        for k in xrange(self.NUM_SLOT):             
            lcstr = []
            for l in xrange(self.NUM_ROOM):
                lcstr.append([])
                lcstr[l] = 0
                                     
            for m in xrange(self.NUM_MEETING_TYPE):                
                if self.SCHE_MODE == 1:
                    mtype_id = self.CURR_DESTROY_MTYPE[m]
                    offset = self.MTYPE_ID.index(mtype_id)
                    mid = self.MTYPE[offset].MLS[0]
                else:
                    mtype_id = self.MTYPE_ID[m]
                    mid = self.MTYPE[m].MLS[0]
                    
                k_m = []
                k_m = self.EAMS.getFeasibleStartTime(mid, self.CURR_K+k)
                if k_m:                     
                    for l in xrange(self.NUM_ROOM):
                        if self.SCHE_MODE == 1:
                            dl = self.CURR_DESTROY_LOCATION[l]
                        else:
                            dl = l
                    
                        if dl in self.EAMS.MR[mid]:  #TODO: currently assume all meetings of the same type can use the same room! Need to re-group if not (_populateMeetingClique) !
                            for i in xrange(len(k_m)):
#                                 print mtype_id, " ", l, " ", k_m[i]
                                if self.BDV_x_MLK_Dict.get(tuple([mtype_id, dl, k_m[i]])) is not None:
                                    logging.debug("Meeting Type %d starts at %s still on-going at time period %d" %(mtype_id, k_m, self.CURR_K+k))
                                    mlk = self.BDV_x_MLK_Dict.get(tuple([mtype_id, dl, k_m[i]]))
                                    lcstr[l] += self.BDV_x_MLK[mlk[0]][mlk[1]][mlk[2]]
                            
            self.CSTR_LocationTimeOccupied.append([])
            for l in xrange(self.NUM_ROOM):
                if self.SCHE_MODE == 1:
                    dl = self.CURR_DESTROY_LOCATION[l]
                else:
                    dl = l
                        
                if lcstr[l]:
                    rcstr = self.BAV_z_LK[l][k]
                    name = ['CSTR_LocationTimeOccupied_KL', str(self.CURR_K+k), str(dl)]
                    name = '_'.join(name)
                    self.CSTR_LocationTimeOccupied[k].append(self.model.addConstr(lcstr[l] <= rcstr, name))
                elif self.MSTR_SCHE.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse.get(tuple([dl,self.CURR_K+k])) is not None: # ongoing meetings
                    logging.debug("(%d,%d) is occupied by %d" %(dl,self.CURR_K+k,self.MSTR_SCHE.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse.get(tuple([dl,self.CURR_K+k]))))
                    rcstr = self.BAV_z_LK[l][k]
                    name = ['CSTR_LocationTimeOccupied_KL', str(self.CURR_K+k), str(dl)]
                    name = '_'.join(name)
                    self.CSTR_LocationTimeOccupied[k].append(self.model.addConstr(1 <= rcstr, name))
                    
        self.model.update()
        logging.debug("CSTR_LocationTimeOccupied:\n %s" %self.CSTR_LocationTimeOccupied)
           
    def _createCSTR_NumAttendee_MT(self):
        """For each meeting type, represent number of attendee as a unique constraint. Note: Number of attendee is grouped by 5, 15, 30 people."""
        
        for k in xrange(self.NUM_SLOT):             
            lcstr = []
            for l in xrange(self.NUM_ROOM):
                lcstr.append([])
                lcstr[l] = 0
                                     
            for m in xrange(self.NUM_MEETING_TYPE):
                if self.SCHE_MODE == 1:
                    mtype_id = self.CURR_DESTROY_MTYPE[m]
                    offset = self.MTYPE_ID.index(mtype_id)
                    mid = self.MTYPE[offset].MLS[0]
                else:
                    mtype_id = self.MTYPE_ID[m]
                    mid = self.MTYPE[m].MLS[0]
                     
                k_m = []
                k_m = self.EAMS.getFeasibleStartTime(mid, self.CURR_K+k)
                if k_m:
                    for l in xrange(self.NUM_ROOM):
                        if self.SCHE_MODE == 1:
                            dl = self.CURR_DESTROY_LOCATION[l]
                        else:
                            dl = l
                        if dl in self.EAMS.MR[mid]:    #TODO: currently assume all meetings of the same type can use the same room! Need to re-group if not (_populateMeetingClique) !
                            for i in xrange(len(k_m)):
                                if self.BDV_x_MLK_Dict.get(tuple([mtype_id, dl, k_m[i]])) is not None:
                                    mlk = self.BDV_x_MLK_Dict.get(tuple([mtype_id, dl, k_m[i]]))
                                    lcstr[l] += self.MTYPE[m].MA*self.BDV_x_MLK[mlk[0]][mlk[1]][mlk[2]]
                            
            self.CSTR_NumAttendee.append([])
            for l in xrange(self.NUM_ROOM):
                if self.SCHE_MODE == 1:
                    dl = self.CURR_DESTROY_LOCATION[l]
                else:
                    dl = l
                rcstr = self.DAV_Attendee_LK[l][k]
                name = ['CSTR_NumAttendee_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)  
                if lcstr[l]:
                    self.CSTR_NumAttendee[k].append(self.model.addConstr(lcstr[l] == rcstr, name))
                elif self.MSTR_SCHE.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse.get(tuple([dl,self.CURR_K+k])) is not None: # ongoing meetings
                    logging.debug("(%d,%d) is occupied by %d" %(dl,self.CURR_K+k,self.MSTR_SCHE.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse.get(tuple([dl,self.CURR_K+k]))))
                    cstr = self.MSTR_SCHE.MSTR_DAV_Attendee_LK[dl][self.CURR_K+k]
                    self.CSTR_NumAttendee[k].append(self.model.addConstr(cstr == rcstr, name))
                else:
                    self.CSTR_NumAttendee[k].append(self.model.addConstr(0 == rcstr, name))
                    
        self.model.update()
        logging.debug("CSTR_NumAttendee:\n %s" %self.CSTR_NumAttendee)
        
    def _createCSTR_AttendeeConflict_MT(self):
        """Meetings Types which have the same attendee(s) should not be allocated into the same time period"""
        
        if self.SCHE_MODE == 1:
#             Given  UNIQ_CMT:[[1, 4], [10, 18, 27], [0, 4], [20, 29], [7, 27], [9, 19], [11, 30], [6, 13], [17, 33], [2, 33], [16, 25]]
#                    self.CURR_DESTROY_MTYPE: [1, 8, 12, 14, 17, 33]
#             Check if any combinations in uniq_mtls exists in CURR_DESTROY_MTYPE.
#             In this example:  CURR_UNIQ_CMT:[[17, 33]]
            
            logging.debug("self.CURR_DESTROY_MTYPE: %s" %(self.CURR_DESTROY_MTYPE))
            self.CURR_UNIQ_CMT = []
            for sublist in self.UNIQ_CMT:
                self.CURR_UNIQ_CMT.append(list(set(sublist).intersection(set(self.CURR_DESTROY_MTYPE))))            
            logging.debug("CURR_UNIQ_CMT: %s" %(self.CURR_UNIQ_CMT))
        else:
            self.CURR_UNIQ_CMT = self.UNIQ_CMT  
        
        for k in xrange(self.NUM_SLOT):
            self.CSTR_AttendeeConflict.append([])
            
            for s in xrange(len(self.CURR_UNIQ_CMT)):      
                mts = self.CURR_UNIQ_CMT[s]
                logging.debug("Conflict Meeting Types:%s" %mts)
                om = []
                for mt in xrange(len(mts)):
                    mtid = mts[mt]                          # mtid is the offset of GLOBAL mtype 
                    mtoffset = self.MTYPE_ID.index(mtid)    # mtoffset is the offset of mtid at LOCAL mtype
                    m = self.MTYPE[mtoffset].MLS[0]           # to get the time window of MTYPE, so simply get the first meeting in MLS
                    if self.EAMS.isInStartTimeWindows(m,self.CURR_K+k) > 0:
                        logging.debug("++ k: %d" %(self.CURR_K+k))    
                        logging.debug("----%s" %self.EAMS.getFeasibleStartTime(m, self.CURR_K+k))
                        
                        om.append([mtid, self.EAMS.getFeasibleStartTime(m, self.CURR_K+k)])
                        
#                         if self.SCHE_MODE == 1:
#                             did = self.CURR_DESTROY_MTYPE.index(mtid)
#                             om.append([did, self.EAMS.getFeasibleStartTime(m, self.CURR_K+k)])
#                         else:
#                             om.append([mtid, self.EAMS.getFeasibleStartTime(m, self.CURR_K+k)])
                            
                if len(om) > 0: # has conflict
                    logging.debug("om: %s" %om)
                    lcstr = 0
                    has_lcstr = False
                    for j in xrange(len(om)):    
                        logging.debug("om[%d]: %s" %(j,om[j]))    
                        logging.debug("om[%d][0]: %s" %(j, om[j][0]))
                        mk = om[j][1]
                        for p in xrange(len(mk)):
                            logging.debug("om[%d][1] [%d]: %s" %(j, p, mk[p]))      
                                     
                            for l in xrange(self.NUM_ROOM):  
                                if self.SCHE_MODE == 1:
                                    dl = self.CURR_DESTROY_LOCATION[l]
                                else:
                                    dl = l

                                mlk = self.BDV_x_MLK_Dict.get(tuple([om[j][0], dl, mk[p]]))    
                                logging.debug("MLK_%s" %mlk)
                                if mlk:
                                    has_lcstr = True
                                    lcstr += self.BDV_x_MLK[mlk[0]][mlk[1]][mlk[2]]
                    
                    if has_lcstr:
                        logging.debug(lcstr)
                        name = ['CSTR_AttendeeConflict_K', str(self.CURR_K+k)]
                        name = '_'.join(name)                        
                        self.CSTR_AttendeeConflict[k].append(self.model.addConstr(lcstr <= 1, name))
                    
        self.model.update()
        logging.debug("CSTR_AttendeeConflict:\n %s" %self.CSTR_AttendeeConflict)

        

    #===========================================================================
    # Constraints: HVAC
    #===========================================================================
    def _get_A_SA_LB(self, l, k):        
        if self.EAMS.SH[k] == 1:
            [width, length, height] = self.EAMS.getRoomThermalConfig(l, "Dim")
            A_SA_LB = self.EAMS.ALPHA_IAQ_FACTOR_OF_SAFETY*(
                                                    (self.EAMS.MASS_AIR_FLOW_OUTSIDE_AIR_PER_METER_SQUARE * width * length * height) /
                                                    (1-self.EAMS.MASS_AIR_FLOW_RETURN_AIR_RATIO))
        else:
            A_SA_LB = self.EAMS.MASS_AIR_FLOW_SUPPLY_AIR_MIN
        
        return float(A_SA_LB)
    
    def _get_T_SA_LB(self, l, k):
        if self.EAMS.SH[k] == 1:
            return float(self.EAMS.TEMPERATURE_CONDITIONED_AIR)
        else:
            return float(0) #float(self.EAMS.INITIAL_TEMPERATURE_SUPPLY_AIR_UNOCC)
        
        
    def _createCSTR_RoomTemperature_LB(self):
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
                rcstr = float(self.EAMS.TEMPERATURE_UNOCC_MIN) + (float(self.EAMS.TEMPERATURE_OCC_COMFORT_RANGE_INCR) * self.BAV_z_LK[l][k])   
                self.CSTR_T_LK_lb[l].append(self.model.addConstr(lcstr >= rcstr, name))
             
        self.model.update()
        logging.debug("CSTR_T_LK_lb:\n %s" %self.CSTR_T_LK_lb)
        
    def _createCSTR_RoomTemperature_UB(self):
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
                rcstr = float(self.EAMS.TEMPERATURE_UNOCC_MAX) - (float(self.EAMS.TEMPERATURE_OCC_COMFORT_RANGE_DECR)*self.BAV_z_LK[l][k]) 
                self.CSTR_T_LK_ub[l].append(self.model.addConstr(lcstr <= rcstr, name))
             
        self.model.update()
        logging.debug("CSTR_T_LK_ub:\n %s" %self.CSTR_T_LK_ub)
        
    def _createCSTR_RoomTemperature(self):
        """For each location at each timestep, create a constraint for room temperature T(k, l)"""
        
        for l in xrange(self.NUM_ROOM):
            self.CSTR_T_LK.append([])
            
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
            
            A = self.EAMS.getRoomThermalConfig(dl, "C")
            B1 =  self.EAMS.getRoomThermalConfig(dl, "Rij")
            B2 =  self.EAMS.getRoomThermalConfig(dl, "Rik")
            B3 =  self.EAMS.getRoomThermalConfig(dl, "Ril")
            B4 =  self.EAMS.getRoomThermalConfig(dl, "Rio")
            B5 =  self.EAMS.getRoomThermalConfig(dl, "Rif")
            B6 =  self.EAMS.getRoomThermalConfig(dl, "Ric")            
            #TODO: For the moment, only 1 wall could have window. Test with more windows
            B7 = self.EAMS.getRoomThermalConfig(dl, "Rwij")            
            C = self.EAMS.AIR_HEAT_CAPACITY_AT_CONSTANT_PRESSURE            
            D = float(self.EAMS.SCHEDULING_INTERVAL)*60 / A            
            E1 = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (A*B1)
            E2 = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (A*B2)
            E3 = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (A*B3)
            E4 = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (A*B4)
            E5 = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (A*B5)
            E6 = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (A*B6)
            E7 = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (A*B7)
            F = D * self.EAMS.OCCUPANT_SENSIBLE_HEAT_GAIN
                
            for k in xrange(self.NUM_SLOT):          
                name = ['CSTR_T_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)
                
                if k != 0:
                    BG = 0
                    EG = 0
                    if (self.EAMS.RNL[dl][0] == self.N_OUTDOOR):
                        BG += (self.CAV_T_LK[l][k-1] / B1)   
                        EG += (E1 * self.CAV_T_l_z1_LK[l][k-1])
                                    
                    if (self.EAMS.RNL[dl][1] == self.N_OUTDOOR):
                        BG += (self.CAV_T_LK[l][k-1] / B2)   
                        EG += (E2 * self.CAV_T_l_z2_LK[l][k-1])
                                                
                    if (self.EAMS.RNL[dl][2] == self.N_OUTDOOR):
                        BG += (self.CAV_T_LK[l][k-1] / B3)     
                        EG += (E3 * self.CAV_T_l_z3_LK[l][k-1])
                                            
                    if (self.EAMS.RNL[dl][3] == self.N_OUTDOOR):
                        BG += (self.CAV_T_LK[l][k-1] / B4)
                        EG += (E4 * self.CAV_T_l_z4_LK[l][k-1])
                        
                    BG += (self.CAV_T_LK[l][k-1] / B5)
                    EG += (E5 * self.CAV_T_l_f_LK[l][k-1])
                    
                    BG += (self.CAV_T_LK[l][k-1] / B6)
                    EG += (E6 * self.CAV_T_l_c_LK[l][k-1])
                    
                    BG += (self.CAV_T_LK[l][k-1] / B7)
                    EG += (E7 * float(self.EAMS.OAT.values()[self.CURR_K+k-1]))
                        
                    rcstr = (
                             (self.CAV_T_LK[l][k-1] - 
                             (D *
                              (BG +
                              (C * self.CAV_A_SA_T_z_LK[l][k-1])
                              )
                             )
                             ) + 
                             EG +                         
                             (F * self.DAV_Attendee_LK[l][k-1]) + 
                             (D * C * self.CAV_A_SA_T_SA_LK[l][k-1]))
                    
                else: # no occupant at previous session (k=-1)
                    rcstr = self.INITIAL_TEMPERATURE[dl]
                
                lcstr = self.CAV_T_LK[l][k]         
                self.CSTR_T_LK[l].append(self.model.addConstr(lcstr==rcstr, name))
                
        self.model.update()
        logging.debug("CSTR_T_LK:\n %s" %self.CSTR_T_LK)
        
#-----------------------------------        
        
    def _createCSTR_T_z1_l(self):        
        for l in xrange(self.NUM_ROOM):
            self.CSTR_T_z1_l_LK.append([])      
            
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
                
            if (self.EAMS.RNL[dl][0] == self.N_OUTDOOR):
                nz = self.EAMS.RNL[dl][0]
                A = float(self.EAMS.SCHEDULING_INTERVAL)*60 / self.EAMS.getRoomThermalConfig(dl, "Cij")
                B = float(1)/self.EAMS.getRoomThermalConfig(dl, "Rji")
                C = float(1)/self.EAMS.getRoomThermalConfig(dl, "Rimj")
                D = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (self.EAMS.getRoomThermalConfig(dl, "Cij") * self.EAMS.getRoomThermalConfig(dl, "Rimj"))
                E = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (self.EAMS.getRoomThermalConfig(dl, "Cij") * self.EAMS.getRoomThermalConfig(dl, "Rji"))
                H = 1-(A*(B+C)) 
                
                logging.debug("Cij = %s" %(self.EAMS.getRoomThermalConfig(dl, "Cij")))  
                logging.debug("A = %s" %(A))
                logging.debug("B = %s" %(B))
                logging.debug("C = %s" %(C))
                logging.debug("H = %s" %(H))
                                                     
                for k in xrange(self.NUM_SLOT):                
                    name = ['CSTR_T_z1_l_LK', str(dl), str(self.CURR_K+k)]
                    name = '_'.join(name)                
                     
                    if k != 0:
                        if nz == self.N_OUTDOOR:
                            F = float(self.EAMS.OAT.values()[self.CURR_K+k-1])
                        else:
                            F = self.CAV_T_LK[nz][k-1]                        
                        G = self.EAMS.getRoomSolarGain(self.CURR_K+k-1, dl, 0)
                            
                        rcstr = (
                                 (H * self.CAV_T_z1_l_LK[l][k-1]) +
                                 (D * self.CAV_T_l_z1_LK[l][k-1]) +
                                 (E * F) +
                                 (A * G)
                                 )
                    else:
                        rcstr = self.INITIAL_CAV_T_z1_l_L[dl]
     
                    lcstr = self.CAV_T_z1_l_LK[l][k]                 
                    self.CSTR_T_z1_l_LK[l].append(self.model.addConstr(lcstr == rcstr, name))
                  
        self.model.update()
        logging.debug("CSTR_T_z1_l_LK:\n %s" %self.CSTR_T_z1_l_LK)
        
    def _createCSTR_T_l_z1(self):
        for l in xrange(self.NUM_ROOM):
            self.CSTR_T_l_z1_LK.append([])
            
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
            
            if (self.EAMS.RNL[dl][0] == self.N_OUTDOOR):
                A = float(self.EAMS.SCHEDULING_INTERVAL)*60 / self.EAMS.getRoomThermalConfig(dl, "Cji")
                B = float(1)/self.EAMS.getRoomThermalConfig(dl, "Rij")
                C = float(1)/self.EAMS.getRoomThermalConfig(dl, "Rimj")
                D = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (self.EAMS.getRoomThermalConfig(dl, "Cji") * self.EAMS.getRoomThermalConfig(dl, "Rij"))
                E = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (self.EAMS.getRoomThermalConfig(dl, "Cji") * self.EAMS.getRoomThermalConfig(dl, "Rimj"))
                
                for k in xrange(self.NUM_SLOT):                
                    name = ['CSTR_T_l_z1_LK', str(dl), str(self.CURR_K+k)]
                    name = '_'.join(name)                
                     
                    if k != 0:    
                        rcstr = (
                                 ((1-A*(B+C))*self.CAV_T_l_z1_LK[l][k-1]) +
                                 (D * self.CAV_T_LK[l][k-1]) +
                                 (E * self.CAV_T_z1_l_LK[l][k-1])
                                 )
                    else:
                        rcstr = self.INITIAL_CAV_T_l_z1_L[dl] 
                    
                    lcstr = self.CAV_T_l_z1_LK[l][k]
                    self.CSTR_T_l_z1_LK[l].append(self.model.addConstr(lcstr == rcstr, name))
                 
        self.model.update()
        logging.debug("CSTR_T_l_z1_LK:\n %s" %self.CSTR_T_l_z1_LK)
        
    def _createCSTR_T_z2_l(self):
        for l in xrange(self.NUM_ROOM):
            self.CSTR_T_z2_l_LK.append([])
            
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
            
            if (self.EAMS.RNL[dl][1] == self.N_OUTDOOR):
                nz = self.EAMS.RNL[dl][1]
                A = float(self.EAMS.SCHEDULING_INTERVAL)*60 / self.EAMS.getRoomThermalConfig(dl, "Cik")
                B = float(1)/self.EAMS.getRoomThermalConfig(dl, "Rki")
                C = float(1)/self.EAMS.getRoomThermalConfig(dl, "Rimk")
                D = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (self.EAMS.getRoomThermalConfig(dl, "Cik") * self.EAMS.getRoomThermalConfig(dl, "Rimk"))
                E = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (self.EAMS.getRoomThermalConfig(dl, "Cik") * self.EAMS.getRoomThermalConfig(dl, "Rki"))
                                         
                for k in xrange(self.NUM_SLOT):                
                    name = ['CSTR_T_z2_l_LK', str(dl), str(self.CURR_K+k)]
                    name = '_'.join(name)                
                     
                    if k != 0:
                        if nz == self.N_OUTDOOR:
                            F = float(self.EAMS.OAT.values()[self.CURR_K+k-1])
                        elif nz == self.N_NOT_EXIST:
                            F = self.CAV_T_LK[l][k-1]
                        else:
                            F = self.CAV_T_LK[nz][k-1]
                        
                        G = self.EAMS.getRoomSolarGain(self.CURR_K+k-1, dl, 1)
                            
                        rcstr = (
                                 ((1-A*(B+C))*self.CAV_T_z2_l_LK[l][k-1]) +
                                 (D * self.CAV_T_l_z2_LK[l][k-1]) +
                                 (E * F) +
                                 (A * G)
                                 )
                    else:
                        rcstr = self.INITIAL_CAV_T_z2_l_L[dl]
                        
                    lcstr = self.CAV_T_z2_l_LK[l][k]
                    self.CSTR_T_z2_l_LK[l].append(self.model.addConstr(lcstr == rcstr, name))
                 
        self.model.update()
        logging.debug("CSTR_T_z2_l_LK:\n %s" %self.CSTR_T_z2_l_LK)
        
    def _createCSTR_T_l_z2(self):
        for l in xrange(self.NUM_ROOM):
            self.CSTR_T_l_z2_LK.append([])
            
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
            
            if (self.EAMS.RNL[dl][1] == self.N_OUTDOOR):            
                A = float(self.EAMS.SCHEDULING_INTERVAL)*60 / self.EAMS.getRoomThermalConfig(dl, "Cki")
                B = float(1)/self.EAMS.getRoomThermalConfig(dl, "Rik")
                C = float(1)/self.EAMS.getRoomThermalConfig(dl, "Rimk")
                D = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (self.EAMS.getRoomThermalConfig(dl, "Cki") * self.EAMS.getRoomThermalConfig(dl, "Rik"))
                E = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (self.EAMS.getRoomThermalConfig(dl, "Cki") * self.EAMS.getRoomThermalConfig(dl, "Rimk"))
                
                for k in xrange(self.NUM_SLOT):                
                    name = ['CSTR_T_l_z2_LK', str(dl), str(self.CURR_K+k)]
                    name = '_'.join(name)                
                     
                    if k != 0:    
                        rcstr = (
                                 ((1-A*(B+C))*self.CAV_T_l_z2_LK[l][k-1]) +
                                 (D * self.CAV_T_LK[l][k-1]) +
                                 (E * self.CAV_T_z2_l_LK[l][k-1])
                                 )
                    else:
                        rcstr = self.INITIAL_CAV_T_l_z2_L[dl]        
                     
                    lcstr = self.CAV_T_l_z2_LK[l][k]
                    self.CSTR_T_l_z2_LK[l].append(self.model.addConstr(lcstr == rcstr, name))
                 
        self.model.update()
        logging.debug("CSTR_T_l_z2_LK:\n %s" %self.CSTR_T_l_z2_LK)
        
    def _createCSTR_T_z3_l(self):
        for l in xrange(self.NUM_ROOM):
            self.CSTR_T_z3_l_LK.append([])
            
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
            
            if (self.EAMS.RNL[dl][2] == self.N_OUTDOOR):            
                nz = self.EAMS.RNL[dl][2]
                A = float(self.EAMS.SCHEDULING_INTERVAL)*60 / self.EAMS.getRoomThermalConfig(dl, "Cil")
                B = float(1)/self.EAMS.getRoomThermalConfig(dl, "Rli")
                C = float(1)/self.EAMS.getRoomThermalConfig(dl, "Riml")
                D = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (self.EAMS.getRoomThermalConfig(dl, "Cil") * self.EAMS.getRoomThermalConfig(dl, "Riml"))
                E = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (self.EAMS.getRoomThermalConfig(dl, "Cil") * self.EAMS.getRoomThermalConfig(dl, "Rli"))
          
                for k in xrange(self.NUM_SLOT):                
                    name = ['CSTR_T_z3_l_LK', str(dl), str(self.CURR_K+k)]
                    name = '_'.join(name)        
                    
                    if k != 0:
                        if nz == self.N_OUTDOOR:
                            F = float(self.EAMS.OAT.values()[self.CURR_K+k-1])
                        elif nz == self.N_NOT_EXIST:
                            F = self.CAV_T_LK[l][k-1]
                        else:
                            F = self.CAV_T_LK[nz][k-1]
                        
                        G = self.EAMS.getRoomSolarGain(self.CURR_K+k-1, dl, 2)
                            
                        rcstr = (
                                 ((1-A*(B+C))*self.CAV_T_z3_l_LK[l][k-1]) +
                                 (D * self.CAV_T_l_z3_LK[l][k-1]) +
                                 (E * F) +
                                 (A * G)
                                 )
                    else:
                        rcstr = self.INITIAL_CAV_T_z3_l_L[dl] 
                     
                    lcstr = self.CAV_T_z3_l_LK[l][k]                
                    self.CSTR_T_z3_l_LK[l].append(self.model.addConstr(lcstr == rcstr, name))
                 
        self.model.update()
        logging.debug("CSTR_T_z3_l_LK:\n %s" %self.CSTR_T_z3_l_LK)
        
    def _createCSTR_T_l_z3(self):
        for l in xrange(self.NUM_ROOM):
            self.CSTR_T_l_z3_LK.append([])
            
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
                
            if (self.EAMS.RNL[dl][2] == self.N_OUTDOOR):            
                A = float(self.EAMS.SCHEDULING_INTERVAL)*60 / self.EAMS.getRoomThermalConfig(dl, "Cli")
                B = float(1)/self.EAMS.getRoomThermalConfig(dl, "Ril")
                C = float(1)/self.EAMS.getRoomThermalConfig(dl, "Riml")
                D = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (self.EAMS.getRoomThermalConfig(dl, "Cli") * self.EAMS.getRoomThermalConfig(dl, "Ril"))
                E = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (self.EAMS.getRoomThermalConfig(dl, "Cli") * self.EAMS.getRoomThermalConfig(dl, "Riml"))
                
                for k in xrange(self.NUM_SLOT):                
                    name = ['CSTR_T_l_z3_LK', str(dl), str(self.CURR_K+k)]
                    name = '_'.join(name)                
                     
                    if k != 0:    
                        rcstr = (
                                 ((1-A*(B+C))*self.CAV_T_l_z3_LK[l][k-1]) +
                                 (D * self.CAV_T_LK[l][k-1]) +
                                 (E * self.CAV_T_z3_l_LK[l][k-1])
                                 )
                    else:
                        rcstr = self.INITIAL_CAV_T_l_z3_L[dl]      
                     
                    lcstr = self.CAV_T_l_z3_LK[l][k]
                    self.CSTR_T_l_z3_LK[l].append(self.model.addConstr(lcstr == rcstr, name))
                 
        self.model.update()
        logging.debug("CSTR_T_l_z3_LK:\n %s" %self.CSTR_T_l_z3_LK)
             
    def _createCSTR_T_z4_l(self):
        for l in xrange(self.NUM_ROOM):
            self.CSTR_T_z4_l_LK.append([])
            
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l            
            
            if (self.EAMS.RNL[dl][3] == self.N_OUTDOOR):            
                nz = self.EAMS.RNL[dl][3]
                A = float(self.EAMS.SCHEDULING_INTERVAL)*60 / self.EAMS.getRoomThermalConfig(dl, "Cio")
                B = float(1)/self.EAMS.getRoomThermalConfig(dl, "Roi")
                C = float(1)/self.EAMS.getRoomThermalConfig(dl, "Rimo")
                D = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (self.EAMS.getRoomThermalConfig(dl, "Cio") * self.EAMS.getRoomThermalConfig(dl, "Rimo"))
                E = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (self.EAMS.getRoomThermalConfig(dl, "Cio") * self.EAMS.getRoomThermalConfig(dl, "Roi"))
          
                for k in xrange(self.NUM_SLOT):                
                    name = ['CSTR_T_z4_l_LK', str(dl), str(self.CURR_K+k)]
                    name = '_'.join(name)                
                     
                    if k != 0:
                        if nz == self.N_OUTDOOR:
                            F = float(self.EAMS.OAT.values()[self.CURR_K+k-1])
                        elif nz == self.N_NOT_EXIST:
                            F = self.CAV_T_LK[l][k-1]
                        else:
                            F = self.CAV_T_LK[nz][k-1]
                        
                        G = self.EAMS.getRoomSolarGain(self.CURR_K+k-1, dl, 3)
                            
                        rcstr = (
                                 ((1-A*(B+C))*self.CAV_T_z4_l_LK[l][k-1]) +
                                 (D * self.CAV_T_l_z4_LK[l][k-1]) +
                                 (E * F) +
                                 (A * G)
                                 )
                    else:
                        rcstr = self.INITIAL_CAV_T_z4_l_L[dl]
                        
                    lcstr = self.CAV_T_z4_l_LK[l][k]                
                    self.CSTR_T_z4_l_LK[l].append(self.model.addConstr(lcstr == rcstr, name))
                 
        self.model.update()
        logging.debug("CSTR_T_z4_l_LK:\n %s" %self.CSTR_T_z4_l_LK)
        
    def _createCSTR_T_l_z4(self):
        for l in xrange(self.NUM_ROOM):
            self.CSTR_T_l_z4_LK.append([])
            
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l  
                        
            if (self.EAMS.RNL[dl][3] == self.N_OUTDOOR):            
                A = float(self.EAMS.SCHEDULING_INTERVAL)*60 / self.EAMS.getRoomThermalConfig(dl, "Coi")
                B = float(1)/self.EAMS.getRoomThermalConfig(dl, "Rio")
                C = float(1)/self.EAMS.getRoomThermalConfig(dl, "Rimo")
                D = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (self.EAMS.getRoomThermalConfig(dl, "Coi") * self.EAMS.getRoomThermalConfig(dl, "Rio"))
                E = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (self.EAMS.getRoomThermalConfig(dl, "Coi") * self.EAMS.getRoomThermalConfig(dl, "Rimo"))
                
                for k in xrange(self.NUM_SLOT):                
                    name = ['CSTR_T_l_z4_LK', str(dl), str(self.CURR_K+k)]
                    name = '_'.join(name)                
                     
                    if k != 0:    
                        rcstr = (
                                 ((1-A*(B+C))*self.CAV_T_l_z4_LK[l][k-1]) +
                                 (D * self.CAV_T_LK[l][k-1]) +
                                 (E * self.CAV_T_z4_l_LK[l][k-1])
                                 )
                    else:
                        rcstr = self.INITIAL_CAV_T_l_z4_L[dl]           
                     
                    lcstr = self.CAV_T_l_z4_LK[l][k]                
                    self.CSTR_T_l_z4_LK[l].append(self.model.addConstr(lcstr == rcstr, name))
                 
        self.model.update()
        logging.debug("CSTR_T_l_z4_LK:\n %s" %self.CSTR_T_l_z4_LK)
        
    def _createCSTR_T_l_f(self):
        for l in xrange(self.NUM_ROOM):
            self.CSTR_T_l_f_LK.append([])
            
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l 
            
            A = float(self.EAMS.SCHEDULING_INTERVAL)*60 / self.EAMS.getRoomThermalConfig(dl, "Cif")
            B = float(1)/self.EAMS.getRoomThermalConfig(dl, "Rif")
            C = float(1)/self.EAMS.getRoomThermalConfig(dl, "Rfi")
            D = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (self.EAMS.getRoomThermalConfig(dl, "Cif") * self.EAMS.getRoomThermalConfig(dl, "Rif"))
            E = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (self.EAMS.getRoomThermalConfig(dl, "Cif") * self.EAMS.getRoomThermalConfig(dl, "Rfi"))
            F = float(self.EAMS.SCHEDULING_INTERVAL)*60 / self.EAMS.getRoomThermalConfig(dl, "Cfi")
       
            for k in xrange(self.NUM_SLOT):                
                name = ['CSTR_T_l_f_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)                
                
                G = self.EAMS.getRoomSolarGain(self.CURR_K+k-1, dl, 4)
                
                if k != 0:    
                    rcstr = (
                             ((1-A*(B+C))*self.CAV_T_l_f_LK[l][k-1]) +
                             (D * self.CAV_T_LK[l][k-1]) +
                             (E * float(self.EAMS.OAT.values()[self.CURR_K+k-1])) +
                             (F * G)
                             )
                else:
                    rcstr = self.INITIAL_CAV_T_l_f_L[dl]   
                
                lcstr = self.CAV_T_l_f_LK[l][k]
                self.CSTR_T_l_f_LK[l].append(self.model.addConstr(lcstr == rcstr, name))
             
        self.model.update()
        logging.debug("CSTR_T_l_f_LK:\n %s" %self.CSTR_T_l_f_LK)
        
    def _createCSTR_T_l_c(self):
        for l in xrange(self.NUM_ROOM):
            self.CSTR_T_l_c_LK.append([])
            
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l             
            
            A = float(self.EAMS.SCHEDULING_INTERVAL)*60 / self.EAMS.getRoomThermalConfig(dl, "Cic")
            B = float(1)/self.EAMS.getRoomThermalConfig(dl, "Ric")
            C = float(1)/self.EAMS.getRoomThermalConfig(dl, "Rci")
            D = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (self.EAMS.getRoomThermalConfig(dl, "Cic") * self.EAMS.getRoomThermalConfig(dl, "Ric"))
            E = float(self.EAMS.SCHEDULING_INTERVAL)*60 / (self.EAMS.getRoomThermalConfig(dl, "Cic") * self.EAMS.getRoomThermalConfig(dl, "Rci"))
            
            for k in xrange(self.NUM_SLOT):                
                name = ['CSTR_T_l_c_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)             
                
                if k != 0:    
                    rcstr = (
                             ((1-A*(B+C))*self.CAV_T_l_c_LK[l][k-1]) +
                             (D * self.CAV_T_LK[l][k-1]) +
                             (E * float(self.EAMS.OAT.values()[self.CURR_K+k-1]))
                             )
                else:
                    rcstr = self.INITIAL_CAV_T_l_c_L[dl]      
                 
                lcstr = self.CAV_T_l_c_LK[l][k]
                self.CSTR_T_l_c_LK[l].append(self.model.addConstr(lcstr == rcstr, name))
             
        self.model.update()
        logging.debug("CSTR_T_l_c_LK:\n %s" %self.CSTR_T_l_c_LK)    
    
    #===========================================================================
    # Constraints: Standby Mode
    #===========================================================================
    def _createCSTR_SupplyAirTemperature_LB_hasStandbyMode(self):
        for l in xrange(self.NUM_ROOM):        
            self.CSTR_T_SA_LB_LK.append([])
            
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l               
            
            for k in xrange(self.NUM_SLOT):                
                name = ['CSTR_T_SA_LB_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)               
                 
                lcstr = self.CDV_T_SA_LK[l][k]
                if self.EAMS.SH[self.CURR_K+k] == 1:
                    rcstr = float(self.EAMS.TEMPERATURE_CONDITIONED_AIR)
                    self.CSTR_T_SA_LB_LK[l].append(self.model.addConstr(lcstr >= rcstr, name))
                else:
                    lk = self.BDV_w_LK_Dict.get(tuple([l, self.CURR_K+k]))
                    rcstr = float(self.EAMS.TEMPERATURE_CONDITIONED_AIR) * self.BDV_w_LK[lk[0]][lk[1]]
                    self.CSTR_T_SA_LB_LK[l].append(self.model.addConstr(lcstr >= rcstr, name))
                             
        self.model.update()
        logging.debug("CSTR_T_SA_LB_LK:\n %s" %self.CSTR_T_SA_LB_LK)
        
    def _createCSTR_SupplyAirTemperature_UB_hasStandbyMode(self):
        for l in xrange(self.NUM_ROOM):        
            self.CSTR_T_SA_UB_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l               
            for k in xrange(self.NUM_SLOT):                
                name = ['CSTR_T_SA_UB_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)               
                 
                lcstr = self.CDV_T_SA_LK[l][k]
                # Not necessary to set the upper bound of SH==1, as it is the same as T_SA default UB
                if self.EAMS.SH[self.CURR_K+k] == 0: 
                    lk = self.BDV_w_LK_Dict.get(tuple([dl, self.CURR_K+k]))
                    rcstr = float(self.EAMS.TEMPERATURE_SUPPLY_AIR_HIGH) * self.BDV_w_LK[lk[0]][lk[1]]
                    self.CSTR_T_SA_UB_LK[l].append(self.model.addConstr(lcstr <= rcstr, name))
                             
        self.model.update()
        logging.debug("CSTR_T_SA_UB_LK:\n %s" %self.CSTR_T_SA_UB_LK)
        
    def _createCSTR_SupplyAirFlowRate_LB_hasStandbyMode(self):
        """For each location at each timestep, create a constraint for lower bound of air mass flow rate"""
        
        for l in xrange(self.NUM_ROOM):
            self.CSTR_A_SA_LB_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l               
            for k in xrange(self.NUM_SLOT):                
                name = ['CSTR_A_SA_LB_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)                
                
                lcstr = self.CDV_A_SA_LK[l][k]
                if self.EAMS.SH[self.CURR_K+k] == 1:
                    rcstr = self._get_A_SA_LB(dl,self.CURR_K+k)
                else: 
                    #TODO:  as long as ASA_LB for sh[k]=0 is set to 0, this cstr can be removed.
                    lk = self.BDV_w_LK_Dict.get(tuple([dl, self.CURR_K+k]))
                    rcstr = self._get_A_SA_LB(dl,self.CURR_K+k) * self.BDV_w_LK[lk[0]][lk[1]]
                self.CSTR_A_SA_LB_LK[l].append(self.model.addConstr(lcstr >= rcstr, name))
                    
        self.model.update()
        logging.debug("CSTR_A_SA_LB_LK:\n %s" %self.CSTR_A_SA_LB_LK)
        
    def _createCSTR_SupplyAirFlowRate_UB_hasStandbyMode(self):
        for l in xrange(self.NUM_ROOM):
            self.CSTR_A_SA_UB_LK.append([])      
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l         
            for k in xrange(self.NUM_SLOT):                
                name = ['CSTR_A_SA_UB_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)                
                
                lcstr = self.CDV_A_SA_LK[l][k]
                if self.EAMS.SH[self.CURR_K+k] == 0: # Not necessary to set the upper bound of SH==1, as it is the same as A_SA default UB
                    lk = self.BDV_w_LK_Dict.get(tuple([dl, self.CURR_K+k]))
                    rcstr = self.EAMS.MASS_AIR_FLOW_SUPPLY_AIR_MAX * self.BDV_w_LK[lk[0]][lk[1]]
                    self.CSTR_A_SA_UB_LK[l].append(self.model.addConstr(lcstr <= rcstr, name))
                    
        self.model.update()
        logging.debug("CSTR_A_SA_UB_LK:\n %s" %self.CSTR_A_SA_UB_LK)
        
#-----------------------------------
        
    def _createCSTR_A_SA_T_SA_1_LK_hasStandbyMode(self):
        for l in xrange(self.NUM_ROOM):
            self.CSTR_A_SA_T_SA_1_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l               
            for k in xrange(self.NUM_SLOT):
                name = ['CSTR_A_SA_T_SA_1_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)
                
                T_SA    = self.CDV_T_SA_LK[l][k]
                T_SA_LB = self._get_T_SA_LB(dl,self.CURR_K+k)
                A_SA    = self.CDV_A_SA_LK[l][k]      
                A_SA_LB = self._get_A_SA_LB(dl,self.CURR_K+k)
                              
                lcstr = self.CAV_A_SA_T_SA_LK[l][k]
                
                rcstr = (A_SA_LB * T_SA) + (T_SA_LB * A_SA) - (A_SA_LB * T_SA_LB)
                self.CSTR_A_SA_T_SA_1_LK[l].append(self.model.addQConstr(lcstr >= rcstr, name=name))
                    
                                    
        self.model.update()
        logging.debug("CSTR_A_SA_T_SA_1_LK:\n %s" %self.CSTR_A_SA_T_SA_1_LK)
        
    def _createCSTR_A_SA_T_SA_2_LK_hasStandbyMode(self):        
        A_SA_UB = self.EAMS.MASS_AIR_FLOW_SUPPLY_AIR_MAX
        T_SA_UB = self.EAMS.TEMPERATURE_SUPPLY_AIR_HIGH
        
        for l in xrange(self.NUM_ROOM):
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l   
            self.CSTR_A_SA_T_SA_2_LK.append([])
            for k in xrange(self.NUM_SLOT):
                name = ['CSTR_A_SA_T_SA_2_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)
                
                T_SA    = self.CDV_T_SA_LK[l][k]   
                A_SA    = self.CDV_A_SA_LK[l][k]
                lcstr = self.CAV_A_SA_T_SA_LK[l][k]
                                    
                rcstr = (A_SA_UB * T_SA) + (T_SA_UB * A_SA) - (A_SA_UB * T_SA_UB)
                self.CSTR_A_SA_T_SA_2_LK[l].append(self.model.addQConstr(lcstr >= rcstr, name=name))
                                    
        self.model.update()
        logging.debug("CSTR_A_SA_T_SA_2_LK:\n %s" %self.CSTR_A_SA_T_SA_2_LK)
        
        
    def _createCSTR_A_SA_T_SA_3_LK_hasStandbyMode(self):
        T_SA_UB = self.EAMS.TEMPERATURE_SUPPLY_AIR_HIGH        
        for l in xrange(self.NUM_ROOM):
            self.CSTR_A_SA_T_SA_3_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l                                           
            for k in xrange(self.NUM_SLOT):
                name = ['CSTR_A_SA_T_SA_3_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)
                
                T_SA    = self.CDV_T_SA_LK[l][k]
                A_SA    = self.CDV_A_SA_LK[l][k]
                A_SA_LB = self._get_A_SA_LB(dl,self.CURR_K+k)
                
                lcstr = self.CAV_A_SA_T_SA_LK[l][k]
                                    
                rcstr = (A_SA_LB * T_SA) + (T_SA_UB * A_SA) - (A_SA_LB * T_SA_UB)
                self.CSTR_A_SA_T_SA_3_LK[l].append(self.model.addQConstr(lcstr <= rcstr, name=name))
                                    
        self.model.update()
        logging.debug("CSTR_A_SA_T_SA_3_LK:\n %s" %self.CSTR_A_SA_T_SA_3_LK)
        
    def _createCSTR_A_SA_T_SA_4_LK_hasStandbyMode(self):        
        A_SA_UB = self.EAMS.MASS_AIR_FLOW_SUPPLY_AIR_MAX
        for l in xrange(self.NUM_ROOM):
            self.CSTR_A_SA_T_SA_4_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l               
                        
            for k in xrange(self.NUM_SLOT):
                name = ['CSTR_A_SA_T_SA_4_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)
                
                T_SA    = self.CDV_T_SA_LK[l][k]    
                T_SA_LB = self._get_T_SA_LB(dl,self.CURR_K+k)                   
                A_SA    = self.CDV_A_SA_LK[l][k]                    
                lcstr = self.CAV_A_SA_T_SA_LK[l][k]
                
                rcstr = (A_SA_UB * T_SA) + (T_SA_LB * A_SA) - (A_SA_UB * T_SA_LB)
                self.CSTR_A_SA_T_SA_4_LK[l].append(self.model.addQConstr(lcstr <= rcstr, name=name))
                                    
        self.model.update()
        logging.debug("CSTR_A_SA_T_SA_4_LK:\n %s" %self.CSTR_A_SA_T_SA_4_LK)   

#-----------------------------------        

    def _createCSTR_A_SA_T_z_1_LK_looseboundedT_hasStandbyMode(self):
        T_LB    = float(self.EAMS.TEMPERATURE_UNOCC_MIN)
        for l in xrange(self.NUM_ROOM):
            self.CSTR_A_SA_T_z_1_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l                               
            for k in xrange(self.NUM_SLOT):
                name = ['CSTR_A_SA_T_z_1_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)
                
                T       = self.CAV_T_LK[l][k]
                A_SA    = self.CDV_A_SA_LK[l][k]
                A_SA_LB = self._get_A_SA_LB(dl,self.CURR_K+k)                    
                lcstr = self.CAV_A_SA_T_z_LK[l][k]
                
                rcstr = (A_SA_LB * T) + (T_LB * A_SA) - (A_SA_LB * T_LB)
                self.CSTR_A_SA_T_z_1_LK[l].append(self.model.addQConstr(lcstr >= rcstr, name=name))
                        
        self.model.update()
        logging.debug("CSTR_A_SA_T_z_1_LK:\n %s" %self.CSTR_A_SA_T_z_1_LK)
        
    def _createCSTR_A_SA_T_z_2_LK_looseboundedT_hasStandbyMode(self):        
        A_SA_UB = self.EAMS.MASS_AIR_FLOW_SUPPLY_AIR_MAX
        T_UB    = float(self.EAMS.TEMPERATURE_UNOCC_MAX)        
        for l in xrange(self.NUM_ROOM):
            self.CSTR_A_SA_T_z_2_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l               
            for k in xrange(self.NUM_SLOT):
                name = ['CSTR_A_SA_T_z_2_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)
                
                T = self.CAV_T_LK[l][k]                    
                A_SA    = self.CDV_A_SA_LK[l][k]
                
                lcstr = self.CAV_A_SA_T_z_LK[l][k]
                
                rcstr = (A_SA_UB * T) + (T_UB * A_SA) - (A_SA_UB * T_UB)
                self.CSTR_A_SA_T_z_2_LK[l].append(self.model.addQConstr(lcstr >= rcstr, name=name))
                                    
        self.model.update()
        logging.debug("CSTR_A_SA_T_z_2_LK:\n %s" %self.CSTR_A_SA_T_z_2_LK)
        
        
    def _createCSTR_A_SA_T_z_3_LK_looseboundedT_hasStandbyMode(self):
        T_UB    = float(self.EAMS.TEMPERATURE_UNOCC_MAX)
        
        for l in xrange(self.NUM_ROOM):
            self.CSTR_A_SA_T_z_3_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l                               
            for k in xrange(self.NUM_SLOT):
                name = ['CSTR_A_SA_T_z_3_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)
                
                T       = self.CAV_T_LK[l][k]
                A_SA    = self.CDV_A_SA_LK[l][k]
                A_SA_LB = self._get_A_SA_LB(dl,self.CURR_K+k)
                
                lcstr = self.CAV_A_SA_T_z_LK[l][k]
                
                rcstr = (A_SA_LB * T) + (T_UB * A_SA) - (A_SA_LB * T_UB)
                self.CSTR_A_SA_T_z_3_LK[l].append(self.model.addQConstr(lcstr <= rcstr, name=name))
                                    
        self.model.update()
        logging.debug("CSTR_A_SA_T_z_3_LK:\n %s" %self.CSTR_A_SA_T_z_3_LK)
        
    def _createCSTR_A_SA_T_z_4_LK_looseboundedT_hasStandbyMode(self):        
        A_SA_UB = self.EAMS.MASS_AIR_FLOW_SUPPLY_AIR_MAX
        T_LB    = float(self.EAMS.TEMPERATURE_UNOCC_MIN)        
        for l in xrange(self.NUM_ROOM):
            self.CSTR_A_SA_T_z_4_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l               
            for k in xrange(self.NUM_SLOT):
                name = ['CSTR_A_SA_T_z_4_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)
                
                T       = self.CAV_T_LK[l][k]
                A_SA    = self.CDV_A_SA_LK[l][k]                    
                lcstr = self.CAV_A_SA_T_z_LK[l][k]
                
                rcstr = (A_SA_UB * T) + (T_LB * A_SA) - (A_SA_UB * T_LB)
                self.CSTR_A_SA_T_z_4_LK[l].append(self.model.addQConstr(lcstr <= rcstr, name=name))
                    
                                    
        self.model.update()
        logging.debug("CSTR_A_SA_T_z_4_LK:\n %s" %self.CSTR_A_SA_T_z_4_LK)
        
        
    #===========================================================================
    # Constraints: No Standby Mode
    #===========================================================================
    def _createCSTR_SupplyAirTemperature_LB_noStandbyMode(self):
        for l in xrange(self.NUM_ROOM):        
            self.CSTR_T_SA_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l               
            for k in xrange(self.NUM_SLOT):                
                name = ['CSTR_T_SA_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)         
                lcstr = self.CDV_T_SA_LK[l][k]

                if self.EAMS.SH[self.CURR_K+k] == 1:
                    rcstr = float(self.EAMS.TEMPERATURE_CONDITIONED_AIR)
                    self.CSTR_T_SA_LK[l].append(self.model.addConstr(lcstr >= rcstr, name))
                else:
                    self.CSTR_T_SA_LK[l].append(self.model.addConstr(lcstr == 0, name))
             
        self.model.update()
        logging.debug("CSTR_T_SA_LK:\n %s" %self.CSTR_T_SA_LK)
        
    def _createCSTR_SupplyAirFlowRate_LB_noStandbyMode(self):
        """For each location at each timestep, create a constraint for lower bound of air mass flow rate"""
        
        for l in xrange(self.NUM_ROOM):
            self.CSTR_A_SA_LB_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l               
            for k in xrange(self.NUM_SLOT):                
                name = ['CSTR_A_SA_LB_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)                
                
                lcstr = self.CDV_A_SA_LK[l][k]
                rcstr = self._get_A_SA_LB(dl,self.CURR_K+k)
                
                if self.EAMS.SH[self.CURR_K+k] == 1:                    
                    self.CSTR_A_SA_LB_LK[l].append(self.model.addConstr(lcstr >= rcstr, name))
                else:
                    self.CSTR_A_SA_LB_LK[l].append(self.model.addConstr(lcstr == rcstr, name))
                    
        self.model.update()
        logging.debug("CSTR_A_SA_LB_LK:\n %s" %self.CSTR_A_SA_LB_LK)
        
#-----------------------------------
        
    def _createCSTR_A_SA_T_SA_1_LK_noStandbyMode(self):
        T_SA_LB = float(self.EAMS.TEMPERATURE_CONDITIONED_AIR)
        for l in xrange(self.NUM_ROOM):
            self.CSTR_A_SA_T_SA_1_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l   
            for k in xrange(self.NUM_SLOT):
                name = ['CSTR_A_SA_T_SA_1_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)
                
                T_SA    = self.CDV_T_SA_LK[l][k]
                A_SA    = self.CDV_A_SA_LK[l][k]
                A_SA_LB = self._get_A_SA_LB(dl,self.CURR_K+k)
                lcstr = self.CAV_A_SA_T_SA_LK[l][k]
                
                if self.EAMS.SH[self.CURR_K+k] == 1:
                    rcstr = (A_SA_LB * T_SA) + (T_SA_LB * A_SA) - (A_SA_LB * T_SA_LB)
                    self.CSTR_A_SA_T_SA_1_LK[l].append(self.model.addQConstr(lcstr >= rcstr, name=name))
                else:
                    self.CSTR_A_SA_T_SA_1_LK[l].append(self.model.addQConstr(lcstr == 0, name=name))
                                    
        self.model.update()
        logging.debug("CSTR_A_SA_T_SA_1_LK:\n %s" %self.CSTR_A_SA_T_SA_1_LK)
        
    def _createCSTR_A_SA_T_SA_2_LK_noStandbyMode(self):
        A_SA_UB = self.EAMS.MASS_AIR_FLOW_SUPPLY_AIR_MAX
        T_SA_UB = self.EAMS.TEMPERATURE_SUPPLY_AIR_HIGH
        
        for l in xrange(self.NUM_ROOM):
            self.CSTR_A_SA_T_SA_2_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l   
            for k in xrange(self.NUM_SLOT):
                name = ['CSTR_A_SA_T_SA_2_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)
                
                T_SA    = self.CDV_T_SA_LK[l][k]   
                A_SA    = self.CDV_A_SA_LK[l][k]                    
                lcstr = self.CAV_A_SA_T_SA_LK[l][k]
                
                if self.EAMS.SH[self.CURR_K+k] == 1:
                    rcstr = (A_SA_UB * T_SA) + (T_SA_UB * A_SA) - (A_SA_UB * T_SA_UB)
                    self.CSTR_A_SA_T_SA_2_LK[l].append(self.model.addQConstr(lcstr >= rcstr, name=name))
                                    
        self.model.update()
        logging.debug("CSTR_A_SA_T_SA_2_LK:\n %s" %self.CSTR_A_SA_T_SA_2_LK)
        
        
    def _createCSTR_A_SA_T_SA_3_LK_noStandbyMode(self):
        T_SA_UB = self.EAMS.TEMPERATURE_SUPPLY_AIR_HIGH
        for l in xrange(self.NUM_ROOM):
            self.CSTR_A_SA_T_SA_3_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l   
            for k in xrange(self.NUM_SLOT):
                name = ['CSTR_A_SA_T_SA_3_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)
                
                T_SA    = self.CDV_T_SA_LK[l][k]
                A_SA    = self.CDV_A_SA_LK[l][k]
                A_SA_LB = self._get_A_SA_LB(dl,self.CURR_K+k)                    
                lcstr = self.CAV_A_SA_T_SA_LK[l][k]
                
                if self.EAMS.SH[self.CURR_K+k] == 1:
                    rcstr = (A_SA_LB * T_SA) + (T_SA_UB * A_SA) - (A_SA_LB * T_SA_UB)
                    self.CSTR_A_SA_T_SA_3_LK[l].append(self.model.addQConstr(lcstr <= rcstr, name=name))
                                    
        self.model.update()
        logging.debug("CSTR_A_SA_T_SA_3_LK:\n %s" %self.CSTR_A_SA_T_SA_3_LK)
        
    def _createCSTR_A_SA_T_SA_4_LK_noStandbyMode(self):        
        A_SA_UB = self.EAMS.MASS_AIR_FLOW_SUPPLY_AIR_MAX
        T_SA_LB = float(self.EAMS.TEMPERATURE_CONDITIONED_AIR)         
        for l in xrange(self.NUM_ROOM):
            self.CSTR_A_SA_T_SA_4_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l   
            for k in xrange(self.NUM_SLOT):
                name = ['CSTR_A_SA_T_SA_4_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)
                
                T_SA    = self.CDV_T_SA_LK[l][k]                       
                A_SA    = self.CDV_A_SA_LK[l][k]                    
                lcstr = self.CAV_A_SA_T_SA_LK[l][k]
                
                if self.EAMS.SH[self.CURR_K+k] == 1:
                    rcstr = (A_SA_UB * T_SA) + (T_SA_LB * A_SA) - (A_SA_UB * T_SA_LB)
                    self.CSTR_A_SA_T_SA_4_LK[l].append(self.model.addQConstr(lcstr <= rcstr, name=name))
                                    
        self.model.update()
        logging.debug("CSTR_A_SA_T_SA_4_LK:\n %s" %self.CSTR_A_SA_T_SA_4_LK)   
        
#---------------------------------------
    def _createCSTR_A_SA_T_z_1_LK_looseboundedT_noStandbyMode(self):   
        T_LB    = float(self.EAMS.TEMPERATURE_UNOCC_MIN)
        for l in xrange(self.NUM_ROOM):
            self.CSTR_A_SA_T_z_1_LK.append([])   
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l                                            
            for k in xrange(self.NUM_SLOT):
                name = ['CSTR_A_SA_T_z_1_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)
                
                T       = self.CAV_T_LK[l][k]
                A_SA    = self.CDV_A_SA_LK[l][k]     
                A_SA_LB = self._get_A_SA_LB(dl,self.CURR_K+k)     
                
                lcstr = self.CAV_A_SA_T_z_LK[l][k]
                
                if self.EAMS.SH[self.CURR_K+k] == 1:
                    rcstr = (A_SA_LB * T) + (T_LB * A_SA) - (A_SA_LB * T_LB)
                    self.CSTR_A_SA_T_z_1_LK[l].append(self.model.addQConstr(lcstr >= rcstr, name=name))
                else:
                    self.CSTR_A_SA_T_z_1_LK[l].append(self.model.addQConstr(lcstr == 0, name=name))
                        
        self.model.update()
        logging.debug("CSTR_A_SA_T_z_1_LK:\n %s" %self.CSTR_A_SA_T_z_1_LK)
        
    def _createCSTR_A_SA_T_z_2_LK_looseboundedT_noStandbyMode(self):
        
        A_SA_UB = self.EAMS.MASS_AIR_FLOW_SUPPLY_AIR_MAX
        T_UB    = float(self.EAMS.TEMPERATURE_UNOCC_MAX)
        
        for l in xrange(self.NUM_ROOM):
            self.CSTR_A_SA_T_z_2_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l               
            for k in xrange(self.NUM_SLOT):
                name = ['CSTR_A_SA_T_z_2_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)
                
                T = self.CAV_T_LK[l][k]                    
                A_SA    = self.CDV_A_SA_LK[l][k]
                
                lcstr = self.CAV_A_SA_T_z_LK[l][k]
                
                if self.EAMS.SH[self.CURR_K+k] == 1:
                    rcstr = (A_SA_UB * T) + (T_UB * A_SA) - (A_SA_UB * T_UB)
                    self.CSTR_A_SA_T_z_2_LK[l].append(self.model.addQConstr(lcstr >= rcstr, name=name))
                                    
        self.model.update()
        logging.debug("CSTR_A_SA_T_z_2_LK:\n %s" %self.CSTR_A_SA_T_z_2_LK)
        
        
    def _createCSTR_A_SA_T_z_3_LK_looseboundedT_noStandbyMode(self):
        T_UB    = float(self.EAMS.TEMPERATURE_UNOCC_MAX)
        
        for l in xrange(self.NUM_ROOM):
            self.CSTR_A_SA_T_z_3_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l               
            for k in xrange(self.NUM_SLOT):
                name = ['CSTR_A_SA_T_z_3_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)
                
                T       = self.CAV_T_LK[l][k]
                A_SA    = self.CDV_A_SA_LK[l][k]
                A_SA_LB = self._get_A_SA_LB(dl,self.CURR_K+k)
                lcstr = self.CAV_A_SA_T_z_LK[l][k]
                
                if self.EAMS.SH[self.CURR_K+k] == 1:
                    rcstr = (A_SA_LB * T) + (T_UB * A_SA) - (A_SA_LB * T_UB)
                    self.CSTR_A_SA_T_z_3_LK[l].append(self.model.addQConstr(lcstr <= rcstr, name=name))
                                    
        self.model.update()
        logging.debug("CSTR_A_SA_T_z_3_LK:\n %s" %self.CSTR_A_SA_T_z_3_LK)
        
    def _createCSTR_A_SA_T_z_4_LK_looseboundedT_noStandbyMode(self):
        
        A_SA_UB = self.EAMS.MASS_AIR_FLOW_SUPPLY_AIR_MAX
        T_LB    = float(self.EAMS.TEMPERATURE_UNOCC_MIN)
        
        for l in xrange(self.NUM_ROOM):
            self.CSTR_A_SA_T_z_4_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l               
            for k in xrange(self.NUM_SLOT):
                name = ['CSTR_A_SA_T_z_4_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)
                
                T       = self.CAV_T_LK[l][k]
                A_SA    = self.CDV_A_SA_LK[l][k]                    
                lcstr = self.CAV_A_SA_T_z_LK[l][k]
                
                if self.EAMS.SH[self.CURR_K+k] == 1:
                    rcstr = (A_SA_UB * T) + (T_LB * A_SA) - (A_SA_UB * T_LB)
                    self.CSTR_A_SA_T_z_4_LK[l].append(self.model.addQConstr(lcstr <= rcstr, name=name))
                    
                                    
        self.model.update()
        logging.debug("CSTR_A_SA_T_z_4_LK:\n %s" %self.CSTR_A_SA_T_z_4_LK)
                 
                 
    #===========================================================================
    # Constraints: Energy Consumption
    #===========================================================================
    def _createCSTR_EnergyConsumption_Fan(self):
        """For each location at each timestep, create a constraint for e_fan(k, l)"""
        
        for l in xrange(self.NUM_ROOM):
            self.CSTR_E_FAN_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l           
            for k in xrange(self.NUM_SLOT):
                name = ['CSTR_E_FAN_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)      
                
                cstr = self.EAMS.BETA_FAN_POWER_CONSTANT * self.CDV_A_SA_LK[l][k]
                
                e_fan = self.CAV_E_FAN_LK[l][k]
                self.CSTR_E_FAN_LK[l].append(self.model.addConstr(e_fan==cstr, name))
                
        self.model.update()
        logging.debug("CSTR_E_FAN_LK:\n %s" %self.CSTR_E_FAN_LK)
        
    def _createCSTR_EnergyConsumption_Conditioning(self):
        """For each location at each timestep, create a constraint for e_conditioning(k, l)"""
        
        for l in xrange(self.NUM_ROOM):
            self.CSTR_E_CONDITIONING_LK.append([])     
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l                      
            for k in xrange(self.NUM_SLOT):               
                name = ['CSTR_E_CONDITIONING_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name)    
                
                cstr = 0
                # NOTE: only when OAT > T_CA!!
                if (float(self.EAMS.OAT.values()[self.CURR_K+k]) > float(self.EAMS.TEMPERATURE_CONDITIONED_AIR)):            
                    cstr += self.CDV_A_SA_LK[l][k] * (
                                   ((float)(self.EAMS.AIR_HEAT_CAPACITY_AT_CONSTANT_PRESSURE) * (float)(self.EAMS.OAT.values()[self.CURR_K+k])) -
                                   ((float)(self.EAMS.AIR_HEAT_CAPACITY_AT_CONSTANT_PRESSURE) * (float)(self.EAMS.TEMPERATURE_CONDITIONED_AIR))
                                   )

                e_conditioning = self.CAV_E_CONDITIONING_LK[l][k]
                self.CSTR_E_CONDITIONING_LK[l].append(self.model.addConstr(e_conditioning==cstr, name))
                
        self.model.update()
        logging.debug("CSTR_E_CONDITIONING_LK:\n %s" %self.CSTR_E_CONDITIONING_LK)
        
    def _createCSTR_EnergyConsumption_Heating(self):
        """For each location at each timestep, create a constraint for e_heating(k, l)"""
                
        for l in xrange(self.NUM_ROOM):
            self.CSTR_E_HEATING_LK.append([])
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l               
            for k in xrange(self.NUM_SLOT):                
                name = ['CSTR_E_HEATING_LK', str(dl), str(self.CURR_K+k)]
                name = '_'.join(name) 
                e_heating = self.CAV_E_HEATING_LK[l][k]
                
                cstr = (
                         (float(self.EAMS.AIR_HEAT_CAPACITY_AT_CONSTANT_PRESSURE) *
                         self.CAV_A_SA_T_SA_LK[l][k]
                         ) - 
                         (float(self.EAMS.AIR_HEAT_CAPACITY_AT_CONSTANT_PRESSURE) *
                         float(self.EAMS.TEMPERATURE_CONDITIONED_AIR) *
                         self.CDV_A_SA_LK[l][k]
                         )
                        )
   
                self.CSTR_E_HEATING_LK[l].append(self.model.addConstr(e_heating==cstr, name)) 
                    
        self.model.update()
        logging.debug("CSTR_E_HEATING_LK:\n %s" %self.CSTR_E_HEATING_LK)
        
    #===========================================================================
    # Energy Minimization Objective
    #===========================================================================
    def _createObjective(self):
        """Create an energy consumption minimization objective """
        
        self.model.modelSense = GRB.MINIMIZE
        objective = 0
        for l in xrange(self.NUM_ROOM):
            for k in xrange(self.NUM_SLOT):
                objective += self.CAV_E_FAN_LK[l][k] + self.CAV_E_CONDITIONING_LK[l][k] + self.CAV_E_HEATING_LK[l][k]
    
        self.model.setObjective(objective)
    
#             
#==================================================================
#   Results
#==================================================================   
    def _updMSTR_Schedules(self):
        self._updMSTR_BDV_x_MLK_MT()
        self._updMSTR_BAV_z_LK()        
        self._updMSTR_DAV_Attendee_LK()
    
    def _is_BDV_x_MLK_allocated(self, lk):
        return self.MSTR_SCHE.MSTR_BDV_x_MLK_MeetingMap_Reverse.has_key(lk)
                    
    def _updMSTR_BDV_x_MLK_MT(self):
        for m in xrange(len(self.BDV_x_MLK)):
            i=0
            
            if self.SCHE_MODE == 1:
                mtype_id = self.CURR_DESTROY_MTYPE[m]
            else:
                mtype_id = self.MTYPE_ID[m]
            
            for l in xrange(len(self.BDV_x_MLK[m])):
                for k in xrange(len(self.BDV_x_MLK[m][l])):
                    val = self.BDV_x_MLK[m][l][k].x
                    if val > self.EPSILON:
                        mlk = self.BDV_x_MLK_ReverseDict.get(tuple([m,l,k]))
#                         print "_is_BDV_x_MLK_allocated:", mlk[1:], " ", self._is_BDV_x_MLK_allocated(tuple(mlk[1:]))
                        if self._is_BDV_x_MLK_allocated(tuple(mlk[1:])) == False:
                            
                            if self.SCHE_MODE == 1:
                                mid = self.CURR_MTYPE_DESTROY_MID.get(mtype_id)[i]
                            else:
                                mid = self.MTYPE_MID.get(mtype_id)[i]    
#                             mkey = self.EAMS.ML[mid].Key
#                             print m, " ", l, " ", k, " ", mlk, " ", mid, " ", mkey
                            self.MSTR_SCHE.updMSTR_BDV_x_MLK_MeetingMap(mid, mlk[1:])
                            self.MSTR_SCHE.updMSTR_BAV_z_LK_OccupiedMap(mid, mlk[1:], self.EAMS.ML[mid].Duration)
                            self.MSTR_SCHE.updMSTR_Location_AllocMap(mlk[1], mlk[2], mtype_id, mid)                            
                            i += 1                        
                        
    def _updMSTR_BAV_z_LK(self):
#         print "MSTR_BAV_z_LK:"
        for l in xrange(self.NUM_ROOM):
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
                
            for k in xrange(self.NUM_SLOT):
                val = self.BAV_z_LK[l][k].x                
                if val > self.EPSILON:
                    self.MSTR_SCHE.MSTR_BAV_z_LK[dl][self.CURR_K+k] = 1                    
                else:
                    self.MSTR_SCHE.MSTR_BAV_z_LK[dl][self.CURR_K+k] = 0
                    
                        
    def _updMSTR_DAV_Attendee_LK(self):
#         print "MSTR_DAV_Attendee_LK:"
        for l in xrange(self.NUM_ROOM):
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
            
            for k in xrange(self.NUM_SLOT):
                val = self.DAV_Attendee_LK[l][k].x
                if val > self.EPSILON:
                    self.MSTR_SCHE.MSTR_DAV_Attendee_LK[dl][self.CURR_K+k] = self.DAV_Attendee_LK[l][k].x
#                     print l, " ", self.CURR_K+k, "=",  self.MSTR_SCHE.MSTR_DAV_Attendee_LK[l][self.CURR_K+k]
                else:
                    self.MSTR_SCHE.MSTR_DAV_Attendee_LK[dl][self.CURR_K+k] = 0
                      
    def _updMSTR_HVAC(self):
        if self.EAMS.STANDBY_MODE == '1':
            self._updMSTR_BDV_w_LK()
        self._updMSTR_CDV_T_SA_LK()
        self._updMSTR_CDV_A_SA_LK()
        self._updMSTR_CAV_T_LK()
        self._updMSTR_CAV_E_FAN_LK()
        self._updMSTR_CAV_E_CONDITIONING_LK()
        self._updMSTR_CAV_E_HEATING_LK() 
        self._updMSTR_CAV_Tz_LK() 
        self._updMSTR_AuxHVAC()
        
    def _updMSTR_AuxHVAC(self):
        pass

    def _updMSTR_BDV_w_LK(self):
        for l in xrange(self.NUM_ROOM):
            for k in xrange(len(self.BDV_w_LK[l])):    
                val = self.BDV_w_LK[l][k].x
                [ll, lk] = self.BDV_w_LK_ReverseDict.get(tuple([l,k]))
                [ml, mk] = self.MSTR_SCHE.MSTR_BDV_w_LK_Dict.get(tuple([ll,lk]))
                if val > self.EPSILON:
                    self.MSTR_SCHE.MSTR_BDV_w_LK[ml][mk] = 1
                else:
                    self.MSTR_SCHE.MSTR_BDV_w_LK[ml][mk] = 0
            
    def _updMSTR_CDV_T_SA_LK(self):
        for l in xrange(self.NUM_ROOM):
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l                
            for k in xrange(self.NUM_SLOT):                
                self.MSTR_SCHE.MSTR_CDV_T_SA_LK[dl][self.CURR_K+k] = self.CDV_T_SA_LK[l][k].x
                
    def _updMSTR_CDV_A_SA_LK(self):
        for l in xrange(self.NUM_ROOM):
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
            for k in xrange(self.NUM_SLOT):                
                self.MSTR_SCHE.MSTR_CDV_A_SA_LK[dl][self.CURR_K+k] = self.CDV_A_SA_LK[l][k].x
          
    def _updMSTR_CAV_T_LK(self):
        for l in xrange(self.NUM_ROOM):
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
            for k in xrange(self.NUM_SLOT):                
                self.MSTR_SCHE.MSTR_CAV_T_LK[dl][self.CURR_K+k] = self.CAV_T_LK[l][k].x
                
    def _updMSTR_CAV_Tz_LK(self):
        for l in xrange(self.NUM_ROOM):
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
            for k in xrange(self.NUM_SLOT):   
                if self.EAMS.RNL[dl][0] == self.N_OUTDOOR:             
                    self.MSTR_SCHE.MSTR_CAV_T_l_z1_LK[dl][self.CURR_K+k] = self.CAV_T_l_z1_LK[l][k].x
                    self.MSTR_SCHE.MSTR_CAV_T_z1_l_LK[dl][self.CURR_K+k] = self.CAV_T_z1_l_LK[l][k].x
                    
                if self.EAMS.RNL[dl][1] == self.N_OUTDOOR:
                    self.MSTR_SCHE.MSTR_CAV_T_l_z2_LK[dl][self.CURR_K+k] = self.CAV_T_l_z2_LK[l][k].x
                    self.MSTR_SCHE.MSTR_CAV_T_z2_l_LK[dl][self.CURR_K+k] = self.CAV_T_z2_l_LK[l][k].x
                    
                if self.EAMS.RNL[dl][2] == self.N_OUTDOOR:
                    self.MSTR_SCHE.MSTR_CAV_T_l_z3_LK[dl][self.CURR_K+k] = self.CAV_T_l_z3_LK[l][k].x
                    self.MSTR_SCHE.MSTR_CAV_T_z3_l_LK[dl][self.CURR_K+k] = self.CAV_T_z3_l_LK[l][k].x
                        
                if self.EAMS.RNL[dl][3] == self.N_OUTDOOR:
                    self.MSTR_SCHE.MSTR_CAV_T_l_z4_LK[dl][self.CURR_K+k] = self.CAV_T_l_z4_LK[l][k].x
                    self.MSTR_SCHE.MSTR_CAV_T_z4_l_LK[dl][self.CURR_K+k] = self.CAV_T_z4_l_LK[l][k].x
                    
                self.MSTR_SCHE.MSTR_CAV_T_l_f_LK[dl][self.CURR_K+k] = self.CAV_T_l_f_LK[l][k].x
                self.MSTR_SCHE.MSTR_CAV_T_l_c_LK[dl][self.CURR_K+k] = self.CAV_T_l_c_LK[l][k].x
                                    
    def _updMSTR_CAV_E_FAN_LK(self):
        for l in xrange(self.NUM_ROOM):
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
            for k in xrange(self.NUM_SLOT):                
                self.MSTR_SCHE.MSTR_CAV_E_FAN_LK[dl][self.CURR_K+k] = self.CAV_E_FAN_LK[l][k].x
                            
    def _updMSTR_CAV_E_CONDITIONING_LK(self):
        for l in xrange(self.NUM_ROOM):
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
            for k in xrange(self.NUM_SLOT):                
                self.MSTR_SCHE.MSTR_CAV_E_CONDITIONING_LK[dl][self.CURR_K+k] = self.CAV_E_CONDITIONING_LK[l][k].x
                
    def _updMSTR_CAV_E_HEATING_LK(self):
        for l in xrange(self.NUM_ROOM):
            if self.SCHE_MODE == 1:
                dl = self.CURR_DESTROY_LOCATION[l]
            else:
                dl = l
            for k in xrange(self.NUM_SLOT):                
                self.MSTR_SCHE.MSTR_CAV_E_HEATING_LK[dl][self.CURR_K+k] = self.CAV_E_HEATING_LK[l][k].x
                
                
        
#==================================================================
#   Main API
#==================================================================    
    def solve(self):
        self._createScheduleModel()
        self._createHVACModel()      
        self._createObjective()  
        self.model.update()
        if self.LOG_LP:
            self.model.write('Output/' + self.CASECFG + '_' + str(self.CURR_K) + '.lp')          
        self.model.optimize()
         
#         if self.model.getAttr(GRB.attr.Status) == self.STATUS.index('INFEASIBLE') or self.model.getAttr(GRB.attr.Status) == self.STATUS.index('SUBOPTIMAL'):
        if self.model.getAttr(GRB.attr.Status) != self.STATUS.index('OPTIMAL') and self.model.getAttr(GRB.attr.Status) != self.STATUS.index('TIME_LIMIT'):
            logging.error("Error! Infeasible model. Status: %s" %(self.model.getAttr(GRB.attr.Status))) 
            return EAMS_Error().eams_infeasible()
        else:
            logging.info("Objective value: %g" %(self.model.getAttr(GRB.attr.ObjVal)))            
            self._updMSTR_Schedules()
            self._updMSTR_HVAC()
            return self.model.getAttr(GRB.attr.ObjVal)
        
    def diagnose(self):
        pass

#==================================================================
#   LNS: Get initial schedule
#================================================================== 
    def getInitialSchedule(self):
        logging.info("Get initial schedule...")

        # Step 1: Create schedule variables & constraints
        self._createScheduleModel()
        self._createMinRoomPerDayObjective()
        self.model.update()        
        if self.LOG_LP:
            self.model.write('Output/' + self.CASECFG + '_' + str(self.CURR_K) + '_LNS_INITSCHE_' + datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f') +'.lp')
        self.model.optimize()
                 
        # Step 5: Check model status
#         if self.STATUS.index('INFEASIBLE') != self.model.getAttr(GRB.attr.Status):
        if self.model.getAttr(GRB.attr.Status) != self.STATUS.index('OPTIMAL') and self.model.getAttr(GRB.attr.Status) != self.STATUS.index('TIME_LIMIT'):
            logging.error("Error! Infeasible initial schedule. Status: %s" %(self.model.getAttr(GRB.attr.Status)))
            return self.err.solver_lns_no_initial_solution() 
        else:
            self.hasInitialSolution = 1
            self._updMSTR_Schedules()                
                     
        return self.model.getAttr(GRB.attr.Status)
    
    def initHVACModelNEnergyObjBasedOnInitialSchedule(self):
        logging.info("Initialize HVAC model and Energy Objective, enforce scheduling constraint, optimize based on initial schedule...")
        
        # Add scheduling constraint, for initial schedule, no destroy, just enforce initial schedule cstr.
        self._createLNS_ScheduleCstr([],[],[])
        
        # Initialize HVAC model      
        self._removeMinRoomPerDayCstr()  
        self._createHVACModel()        
        # Add energy minimization objective
        self._createObjective()        
        self.model.update()
                     
        if self.LOG_LP:
            self.model.write('Output/' + self.CASECFG + '_' + str(self.CURR_K) + '_LNS_INITSCHEHVAC_' + datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f') +'.lp')
        self.model.optimize()
               
        if self.model.getAttr(GRB.attr.Status) != self.STATUS.index('OPTIMAL') and self.model.getAttr(GRB.attr.Status) != self.STATUS.index('TIME_LIMIT'):
            logging.error("Error! Infeasible HVAC model for the given initial schedule. Status: %s" %(self.model.getAttr(GRB.attr.Status)))
            return self.err.solver_lns_infeasible_hvac_ctrl()
        else:            
            self._updMSTR_HVAC()
            self.diagnose()
         
        return self.model.getAttr(GRB.attr.ObjVal)
    
    
#===========================================================================
# Room Usage Minimization (Scheduling) Objective
#===========================================================================
    def _createMinRoomPerDayObjective(self):
        """Create a scheduling objective which allocate meeting into minimum number of room per day"""
        
        self._createBAV_y_LD()        
        self._createCSTR_MinRoom()
        self._createLinearMinRoomObjective()
        
    def _removeMinRoomPerDayCstr(self):
        for m in xrange(len(self.CSTR_MinRoom)):
            for l in xrange(len(self.CSTR_MinRoom[m])):
                for k in xrange(len(self.CSTR_MinRoom[m][l])):
                    self.model.remove(self.CSTR_MinRoom[m][l][k])
                    
        for l in xrange(len(self.BAV_y_LD)):
            for d in xrange(len(self.BAV_y_LD[l])):
                self.model.remove(self.BAV_y_LD[l][d])
        
        self.model.update()
            
    def _createBAV_y_LD(self):
        """For each location at day D, create an auxiliary variable"""
        curr_k_day_from_start_day = self.EAMS.TS[self.CURR_K].day - self.EAMS.SCHEDULING_START_DATETIME.day
        
        if (self.EAMS.SCHEDULING_END_DATETIME.month == self.EAMS.TS[self.CURR_K].month) and (self.EAMS.SCHEDULING_END_DATETIME.day >= self.EAMS.TS[self.CURR_K].day):
            num_day = self.EAMS.SCHEDULING_END_DATETIME.day - self.EAMS.TS[self.CURR_K].day
        else:
            mrange = monthrange(self.EAMS.TS[self.CURR_K].year, self.EAMS.TS[self.CURR_K].month)
            num_day = self.EAMS.SCHEDULING_END_DATETIME.day + (mrange[1] - self.EAMS.TS[self.CURR_K].day)
            
        for l in xrange(self.NUM_ROOM):
            self.BAV_y_LD.append([])
            for d in xrange(num_day):
                name = ['BAV_y_LD', str(l), str(curr_k_day_from_start_day+d)]
                name = '_'.join(name)         
                self.BAV_y_LD[l].append(self.model.addVar(lb=0, ub=1, vtype=GRB.CONTINUOUS, name=name))
        
        self.model.update()
        logging.debug("BAV_y_LD:\n %s" %self.BAV_y_LD)
        
    def _getDayForSlotIdx(self, k):
        """Number of day of k fromm the starting day CURR_K"""
        if (self.EAMS.TS[self.CURR_K].month == self.EAMS.TS[k].month) and (self.EAMS.TS[k].day >= self.EAMS.TS[self.CURR_K].day):
            return self.EAMS.TS[k].day - self.EAMS.TS[self.CURR_K].day
        else:
            mrange = monthrange(self.EAMS.TS[self.CURR_K].year, self.EAMS.TS[self.CURR_K].month)
            return self.EAMS.TS[k].day + (mrange[1] - self.EAMS.TS[self.CURR_K].day)
        
        
    def _createCSTR_MinRoom(self):
        """Force meeting allocation into minimum number of room per day"""
                
        for m in xrange(self.NUM_MEETING_TYPE):
            self.CSTR_MinRoom.append([])
            mtype_id = self.MTYPE_ID[m]
            mid = self.MTYPE[m].MLS[0]
            mdur = self.EAMS.ML[mid].Duration                
            
            for l in xrange(self.NUM_ROOM):
                self.CSTR_MinRoom[m].append([])
                if l in self.EAMS.MR[m]:    # TODO: assume all meetings of the same type can access the same room. Re-group required if not!
                    for k in xrange(self.NUM_SLOT):                        
                        if (self.EAMS.isInStartTimeWindows(mid, self.CURR_K+k) > 0 and
                            self._is_K_available(mtype_id, self.CURR_K+k) and
                            self._is_LK_available(l, self.CURR_K+k, mdur)):
                            
                            day = self._getDayForSlotIdx(self.CURR_K+k) 
                            [om, ol, ok] = self.BDV_x_MLK_Dict[mtype_id, l, self.CURR_K+k]  
                            lcstr = self.BDV_x_MLK[om][ol][ok]
                            rcstr = self.BAV_y_LD[l][day] 
                            name = ['CSTR_MinRoom_MLK', str(mtype_id), str(l), str(self.CURR_K+k)]
                            name = '_'.join(name)
                            self.CSTR_MinRoom[m][l].append(self.model.addConstr(lcstr <= rcstr, name))
        
        self.model.update()
        logging.debug("CSTR_MinRoom:\n %s" %self.CSTR_MinRoom)  
        
    
    def _createLinearMinRoomObjective(self):
        """Create an objective to minimize number of room used """
        
        num_day = self.EAMS.SCHEDULING_END_DATETIME.day - self.EAMS.TS[self.CURR_K].day        
        self.model.modelSense = GRB.MINIMIZE
        objective = 0     
        
        for l in xrange(self.NUM_ROOM):
            for d in xrange(num_day):                    
                objective += self.BAV_y_LD[l][d]
                       
        self.model.setObjective(objective)
        
#==================================================================
#   LNS: Common Func
#==================================================================     
    def _createLNS_ScheduleCstr(self, locationls, slotls, mls):
        """Limit the upper bound and lower bound of x=1 which is NOT IN locationls and slotls"""
        
        self._getBDV_x_MLK_setToOne()
        for m in xrange(self.NUM_MEETING_TYPE):
            for l in xrange(len(self.BDV_x_MLK[m])):
                for k in xrange(len(self.BDV_x_MLK[m][l])):
                    [fm,fl,fk] = self.BDV_x_MLK_ReverseDict.get(tuple([m,l,k]))
                      
                    # Add constraint on x=1 which is NOT TO BE destroyed in the current round
                    if (self.BDV_x_MLK[m][l][k].getAttr("LB") == 0.0 and
                        [fm,fl,fk] in self.milp_alloc and
                        fl not in locationls and
                        fk not in slotls and
                        [fm, fl,fk] not in mls):
                        self.BDV_x_MLK[m][l][k].setAttr("LB", 1.0)
                                
        self.model.update()
        
    def _getBDV_x_MLK_setToOne(self):
        logging.info("------------------- _getBDV_x_MLK_setToOne  Identify x=1")
        self.milp_alloc = []
        self.milp_alloc_sl = []
        self.milp_alloc_sk = []
        for m in xrange(self.NUM_MEETING_TYPE):
            for l in xrange(len(self.BDV_x_MLK[m])):
                for k in xrange(len(self.BDV_x_MLK[m][l])):
                    val = self.BDV_x_MLK[m][l][k].x                    
                    if val > self.EPSILON:
                        [fm,fl,fk] = self.BDV_x_MLK_ReverseDict.get(tuple([m,l,k]))
                        self.milp_alloc.append([fm,fl,fk])
                        if fl not in self.milp_alloc_sl:
                            self.milp_alloc_sl.append(fl)
                        if fk not in self.milp_alloc_sk:
                            self.milp_alloc_sk.append(fk) 
        logging.info("[fm, fl, fk]: %s" %(self.milp_alloc))
        logging.info("[fl]: %s" %(self.milp_alloc_sl))
        logging.info("[fk]: %s" %(self.milp_alloc_sk))
            
    def updateGurobiParam(self, TIME_LIMIT):
        """Set Gurobi param which apply to non-initial solution"""
                        
        if TIME_LIMIT > 0:
            self.TIME_LIMIT = TIME_LIMIT
#             self.model.setParam(GRB.Param.TimeLimit, TIME_LIMIT) 
            logging.info("Update GRB.Param.TimeLimit to %f" %(self.TIME_LIMIT) )
                            
#==================================================================
#   LNS: Rebuild
#==================================================================
    
    def rebuildNeighbourhood(self, runidx, locationls, slotls, mls): 
        self._getAllocMeetingsInLocation(locationls)
        
        if len(self.CURR_DESTROY_MTYPE) == 0:  # No meeting was scheduled in these rooms
            return self.err.solver_lns_no_meeting_destroy()
             
        self.SCHE_MODE = 1
        self._resetGurobi(runidx)  
        self._reset_constant_for_partial_destroy()
                   
        self._createScheduleModel()
        self._createHVACModel()
        self._createObjective()
        self.model.update()
        if self.LOG_LP:
            self.model.write('Output/' + self.CASECFG + '_' + str(self.CURR_K) + '_LNS_RUN_' + str(runidx) + '_' + datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f') +'.lp')            
        self.model.optimize()
          
          
        if self.model.getAttr(GRB.attr.Status) != self.STATUS.index('OPTIMAL') and self.model.getAttr(GRB.attr.Status) != self.STATUS.index('TIME_LIMIT'):
            logging.error("Error! Infeasible partial schedule. Status: %s" %(self.model.getAttr(GRB.attr.Status))) 
            return self.err.solver_lns_infeasible_partial_schedule()    
        else:
            logging.info("runidx: %s  Objective value: %g" %(runidx, self.model.getAttr(GRB.attr.ObjVal)))
            return self.model.getAttr(GRB.attr.ObjVal)
             
        
    def _getAllocMeetingsInLocation(self, locationls):         
#         logging.info("-------------------------------------")
#         self.MSTR_SCHE.diagnose()
#         logging.info("-------------------------------------") 
        self.CURR_DESTROY_LOCATION = locationls        
        self.CURR_DESTROY_MTYPE = []
        self.CURR_DESTROY_MTYPE_NUM = []
        self.CURR_MTYPE_DESTROY_MID = {}
        
        self.DESTROY_MSTR_BDV_x_MLK_MeetingMap = {}
        self.DESTROY_MSTR_BDV_x_MLK_MeetingMap_Reverse = {}
        self.DESTROY_MSTR_BDV_x_MLK_MeetingMap_ReverseK = {}
        self.DESTROY_MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse = {}
        self.DESTROY_MSTR_Location_AllocMap = {}
        self._init_destroyAuxHVAC()
                
        for l in self.CURR_DESTROY_LOCATION:
            alloc = self.MSTR_SCHE.MSTR_Location_AllocMap[l]
            self.DESTROY_MSTR_Location_AllocMap[l] = copy.copy(alloc)
            for k, mtype, mid in alloc:
                if (k >= self.CURR_K and
                    mtype in self.MTYPE_ID
                    ):
                    if mtype in self.CURR_DESTROY_MTYPE:
                        idx = self.CURR_DESTROY_MTYPE.index(mtype)
                        self.CURR_DESTROY_MTYPE_NUM[idx] += 1
                        self.CURR_MTYPE_DESTROY_MID[mtype].append(mid)
                    else:
                        self.CURR_DESTROY_MTYPE.append(mtype)
                        self.CURR_DESTROY_MTYPE_NUM.append(1)
                        self.CURR_MTYPE_DESTROY_MID[mtype] = [mid]
                                      
                    self._remMSTRCopy(mid) 
                                              
                                        
        logging.info("CURR_DESTROY_MTYPE: %s" %(self.CURR_DESTROY_MTYPE))
        logging.info("CURR_DESTROY_MTYPE_NUM: %s" %(self.CURR_DESTROY_MTYPE_NUM))
        logging.info("CURR_MTYPE_DESTROY_MID: %s" %(self.CURR_MTYPE_DESTROY_MID))
                            
        logging.info("DESTROY_MSTR_BDV_x_MLK_MeetingMap : %s" %(self.DESTROY_MSTR_BDV_x_MLK_MeetingMap))
        logging.info("DESTROY_MSTR_BDV_x_MLK_MeetingMap_Reverse : %s" %(self.DESTROY_MSTR_BDV_x_MLK_MeetingMap_Reverse))
        logging.info("DESTROY_MSTR_BDV_x_MLK_MeetingMap_ReverseK : %s" %(self.DESTROY_MSTR_BDV_x_MLK_MeetingMap_ReverseK))
        logging.info("DESTROY_MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse : %s" %(self.DESTROY_MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse))
        logging.info("DESTROY_MSTR_Location_AllocMap : %s" %(self.DESTROY_MSTR_Location_AllocMap))
        self._diagAuxHVAC()
#         logging.info("-------------------------------------")
#         self.MSTR_SCHE.diagnose()
#         logging.info("-------------------------------------")
        
                
    
    def _remMSTRCopy(self, mid):        
#         MSTR_BDV_x_MLK_MeetingMap: {1: [2, 453], 2: [3, 453]}
        if self.MSTR_SCHE.MSTR_BDV_x_MLK_MeetingMap.get(mid) is None:
            logging.error("mid %d missing in MSTR_SCHE.MSTR_BDV_x_MLK_MeetingMap %s" %(mid, self.MSTR_SCHE.MSTR_BDV_x_MLK_MeetingMap))
            
        [l, k] = self.MSTR_SCHE.MSTR_BDV_x_MLK_MeetingMap.get(mid)
        self.DESTROY_MSTR_BDV_x_MLK_MeetingMap[mid] = [l, k]
        del self.MSTR_SCHE.MSTR_BDV_x_MLK_MeetingMap[mid]
                
#         MSTR_BDV_x_MLK_MeetingMap_Reverse: {(2, 453): 1, (3, 453): 2}
        key = tuple([l, k])
        self.DESTROY_MSTR_BDV_x_MLK_MeetingMap_Reverse[key] = mid
        del self.MSTR_SCHE.MSTR_BDV_x_MLK_MeetingMap_Reverse[key]

#         MSTR_BDV_x_MLK_MeetingMap_ReverseK: {453: [1, 2]}
        if self.DESTROY_MSTR_BDV_x_MLK_MeetingMap_ReverseK.has_key(k):
            self.DESTROY_MSTR_BDV_x_MLK_MeetingMap_ReverseK[k].append(mid)
        else:
            self.DESTROY_MSTR_BDV_x_MLK_MeetingMap_ReverseK[k] = [mid]         
        self.MSTR_SCHE.MSTR_BDV_x_MLK_MeetingMap_ReverseK[k].remove(mid)
        if len(self.MSTR_SCHE.MSTR_BDV_x_MLK_MeetingMap_ReverseK[k]) == 0:
            del self.MSTR_SCHE.MSTR_BDV_x_MLK_MeetingMap_ReverseK[k]
                         
#         MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse: {(2, 453): 1, (2, 454): 1, (3, 454): 2, (3, 453): 2}
        duration = self.EAMS.ML[mid].Duration
        self._destroyAuxHVAC(l, k, duration)   #NOTE: need to do this before MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse is deleted below....
        for i in xrange(k, k+duration):
            key = tuple([l, i])
            self.DESTROY_MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse[key] = mid
            del self.MSTR_SCHE.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse[key]
        
        
        
    def _init_destroyAuxHVAC(self):
        pass 
    
    def _destroyAuxHVAC(self, l, k, duration):
        pass
    
    def _diagAuxHVAC(self):
        pass
        
    def _resetGurobi(self, runidx):
        self.model = Model('EAMS_'+str(self.CURR_K)+'_'+str(runidx))
        self._init_gurobi_cfg()
        
    
    def _reset_constant_for_partial_destroy(self):
        """Reset variable and constraint for new partial schedule generation every round."""
        
        logging.info("Building *PARTIAL* schedule")                       
        self.NUM_MEETING_TYPE = len(self.CURR_DESTROY_MTYPE)
        self.NUM_ROOM = len(self.CURR_DESTROY_LOCATION)
        logging.info("******************* #k = %d #r = %d  #mtype = %d" %(self.NUM_SLOT, self.NUM_ROOM, self.NUM_MEETING_TYPE))

    def getEnergyConsumption(self, locls, start_k):
        """Get the energy consumption of the location in locls from the Master Schedule"""
        e = 0
        for l in xrange(self.MSTR_SCHE.MSTR_NUM_ROOM):
            if l in locls:
                e = e + sum(self.MSTR_SCHE.MSTR_CAV_E_HEATING_LK[l][start_k:]) + sum(self.MSTR_SCHE.MSTR_CAV_E_CONDITIONING_LK[l][start_k:]) + sum(self.MSTR_SCHE.MSTR_CAV_E_FAN_LK[l][start_k:])
        return e
        
    def updateNeighbourhood(self):
        self._updMSTR_Location_AllocMap_basedOn_DestroyMap()
        self._updMSTR_Schedules()  
        self._updMSTR_HVAC()
        
        
    def _updMSTR_Location_AllocMap_basedOn_DestroyMap(self):
        for l, v in self.DESTROY_MSTR_Location_AllocMap.iteritems():
            logging.info("Updating MSTR_Location_AllocMap of location %s ... %s" %(l, v))
            if len(v) > 0:
                self.MSTR_SCHE.MSTR_Location_AllocMap[l] = []
#                 logging.info("MSTR_Location_AllocMap %s: %s" %(l, self.MSTR_SCHE.MSTR_Location_AllocMap[l]))
        logging.info("MSTR_Location_AllocMap: %s" %(self.MSTR_SCHE.MSTR_Location_AllocMap))
        
        
    def rollbackNeighbourhood(self):        
        for k, v in self.DESTROY_MSTR_BDV_x_MLK_MeetingMap.iteritems():
            self.MSTR_SCHE.MSTR_BDV_x_MLK_MeetingMap[k] = v
                    
        for k, v in self.DESTROY_MSTR_BDV_x_MLK_MeetingMap_Reverse.iteritems():
            self.MSTR_SCHE.MSTR_BDV_x_MLK_MeetingMap_Reverse[k] = v
                    
        for k, v in self.DESTROY_MSTR_BDV_x_MLK_MeetingMap_ReverseK.iteritems():
            if self.MSTR_SCHE.MSTR_BDV_x_MLK_MeetingMap_ReverseK.has_key(k):
                self.MSTR_SCHE.MSTR_BDV_x_MLK_MeetingMap_ReverseK[k].extend(v)
            else:
                self.MSTR_SCHE.MSTR_BDV_x_MLK_MeetingMap_ReverseK[k] = v
                
        for k, v in self.DESTROY_MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse.iteritems():
            self.MSTR_SCHE.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse[k] = v
            
        self._rollbackAuxHVAC()
        
    def _rollbackAuxHVAC(self):
        pass
      
        
        
        
        
        
        
        
        
        
        
            
            