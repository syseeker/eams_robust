
SOLVER_LNS_CRITICAL_ERR                             = -1
SOLVER_LNS_OPT_CONFIG_NOT_FOUND                     = -10001
SOLVER_LNS_NO_INITIAL_SOLUTION                      = -10002
SOLVER_LNS_INFEASIBLE_HVAC_CTRL                     = -10003
SOLVER_LNS_NO_MEETING_DESTROY                       = -10004
SOLVER_LNS_INFEASIBLE_PARTIAL_SCHEDULE              = -10005

class SOLVER_LNS_Error:
    def __init__(self):
        pass
    
    def solver_lns_opt_config_not_found(self):
        return SOLVER_LNS_OPT_CONFIG_NOT_FOUND
    
    def solver_lns_no_initial_solution(self):
        return SOLVER_LNS_NO_INITIAL_SOLUTION
    
    def solver_lns_infeasible_hvac_ctrl(self):
        return SOLVER_LNS_INFEASIBLE_HVAC_CTRL
    
    def solver_lns_no_meeting_destroy(self):
        return SOLVER_LNS_NO_MEETING_DESTROY
    
    def solver_lns_infeasible_partial_schedule(self):
        return SOLVER_LNS_INFEASIBLE_PARTIAL_SCHEDULE
    
    
    