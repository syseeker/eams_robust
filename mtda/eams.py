import sys
import logging
from datetime import datetime
from configobj import ConfigObj, ConfigObjError

from eams_error import EAMS_Error
from eams_meeting import Meeting
from eams_timeslot import TimeSlot
from eams_outdoor_temp import OutdoorTemperature
from eams_room_config import RoomConfig
from eams_room_thermal_config import RoomThermalCfg

class EAMS():
    def __init__(self):
        self.Z = None
        #=======================================================================
        # Zone -> Room. Eg: {'1': {'Room1': {'ZoneID': '1', 'Width': 10.0, 'Length': 6.0 ...
        #=======================================================================               
                
        self.RL = None
        #=======================================================================
        # Room list. Eg: ['Room1', 'Room3', 'Room2']
        #=======================================================================
        
        self.TS = None
        #=======================================================================
        #  Idx -> datetime. Eg: {0: datetime.datetime(2013, 1, 1, 8, 0), 1: datetime.datetime(2013, 1, 1, 8, 30), 2: datetime.datetime(2013, 1, 1, 9, 0), 3: datetime.datetime(2013, 1, 1, 9, 30), 4: datetime.datetime(2013, 1, 1, 10, 0),
        #=======================================================================
       
        self.SH = None
        #=======================================================================
        # A list follow the sequence of TS
        #=======================================================================
        
        self.ML = None
        #=======================================================================
        # List of namedtuple('Meeting_Desc', 'Key TimeWindows Duration Room Attendees')
        # [Meeting_Desc(Key='M110133', TimeWindows=[[datetime.datetime(2013, 1, 1, 9, 0), datetime.datetime(2013, 1, 1, 10, 30)], [datetime.datetime(2013, 1, 1, 12, 0), datetime.datetime(2013, 1, 1, 14, 0)], [datetime.datetime(2013, 1, 2, 14, 0), datetime.datetime(2013, 1, 2, 16, 0)]], Duration='3', Room='', Attendees=['1119', '2578', '3470', '4601', '6823', '7105', '7908', '12736', '12996', '20479']), Meeting_Desc(Key='M316335', TimeWindows=[[datetime.datetime(2013, 1, 1, 9, 0), datetime.datetime(2013, 1, 1, 18, 0)]], Duration='7', Room='', Attendees=['219', '246', '2852', '3304', '4095', '6845', '8495', '8811', '8927', '15695']), Meeting_Desc(Key='M325401', TimeWindows=[[datetime.datetime(2013, 1, 1, 9, 0), datetime.datetime(2013, 1, 1, 18, 0)]], Duration='7', Room='', Attendees=['264', '2165', '2528', '2890', '3167', '4273', '5258', '5363', '10719', '20204']), Meeting_Desc(Key='M433676', TimeWindows=[[datetime.datetime(2013, 1, 1, 9, 0), datetime.datetime(2013, 1, 1, 18, 0)]], Duration='7', Room='', Attendees=['413', '1104', '2192', '2674', '3201', '6866', '13958', '13998', '14601', '14607'])]
        #=======================================================================
        
        self.MR = None
        #=======================================================================
        # A Double array follow the sequence of self.ML
        #=======================================================================
        
        
                
        self.STANDBY_MODE = ""
        self.MEETINGS_CONFIG_DATA = ""      
        self.OUTDOOR_TEMP_DATA = ""
        self.ROOM_CONFIG_DATA = ""        
        self.SCHEDULING_START_DATETIME = "" 
        self.SCHEDULING_END_DATETIME = ""
        self.SCHEDULING_INTERVAL = -1
        self.HVAC_NON_PEAK_OFF = -1
        self.HVAC_SHUT_DOWN = ""
        self.HVAC_TURN_ON = ""    
        self.INITIAL_TEMPERATURE_MODE = -1        
        self.INITIAL_TEMPERATURE = -1      
        self.TEMPERATURE_UNOCC_MIN = -1               
        self.TEMPERATURE_OCC_COMFORT_RANGE_INCR = -1                  
        self.TEMPERATURE_UNOCC_MAX = -1          
        self.TEMPERATURE_OCC_COMFORT_RANGE_DECR = -1      
        self.TEMPERATURE_CONDITIONED_AIR = -1            
        self.TEMPERATURE_SUPPLY_AIR_HIGH = -1         
        self.ALPHA_IAQ_FACTOR_OF_SAFETY = -1                 
        self.BETA_FAN_POWER_CONSTANT = -1        
        self.AIR_HEAT_CAPACITY_AT_CONSTANT_PRESSURE = -1 
        self.MASS_AIR_FLOW_SUPPLY_AIR_MIN = -1             
        self.MASS_AIR_FLOW_SUPPLY_AIR_MAX = -1             
        self.MASS_AIR_FLOW_SUPPLY_AIR_PER_PERSON = -1      
        self.MASS_AIR_FLOW_OUTSIDE_AIR_PER_PERSON = -1   
        self.MASS_AIR_FLOW_OUTSIDE_AIR_PER_METER_SQUARE = -1 
        self.MASS_AIR_FLOW_RETURN_AIR_RATIO = -1   
        self.OCCUPANT_SENSIBLE_HEAT_GAIN = -1
        
    def _critical_err(self):
        sys.exit("Pop, Bang, Whooo, Boom... Fire Alarm! Evacuate! EAMS exit.")
        
