import logging
import numpy as np

class Sche_Master:
    def __init__(self, ML, TS, SH, ROOM, STANDBY_MODE):
        self.ML = ML
        self.TS = TS                        # Datetime for each slot
        self.SH = SH
        self.ROOM = ROOM                    # Room name
        self.STANDBY_MODE = STANDBY_MODE    # is standby mode ON?
        
        self.MSTR_NUM_MEETING = len(ML)
        self.MSTR_NUM_SLOT = len(TS)-1      
        self.MSTR_NUM_ROOM = len(ROOM)
        
        self._initMstrScheduleVar()
        self._initMstrHVACVar()
        
    def _initMstrScheduleVar(self):                
#         self.MSTR_BDV_x_MLK = []                         # Binary Decision variable: The "Starting" slot of a meeting in Meeting x Location x Time        
        self.MSTR_BAV_z_LK = []                          # Binary Auxiliary variable: represent if location l is occupied at time k (do not care which meeting)        
        self.MSTR_DAV_Attendee_LK = []                   # Discrete Auxiliary variable: Number of attendee at room l at time k
        
        self.MSTR_BDV_x_MLK_MeetingMap = {}              # d[meeting ID] = [l,k]. Record location x starting slot for each meeting
        self.MSTR_BDV_x_MLK_MeetingMap_Reverse = {}     # d[l,k] = list of meeting assign to location x starting slot k.
        self.MSTR_BDV_x_MLK_MeetingMap_ReverseK = {}     # d[k] = list of meeting assign to slot k.
        self.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse = {}      # d[(l,k)] = list of meeting assign to location x slot k
        self.MSTR_Location_AllocMap = []                        # MSTR_Location_AllocMap[0] = [[455, 12, 1]]  Location 0 has meeting ID 1 (of MTYPE 12) starts at slot 455
        
        self.MSTR_CAV_T_SLACK_UB = {}                   # d[(l,k)] = T_SLACK_UB_LK  - the slack ratio assigned to T_UB location l at time k
        self.MSTR_CAV_T_SLACK_LB = {}                   # d[(l,k)] = T_SLACK_LB_LK  - the slack ratio assigned to T_LB location l at time k
        self.MSTR_CAV_T_MSLACK_UB = {}                   # d[(l,k)] = T_MSLACK_UB_LK  - the MSLACK ratio assigned to T_UB location l at time k
        self.MSTR_CAV_T_MSLACK_LB = {}                   # d[(l,k)] = T_MSLACK_LB_LK  - the MSLACK ratio assigned to T_LB location l at time k
        
        self._initMSTR_Location_AllocMap()
        self._initMSTR_BAV_z_LK()
        self._initMSTR_DAV_Attendee_LK()
                
    def _initMstrHVACVar(self):
        self.MSTR_CDV_T_SA_LK = []                       # Continuous Decision variable: Supply air temperature
        self.MSTR_CDV_A_SA_LK = []                       # Continuous Decision variable: air mass flow rate                
        self.MSTR_CAV_T_LK = []                          # Continuous Auxiliary variable: Room/Zone temperature        
        self.MSTR_CAV_E_FAN_LK = []                      # Auxiliary variable: Energy consumption of fan operation
        self.MSTR_CAV_E_CONDITIONING_LK = []             # Auxiliary variable: Energy consumption of conditioning operation
        self.MSTR_CAV_E_HEATING_LK = []                  # Auxiliary variable: Energy consumption of heating operation
        
        self.MSTR_CAV_T_l_z1_LK = []                     # Continuous Auxiliary variable: wall temperature from zone l to zone z1
        self.MSTR_CAV_T_l_z2_LK = []                     # Continuous Auxiliary variable: wall temperature from zone l to zone z2
        self.MSTR_CAV_T_l_z3_LK = []                     # Continuous Auxiliary variable: wall temperature from zone l to zone z3
        self.MSTR_CAV_T_l_z4_LK = []                     # Continuous Auxiliary variable: wall temperature from zone l to zone z4
        self.MSTR_CAV_T_l_f_LK  = []                     # Continuous Auxiliary variable: wall temperature from zone l to zone f
        self.MSTR_CAV_T_l_c_LK  = []                     # Continuous Auxiliary variable: wall temperature from zone l to zone c 
        self.MSTR_CAV_T_z1_l_LK = []                     # Continuous Auxiliary variable: wall temperature from zone z1 to zone l
        self.MSTR_CAV_T_z2_l_LK = []                     # Continuous Auxiliary variable: wall temperature from zone z2 to zone l
        self.MSTR_CAV_T_z3_l_LK = []                     # Continuous Auxiliary variable: wall temperature from zone z3 to zone l
        self.MSTR_CAV_T_z4_l_LK = []                     # Continuous Auxiliary variable: wall temperature from zone z4 to zone l  
        
        self._initMSTR_CDV_T_SA_LK()
        self._initMSTR_CDV_A_SA_LK()
        self._initMSTR_CAV_T_LK()
        self._initMSTR_CAV_E_FAN_LK()
        self._initMSTR_CAV_E_CONDITIONING_LK()
        self._initMSTR_CAV_E_HEATING_LK()        
        self._initMSTR_CAV_T_z_LK()
        
        if self.STANDBY_MODE == '1':
            self.MSTR_BDV_w_LK = []                          # Binary Decision variable: represent if HVAC is activated from standby mode at location l at time k            
            self.MSTR_BDV_w_LK_Dict = {}                     # d[(l,k)] = offset of (l,k) in BDV_w_LK. Record index of location x time periods
            self.MSTR_BDV_w_LK_ReverseDict = {}              # d[offset of (l,k) in BDV_w_MLK] = (l,k). Basically to avoid search by value using MSTR_BDV_w_LK_Dict
            self._initMSTR_BDV_w_LK()
    
    def _initMSTR_BDV_w_LK(self):                
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_BDV_w_LK.append([])
            mk = 0
            for k in xrange(self.MSTR_NUM_SLOT):
                if self.SH[k] == 0:
                    self.MSTR_BDV_w_LK[l].append(0)
                    self.MSTR_BDV_w_LK_Dict[tuple([l,k])] = [l,mk]
                    self.MSTR_BDV_w_LK_ReverseDict[tuple([l,mk])] = [l,k]
                    mk = mk+1
           
    def _initMSTR_Location_AllocMap(self):
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_Location_AllocMap.append([])
            
    def resetMSTR_Location_AllocMap(self):
        self.MSTR_Location_AllocMap = []
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_Location_AllocMap.append([])
            
    def _initMSTR_BAV_z_LK(self):
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_BAV_z_LK.append([])
            self.MSTR_BAV_z_LK[l] = [0] * self.MSTR_NUM_SLOT
                         
    def _initMSTR_DAV_Attendee_LK(self): 
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_DAV_Attendee_LK.append([])
            self.MSTR_DAV_Attendee_LK[l] = [0] * self.MSTR_NUM_SLOT
                
    def _initMSTR_CDV_T_SA_LK(self):
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_CDV_T_SA_LK.append([])
            self.MSTR_CDV_T_SA_LK[l] = [0] * self.MSTR_NUM_SLOT
                
    def _initMSTR_CDV_A_SA_LK(self):
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_CDV_A_SA_LK.append([])
            self.MSTR_CDV_A_SA_LK[l] = [0] * self.MSTR_NUM_SLOT
          
    def _initMSTR_CAV_T_LK(self):
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_CAV_T_LK.append([])
            self.MSTR_CAV_T_LK[l] = [0] * self.MSTR_NUM_SLOT
            
    def _initMSTR_CAV_T_z_LK(self):
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_CAV_T_l_z1_LK.append([])
            self.MSTR_CAV_T_l_z1_LK[l] = [0] * self.MSTR_NUM_SLOT
            
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_CAV_T_l_z2_LK.append([])
            self.MSTR_CAV_T_l_z2_LK[l] = [0] * self.MSTR_NUM_SLOT
            
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_CAV_T_l_z3_LK.append([])
            self.MSTR_CAV_T_l_z3_LK[l] = [0] * self.MSTR_NUM_SLOT
            
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_CAV_T_l_z4_LK.append([])
            self.MSTR_CAV_T_l_z4_LK[l] = [0] * self.MSTR_NUM_SLOT
            
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_CAV_T_l_f_LK.append([])
            self.MSTR_CAV_T_l_f_LK[l] = [0] * self.MSTR_NUM_SLOT
            
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_CAV_T_l_c_LK.append([])
            self.MSTR_CAV_T_l_c_LK[l] = [0] * self.MSTR_NUM_SLOT
            
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_CAV_T_z1_l_LK.append([])
            self.MSTR_CAV_T_z1_l_LK[l] = [0] * self.MSTR_NUM_SLOT
            
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_CAV_T_z2_l_LK.append([])
            self.MSTR_CAV_T_z2_l_LK[l] = [0] * self.MSTR_NUM_SLOT
            
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_CAV_T_z3_l_LK.append([])
            self.MSTR_CAV_T_z3_l_LK[l] = [0] * self.MSTR_NUM_SLOT
            
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_CAV_T_z4_l_LK.append([])
            self.MSTR_CAV_T_z4_l_LK[l] = [0] * self.MSTR_NUM_SLOT     
            
    def _initMSTR_CAV_E_FAN_LK(self):
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_CAV_E_FAN_LK.append([])
            self.MSTR_CAV_E_FAN_LK[l] = [0] * self.MSTR_NUM_SLOT
                            
    def _initMSTR_CAV_E_CONDITIONING_LK(self):
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_CAV_E_CONDITIONING_LK.append([])
            self.MSTR_CAV_E_CONDITIONING_LK[l] = [0] * self.MSTR_NUM_SLOT
                
    def _initMSTR_CAV_E_HEATING_LK(self):
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_CAV_E_HEATING_LK.append([])
            self.MSTR_CAV_E_HEATING_LK[l] = [0] * self.MSTR_NUM_SLOT
    
