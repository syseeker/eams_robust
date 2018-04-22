import logging
from eams import EAMS
from solver_osg import Solver_OS_Greedy

class Solver:
    def __init__(self):
        self._initLogging()
                
    def _initLogging(self):
        self.logger = logging.getLogger()           # activate log
#         self.logger.setLevel(logging.WARN)
        self.logger.setLevel(logging.INFO)
#         self.logger.setLevel(logging.DEBUG)

    def _activateLogFile(self, f):
        for old_handler in self.logger.handlers:
            self.logger.removeHandler(old_handler)  # remove old handler
        handler = logging.FileHandler(f)            # create a handler with the name defined by the variable f        
        self.logger.addHandler(handler)             # add that handler to the logger
        
    def initrun(self, runcfg, casecfg):
        for i in xrange(0,len(casecfg)):      
            if len(casecfg[i]) <= 0:
                return
            
            caseprop = casecfg[i].split()
            case = caseprop[0]                  # general configuration
            mcfg = caseprop[1]                  # meeting configuration
            lns_limit = int(caseprop[2])        # LNS time limit
            mip_limit = float(caseprop[3])      # MIP time limit
            update_interval = int(caseprop[4])  # online update interval
            rndseed = int(caseprop[5])          # random seed (used previously to pick meetings from USC data and so on.)
            algo = caseprop[6]
                                    
            # Given Input/eams_meeting_m10_04_227000_18_ws.cfg        
            #      caseid : ['Input', 'eams_meeting_m10_04_227000_18_ws', 'cfg']
            gencasecfgid = case.replace('/',' ').replace('.',' ').split()
            room_num = gencasecfgid[1].split('_')[0]
            mcfgid = mcfg.replace('/',' ').split()
            
            self.casecfgid = room_num+"_"+mcfgid[3]
            self.runcfg = runcfg
            
            # Activate log file
            fn = 'Output/' + self.casecfgid
            self._activateLogFile(fn)
                              
            self.eams = EAMS()        
            self.eams.readProblemInstance(case, mcfg)
            
            if algo == 'EU_RB' or algo == 'OA_RB' or algo == 'PC_RB':
                slack = float(caseprop[7])
                delta = float(caseprop[8])
                probguar = float(caseprop[9])
                osg = Solver_OS_Greedy(self.eams, fn, runcfg, self.casecfgid, lns_limit, mip_limit, update_interval, rndseed, algo, slack, delta, probguar)
            else:
                osg = Solver_OS_Greedy(self.eams, fn, runcfg, self.casecfgid, lns_limit, mip_limit, update_interval, rndseed)
            osg.run()
            
            
            
            

            
            
        