#==================================================================
#   Problem Configurations  
#==================================================================         
    def _loadProblemConfig(self, config):
        self.STANDBY_MODE                               = config['STANDBY_MODE']
#         self.MEETINGS_CONFIG_DATA                       = config['MEETINGS_CONFIG_DATA']
        self.OUTDOOR_TEMP_DATA                          = config['OUTDOOR_TEMP_DATA'] 
        self.ROOM_CONFIG_DATA                           = config['ROOM_CONFIG_DATA']        
        self.SCHEDULING_START_DATETIME                  = datetime.strptime(config['SCHEDULING_START_DATETIME'], "%Y-%m-%d %H:%M")  
        self.SCHEDULING_END_DATETIME                    = datetime.strptime(config['SCHEDULING_END_DATETIME'], "%Y-%m-%d %H:%M")   
        self.SCHEDULING_INTERVAL                        = int(config['SCHEDULING_INTERVAL'])
        self.HVAC_NON_PEAK_OFF                          = config['HVAC_NON_PEAK_OFF']
        self.HVAC_SHUT_DOWN                             = config['HVAC_SHUT_DOWN']
        self.HVAC_TURN_ON                               = config['HVAC_TURN_ON']
        self.INITIAL_TEMPERATURE_MODE                   = config['INITIAL_TEMPERATURE_MODE']             
        self.INITIAL_TEMPERATURE                        = float(config['INITIAL_TEMPERATURE'])
        self.TEMPERATURE_UNOCC_MIN                      = float(config['TEMPERATURE_UNOCC_MIN'])
        self.TEMPERATURE_OCC_COMFORT_RANGE_INCR         = float(config['TEMPERATURE_OCC_COMFORT_RANGE_INCR'])                    
        self.TEMPERATURE_UNOCC_MAX                      = float(config['TEMPERATURE_UNOCC_MAX'])             
        self.TEMPERATURE_OCC_COMFORT_RANGE_DECR         = float(config['TEMPERATURE_OCC_COMFORT_RANGE_DECR'])      
        self.TEMPERATURE_CONDITIONED_AIR                = float(config['TEMPERATURE_CONDITIONED_AIR'])                
        self.TEMPERATURE_SUPPLY_AIR_HIGH                = float(config['TEMPERATURE_SUPPLY_AIR_HIGH'])   
        self.ALPHA_IAQ_FACTOR_OF_SAFETY                 = float(config['ALPHA_IAQ_FACTOR_OF_SAFETY'])                   
        self.BETA_FAN_POWER_CONSTANT                    = float(config['BETA_FAN_POWER_CONSTANT'])
        self.AIR_HEAT_CAPACITY_AT_CONSTANT_PRESSURE     = float(config['AIR_HEAT_CAPACITY_AT_CONSTANT_PRESSURE'])
        self.MASS_AIR_FLOW_SUPPLY_AIR_MIN               = float(config['MASS_AIR_FLOW_SUPPLY_AIR_MIN'])             
        self.MASS_AIR_FLOW_SUPPLY_AIR_MAX               = float(config['MASS_AIR_FLOW_SUPPLY_AIR_MAX'])             
        self.MASS_AIR_FLOW_SUPPLY_AIR_PER_PERSON        = float(config['MASS_AIR_FLOW_SUPPLY_AIR_PER_PERSON'])      
        self.MASS_AIR_FLOW_OUTSIDE_AIR_PER_PERSON       = float(config['MASS_AIR_FLOW_OUTSIDE_AIR_PER_PERSON'])   
        self.MASS_AIR_FLOW_OUTSIDE_AIR_PER_METER_SQUARE = float(config['MASS_AIR_FLOW_OUTSIDE_AIR_PER_METER_SQUARE']) 
        self.MASS_AIR_FLOW_RETURN_AIR_RATIO             = float(config['MASS_AIR_FLOW_RETURN_AIR_RATIO'])        
        self.OCCUPANT_SENSIBLE_HEAT_GAIN                = float(config['OCCUPANT_SENSIBLE_HEAT_GAIN'])
        logging.info("Problem configuration initialized.")
        
    def _populateProbData(self, filename, meeting_cfg):            
        ret = 0
        try:
            # Load problem configuration
            config = ConfigObj(filename, file_error=True)
            self._loadProblemConfig(config)
            
            self.MEETINGS_CONFIG_DATA = meeting_cfg
            
            # Initialize & load room, meeting, timeslot, outdoor temperature etc information
            self._populateSchedulingTimeSlot()
            self._populateHVACStdTimeslot()
            
            ret = self._populateRoomConfig()
            if ret < 0:
                raise ValueError("Invalid room configuration.")
            self._populateRoomThermalCfg() 
            
            ret = self._populateMeetingConfig()
            if ret < 0:
                raise ValueError("Invalid meeting configuration.")
            
            ret = self._populateOutdoorTemperature()
            if ret < 0:
                raise ValueError("Invalid outdoor temperature configuration.")
            
            ret = self._populateFeasibleRoomsForMeeting()
            if ret < 0:
                raise ValueError("Invalid room configuration for a meeting.")
            
            
        except (ConfigObjError, IOError), e:        
            logging.critical('%s' % (e))
            return self.err.eams_config_problem_err()
        except (ValueError), e:
            logging.critical('%s' % (e))            
        
        return ret
        