#==================================================================
#   API
#==================================================================      
    def updMSTR_BDV_x_MLK_MeetingMap(self, mid, lk):
        self.MSTR_BDV_x_MLK_MeetingMap[mid] = lk
        self.MSTR_BDV_x_MLK_MeetingMap_Reverse[tuple(lk)] = mid
        
        k = lk[1]
        if k not in self.MSTR_BDV_x_MLK_MeetingMap_ReverseK:
            self.MSTR_BDV_x_MLK_MeetingMap_ReverseK[k] = [mid]
        else:
            self.MSTR_BDV_x_MLK_MeetingMap_ReverseK[k].append(mid) 
        
    def getMSTR_BDV_x_MLK_After_K(self, k):
#         print "has: ", k, " ", self.MSTR_BDV_x_MLK_MeetingMap_ReverseK.has_key(k)
        if self.MSTR_BDV_x_MLK_MeetingMap_ReverseK.has_key(k):
            return self.MSTR_BDV_x_MLK_MeetingMap_ReverseK[k]
        
    def updMSTR_BAV_z_LK_OccupiedMap(self, mid, lk, d):
        l = lk[0]
        start_k = lk[1]
        for i in xrange(d):
            self.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse[tuple([l, start_k+i])] = mid
            
    def updMSTR_Location_AllocMap(self, l, k, mtype, mid):
        logging.debug("Updating [%s, %s, %s] to location %s" %(k, mtype, mid, l))
        self.MSTR_Location_AllocMap[l].append([k, mtype, mid])        
                
    def updMSTR_CAV_T_SLACK_LK_SlackMap(self, l, k, ub_slack, lb_slack):
        self.MSTR_CAV_T_SLACK_UB[tuple([l, k])] = ub_slack
        self.MSTR_CAV_T_SLACK_LB[tuple([l, k])] = lb_slack
        
    def updMSTR_CAV_T_MSLACK_MK_SlackMap(self, m, k, ub_mslack, lb_mslack):
        self.MSTR_CAV_T_MSLACK_UB[tuple([m, k])] = ub_mslack
        self.MSTR_CAV_T_MSLACK_LB[tuple([m, k])] = lb_mslack
                                        
    def calcEnergyConsumption(self, interval):
        KJ_TO_KWh = 0.000277777778
        self.MSTR_fan_energy_kWh = []
        self.MSTR_cond_energy_kWh = []
        self.MSTR_heat_energy_kWh = []
        self.MSTR_energy_kWh = []
        self.MSTR_power = []        
        
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_fan_energy_kWh.append([])
            self.MSTR_cond_energy_kWh.append([])
            self.MSTR_heat_energy_kWh.append([])
            self.MSTR_energy_kWh.append([])
            self.MSTR_power.append([])
            for k in xrange(self.MSTR_NUM_SLOT):
                self.MSTR_fan_energy_kWh[l].append(self.MSTR_CAV_E_FAN_LK[l][k] * interval * 60 * KJ_TO_KWh)
                self.MSTR_cond_energy_kWh[l].append(self.MSTR_CAV_E_CONDITIONING_LK[l][k] * interval * 60 * KJ_TO_KWh)
                self.MSTR_heat_energy_kWh[l].append(self.MSTR_CAV_E_HEATING_LK[l][k] * interval * 60 * KJ_TO_KWh)
                
                self.MSTR_power[l].append(self.MSTR_CAV_E_FAN_LK[l][k] + self.MSTR_CAV_E_CONDITIONING_LK[l][k] + self.MSTR_CAV_E_HEATING_LK[l][k])
                self.MSTR_energy_kWh[l].append(self.MSTR_fan_energy_kWh[l][k] + self.MSTR_cond_energy_kWh[l][k]  + self.MSTR_heat_energy_kWh[l][k])
                
                                
    def calcHeatGain(self, eams):
        self.MSTR_Q_PEOPLE = []
        self.MSTR_Q_SOLAR = []
        
        for l in xrange(self.MSTR_NUM_ROOM):
            self.MSTR_Q_PEOPLE.append([])
            self.MSTR_Q_SOLAR.append([])
            
            for k in xrange(self.MSTR_NUM_SLOT):
                self.MSTR_Q_PEOPLE[l].append(self.MSTR_DAV_Attendee_LK[l][k] * eams.OCCUPANT_SENSIBLE_HEAT_GAIN)
                self.MSTR_Q_SOLAR[l].append(eams.getRoomSolarGain(k,l,0))
                
            
    def calcThermalComfortViolation(self, min_occupied_comfort_temperature, max_occupied_comfort_temperature):
        occupied = self.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse.keys()        
        self.MSTR_comfort_violation = 0
        self.MSTR_max_comfort_violation = -999
        diff = 0
        for lk in occupied:
            [l,k] = list(lk)
            logging.info("[%s][%s]: %s" %(l,k,self.MSTR_CAV_T_LK[l][k]))
            if float(self.MSTR_CAV_T_LK[l][k]) < float(min_occupied_comfort_temperature):
                diff = min_occupied_comfort_temperature-self.MSTR_CAV_T_LK[l][k]
                self.MSTR_comfort_violation += diff
            elif float(self.MSTR_CAV_T_LK[l][k]) > float(max_occupied_comfort_temperature):
                diff = self.MSTR_CAV_T_LK[l][k]-max_occupied_comfort_temperature
                self.MSTR_comfort_violation += diff
            
            if diff > self.MSTR_max_comfort_violation:
                self.MSTR_max_comfort_violation = diff

                
                
    def diagnose(self):
