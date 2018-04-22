import sys
from solver import Solver

def run_it(runcfg, arr_casecfg):
    casecfgs = arr_casecfg.split('\n')
    solver = Solver()
    solver.initrun(runcfg, casecfgs)  
    

if __name__ == '__main__':
           
    if len(sys.argv) > 1:        
        file_location = sys.argv[1].strip()
        run_config_file = open(file_location, 'r')
        arr_casecfg = ''.join(run_config_file.readlines())
        run_config_file.close()        
        
        runcfg = file_location.replace('/',' ').replace('.',' ').split() # exclude folder and .cfg        
        run_it(runcfg[2], arr_casecfg)    
    else:
        print 'This test requires an input file.  Please select one from the data directory. (i.e. python run.py ./Input/eams.cfg)'
        