#==================================================================
#   Room Configurations  
#==================================================================  
    def _populateRoomConfig(self):
        self.RC = RoomConfig()        
        ret = self.RC.loadRoomConfig(self.ROOM_CONFIG_DATA)
        if ret == 0:  
            self.RC.populateRoomByZone()
            self.Z = self.RC.getRoomsInfoByZone("All")
            self.RL = self.RC.getRoomList()
            self.RCL = self.RC.getRoomCapaList()
            self.RNL = self.RC.getRoomNeighboursList()
            logging.debug("Get rooms: %s" %self.Z)
            logging.debug("Get roomlist: %s" %(self.RL))    
            logging.debug("Get room capa list: %s" %(self.RCL))
            logging.debug("Get room neighbours list: %s" %(self.RNL))    
        return ret   
            
    def _populateRoomThermalCfg(self):
        """Populate individual room config to be used by Gurobi"""
        
        logging.info("Populating Room Thermal Config...")            
        self.RTC = RoomThermalCfg(self.Z, self.TS)
        
        
    def _populateFeasibleRoomsForMeeting(self):
        """Does location l has the capacity to accommodate meeting midx? """   
        
        logging.info("Populate feasible rooms for meeting(s)...")
        self.MR = []
        for i in xrange(len(self.ML)):
            self.MR.append([])
            a = len(self.ML[i].Attendees)
            
            if not self.ML[i].Room:  # no preferred room            
                for j in xrange(len(self.RCL)):
                    if a <= self.RCL[j]:
                        self.MR[i].append(j)
                        
                if not self.MR[i]:
                    logging.error("No feasible room for meeting [%d]" %i) 
                    return EAMS_Error().eams_meeting_no_feasible_room()
            else: # has preferred room
                if self.ML[i].Room not in self.RL:
                    logging.critical("Preferred room [%s] for meeting [%s] does not exist in room list." %(self.ML[i].Room, self.ML[i].Key))
                    return EAMS_Error().eams_config_meeting_err()
                
                ridx = self.RL.index(self.ML[i].Room)
                if len(self.ML[i].Attendees) > self.RCL[ridx]:
                    logging.critical("Mode Config: %s. Preferred room [%s] for meeting [%s] has smaller capacity (only for %d people) than the number of attendee." %(self.MODE_CONFIG, self.ML[i].Room, self.ML[i].Key, self.RCL[ridx]))
                    return EAMS_Error().eams_config_meeting_err()
                
                self.MR[i].append(ridx)  # limit feasible room to preferred room
                
        logging.debug("Feasible rooms based on meetings' attendees and room capacity:")
        logging.debug(self.MR)    
        return 0