#         logging.info("Energy consumption: %f" %round(np.sum(self.MSTR_energy_kWh),2))
        logging.info("MSTR_BDV_x_MLK_MeetingMap: %s" %self.MSTR_BDV_x_MLK_MeetingMap)
        logging.info("MSTR_BDV_x_MLK_MeetingMap_Reverse: %s" %self.MSTR_BDV_x_MLK_MeetingMap_Reverse)
        logging.info("MSTR_BDV_x_MLK_MeetingMap_ReverseK: %s" %self.MSTR_BDV_x_MLK_MeetingMap_ReverseK)
        logging.info("MSTR_Location_AllocMap: %s" %self.MSTR_Location_AllocMap)
        logging.info("MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse: %s" %self.MSTR_BAV_z_LK_MeetingOccupiedMap_Reverse)
         
        logging.info("MSTR_CAV_T_SLACK_UB (LK): %s" %self.MSTR_CAV_T_SLACK_UB)
        logging.info("MSTR_CAV_T_SLACK_LB (LK): %s" %self.MSTR_CAV_T_SLACK_LB)
        logging.info("MSTR_CAV_T_MSLACK_UB (MK): %s" %self.MSTR_CAV_T_MSLACK_UB)
        logging.info("MSTR_CAV_T_MSLACK_LB (MK): %s" %self.MSTR_CAV_T_MSLACK_LB)
         
        logging.info("MSTR_BAV_z_LK: %s" %self.MSTR_BAV_z_LK)
        logging.info("MSTR_DAV_Attendee_LK: %s" %self.MSTR_DAV_Attendee_LK)
        
        logging.info("MSTR_CAV_T_LK: %s" %self.MSTR_CAV_T_LK)
        logging.info("MSTR_CDV_T_SA_LK: %s" %self.MSTR_CDV_T_SA_LK)
        logging.info("MSTR_CDV_A_SA_LK: %s" %self.MSTR_CDV_A_SA_LK)
                                            
        self.calcEnergyConsumption(30)
        logging.info("MSTR_energy_kWh: %s" %self.MSTR_energy_kWh)
            
        
        
        
        