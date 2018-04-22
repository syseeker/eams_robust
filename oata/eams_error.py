
EAMS_CRITICAL_ERR                               = -1
EAMS_CONFIG_PROBLEM_ERR                         = -100
EAMS_CONFIG_ROOM_ERR                            = -111
EAMS_CONFIG_ROOM_DUPLICATE_WALL_ERR             = -112
EAMS_CONFIG_ROOM_INVALID_WALL_ERR               = -113
EAMS_CONFIG_MEETING_ERR                         = -120
EAMS_CONFIG_OUTDOOR_TEMPERATURE_ERR             = -130
EAMS_MEETING_OUT_OF_TIMESLOT_RANGE              = -200
EAMS_MEETING_INVALID_DURATION                   = -201
EAMS_MEETING_INVALID_TIME_WINDOWS               = -202
EAMS_MEETING_OVERLAPPED_TIME_WINDOWS            = -203
EAMS_MEETING_NO_FEASIBLE_ROOM                   = -204
EAMS_NO_OUTDOOR_TEMP_IN_SCHEDULING_RANGE        = -300

SOLVER_LNS_CRITICAL_ERR                             = -1
SOLVER_LNS_OPT_CONFIG_NOT_FOUND                     = -10001
SOLVER_LNS_NO_INITIAL_SOLUTION                      = -10002
SOLVER_LNS_INFEASIBLE_HVAC_CTRL                     = -10003
SOLVER_LNS_NO_MEETING_DESTROY                       = -10004

SOLVER_MODEL_INFEASIBLE                             = -999

class EAMS_Error:
    def __init__(self):
        pass
    
    def eams_config_problem_err(self):
        return EAMS_CONFIG_PROBLEM_ERR

    def eams_config_room_err(self):
        return EAMS_CONFIG_ROOM_ERR
    
    def eams_config_room_duplicate_wall_err(self):
        return EAMS_CONFIG_ROOM_DUPLICATE_WALL_ERR
    
    def eams_config_room_invalid_wall_err(self):
        return EAMS_CONFIG_ROOM_INVALID_WALL_ERR
    
    def eams_config_meeting_err(self):
        return EAMS_CONFIG_MEETING_ERR
    
    def eams_config_otc_err(self):
        return EAMS_CONFIG_OUTDOOR_TEMPERATURE_ERR
    
    def eams_meeting_out_of_timeslot_range(self):
        return EAMS_MEETING_OUT_OF_TIMESLOT_RANGE
    
    def eams_meeting_invalid_duration(self):
        return EAMS_MEETING_INVALID_DURATION
    
    def eams_meeting_invalid_time_windows(self):
        return EAMS_MEETING_INVALID_TIME_WINDOWS
    
    def eams_meeting_overlapped_time_windows(self):
        return EAMS_MEETING_OVERLAPPED_TIME_WINDOWS
    
    def eams_no_outdoor_temp_in_scheduling_range(self):
        return EAMS_NO_OUTDOOR_TEMP_IN_SCHEDULING_RANGE
    
    def eams_meeting_no_feasible_room(self):
        return EAMS_MEETING_NO_FEASIBLE_ROOM
    
    def eams_infeasible(self):
        return SOLVER_MODEL_INFEASIBLE
    
    
    