#==================================================================
#   TimeSlot Configurations  
#==================================================================  
    def _populateSchedulingTimeSlot(self):
        """Form timeslot based on given work week and time slot interval"""
        self.TSC = TimeSlot(self.SCHEDULING_START_DATETIME, self.SCHEDULING_END_DATETIME, (int)(self.SCHEDULING_INTERVAL))
        self.TS = self.TSC.getTimeSlots()
        logging.debug("Timeslot: %s" %self.TS) 
        logging.debug("Total number of timeslot: %d" %len(self.TS))
        
    def _populateHVACStdTimeslot(self):
        """Populate binary indicator list which denotes if the timeslot is in standard operating hour of HVAC (i.e. always on) """  
        self.SH = []
        if self.HVAC_NON_PEAK_OFF ==  '1':
            s = datetime.strptime(self.HVAC_SHUT_DOWN, "%H:%M")
            e = datetime.strptime(self.HVAC_TURN_ON, "%H:%M")
         
            for _, v in self.TS.iteritems():
                if (v.time() >= s.time() or v.time() < e.time()):
                    self.SH.append(0)  #off HVAC
                else:
                    self.SH.append(1)
        else:
            for _, v in self.TS.iteritems():
                self.SH.append(1)
                
        logging.debug("HVAC Standard Hours:\n%s" %(self.SH))

#==================================================================
#   Meeting Configurations  
#==================================================================  
    def _populateMeetingConfig(self):
        self.M = Meeting()
        ret = self.M.loadMeetings(self.MEETINGS_CONFIG_DATA)
        if ret == 0:    
            ret = self.M.populateMeetingsForRoomAllocNSchedule(self.TSC)
            if ret < 0:
                return ret
            self.ML = self.M.getMeetingsList() 
            logging.debug("Total number of meetings: %d" %(len(self.ML)))
            logging.debug(self.ML)
        return ret  

#==================================================================
#   Outdoor Temperature Configurations  
#==================================================================  
    def _populateOutdoorTemperature(self):
        self.OTC = OutdoorTemperature()
        ret = self.OTC.loadOutdoorTemperature(self.OUTDOOR_TEMP_DATA)    
        if ret == 0:
            # Populate outdoor temperature
#             self.OAT = self.OTC.getSingleDayOutdoorTemperatureShortInterval(self.SCHEDULING_START_DATETIME, self.SCHEDULING_END_DATETIME, self.SCHEDULING_INTERVAL)
            self.OAT = self.OTC.getOutdoorTemperature(self.SCHEDULING_START_DATETIME, self.SCHEDULING_END_DATETIME, self.SCHEDULING_INTERVAL)
            logging.debug("OAT: %s" %(self.OAT))
            logging.debug("len: %s" %(len(self.OAT)))
            if len(self.OAT) == 0:
                return EAMS_Error().eams_no_outdoor_temp_in_scheduling_range()
          
            # Set initial temperature is set to outdoor temperature at first slot
#             option 1: override eams_probN.cfg INITIAL_TEMPERATURE
            if self.INITIAL_TEMPERATURE_MODE == '1':
                self.INITIAL_TEMPERATURE = float(self.OAT.get(self.SCHEDULING_START_DATETIME))
                logging.debug("Initial OAT: %s" %(self.INITIAL_TEMPERATURE))
            # option 2:
            else:
                self.INITIAL_TEMPERATURE = self.INITIAL_TEMPERATURE

            logging.debug("Set Initial Temperature : %.2f" %(self.INITIAL_TEMPERATURE))        
        return ret    
        
        
#==================================================================
#     API
#==================================================================    
    def isInStartTimeWindows(self, midx, k):
        """Is k within feasible timeslot between earliest-start-time and latest-start-time? """
        d = self.ML[midx].Duration        
        for i in xrange(len(self.ML[midx].TimeWindowsOffset)):            
            tw = self.ML[midx].TimeWindowsOffset[i]
            if k >= tw[0] and  k <= (tw[1]-d+1): 
                return 1            
        return -1       
    
    def isInOngoingTimeWindows(self, midx, k):
        """Is k within feasible timeslot between earliest-start-time and latest-end-time? """
        for i in xrange(len(self.ML[midx].TimeWindowsOffset)):            
            tw = self.ML[midx].TimeWindowsOffset[i]
            if k >= tw[0] and  k <= tw[1]: 
                return 1            
        return -1   
    
    def getFeasibleStartTime(self, midx, k):
        """If meeting m starts at kp, is it still on-going at time period k?"""
        ls = []        
        d = self.ML[midx].Duration
        for i in xrange(len(self.ML[midx].TimeWindowsOffset)):
            tw = self.ML[midx].TimeWindowsOffset[i]
            if tw[0] <= k and tw[1] >= k:
                kp = tw[0]
                while kp <= tw[1]-d+1:
                    if kp not in ls and kp <= k and kp+d-1 >= k:
                        ls.append(kp)
                    kp = kp+1                
        return ls
    
    def getRoomThermalConfig(self, ridx, param):
        """API to retrieve room thermal resistance and capacitance"""
        
        if param == "C":
            return self.RTC.getRoomC(self.RL[ridx])
        
        if param == "Rij":
            return self.RTC.getRoomRij(self.RL[ridx])
        if param == "Rimj":
            return self.RTC.getRoomRimj(self.RL[ridx])
        if param == "Rji":
            return self.RTC.getRoomRji(self.RL[ridx])
        if param == "Cij":
            return self.RTC.getRoomCij(self.RL[ridx])
        if param == "Cji":
            return self.RTC.getRoomCji(self.RL[ridx])
        
        if param == "Rik":
            return self.RTC.getRoomRik(self.RL[ridx])
        if param == "Rimk":
            return self.RTC.getRoomRimk(self.RL[ridx])
        if param == "Rki":
            return self.RTC.getRoomRki(self.RL[ridx])
        if param == "Cik":
            return self.RTC.getRoomCik(self.RL[ridx])
        if param == "Cki":
            return self.RTC.getRoomCki(self.RL[ridx])
        
        if param == "Ril":
            return self.RTC.getRoomRil(self.RL[ridx])
        if param == "Riml":
            return self.RTC.getRoomRiml(self.RL[ridx])
        if param == "Rli":
            return self.RTC.getRoomRli(self.RL[ridx])
        if param == "Cil":
            return self.RTC.getRoomCil(self.RL[ridx])
        if param == "Cli":
            return self.RTC.getRoomCli(self.RL[ridx])
        
        if param == "Rio":
            return self.RTC.getRoomRio(self.RL[ridx])
        if param == "Rimo":
            return self.RTC.getRoomRimo(self.RL[ridx])
        if param == "Roi":
            return self.RTC.getRoomRoi(self.RL[ridx])
        if param == "Cio":
            return self.RTC.getRoomCio(self.RL[ridx])
        if param == "Coi":
            return self.RTC.getRoomCoi(self.RL[ridx])
        
        if param == "Rif":
            return self.RTC.getRoomRif(self.RL[ridx])
        if param == "Rfi":
            return self.RTC.getRoomRfi(self.RL[ridx])
        if param == "Cif":
            return self.RTC.getRoomCif(self.RL[ridx])
        if param == "Cfi":
            return self.RTC.getRoomCfi(self.RL[ridx])
        
        if param == "Ric":
            return self.RTC.getRoomRic(self.RL[ridx])
        if param == "Rci":
            return self.RTC.getRoomRci(self.RL[ridx])
        if param == "Cic":
            return self.RTC.getRoomCic(self.RL[ridx])
        if param == "Cci":
            return self.RTC.getRoomCci(self.RL[ridx])
        
        if param == "Rwij":
            return self.RTC.getRoomRwij(self.RL[ridx])
        if param == "Rwik":
            return self.RTC.getRoomRwik(self.RL[ridx])
        if param == "Rwil":
            return self.RTC.getRoomRwil(self.RL[ridx])
        if param == "Rwio":
            return self.RTC.getRoomRwio(self.RL[ridx])
                
        if param == "Dim":
            return self.RTC.getRoomDim(self.RL[ridx])
             
    def getRoomSolarGain(self, slot, ridx, wall):
        """API to retrieve room solar gain"""
        return (self.RTC.getRoomSolarGainByTime(slot, self.RL[ridx], wall))/1000
    
    
#==================================================================
#     Main
#==================================================================
    def readProblemInstance(self, filename, meeting_cfg):    
        logging.info("===============================================================")
        logging.info("Loading problem instance from %s ..." %filename)
        logging.info("===============================================================")        
        ret = self._populateProbData(filename, meeting_cfg)
        if ret < 0:
            self._critical_err()
            
            

            
        
    