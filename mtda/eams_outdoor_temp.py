
import logging
import collections
from datetime import datetime
from datetime import timedelta
from eams_error import EAMS_Error 
    
class OutdoorTemperature:
    def __init__(self):        
        self.err = EAMS_Error()
        self.OUTDOOR_TEMP_DATA = None
        self.temperature = {}      
        
    def loadOutdoorTemperature(self, tfile):
        """Load outdoor temperature from OUTDOOR_TEMP_DATA"""
        logging.info("Loading outdoor temperature data from %s" %tfile)
        
        try:
            df = open(tfile, 'r')
            data = ''.join(df.readlines())
            df.close()
            
            self._parseOutdoorTemperature(data)            
        except (IOError), e:        
            logging.error('%s' % (e))
            return self.err.eams_config_otc_err()
        
        return 0  
            
    def _parseOutdoorTemperature(self, data):
        """Parse the temperature input data"""
        
        temperature = {}
        lines = data.split('\n')    
        count = int(lines[0])
        for i in range(1, count+1):
            line = lines[i]
            parts = line.split()
            dtstr = ' '.join((parts[1], parts[2]))
            #NOTE: As dict type is used, duplicate entries with the same date/time is filtered.
            temperature[datetime.strptime(dtstr, "%Y-%m-%d %H:%M")] = parts[3]
            
        #NOTE: Python dictionary is unordered by default. Use OrderedDict to make sure temperature is recorded in date/time order.
        self.temperature = collections.OrderedDict(sorted(temperature.items()))        
        
#         for k,v in self.temperature.iteritems():
#             logging.debug("[%s]: %s" %(k,v))
            
    
    def getOutdoorTemperature(self, start, end, interval):
        """Get outdoor temperature between specific timeframe"""
        logging.info("Extracting temperature data between %s and %s" %(start, end))
        
        filtered_temperature = {}   
        for k, v in self.temperature.iteritems():
            if (k >= start and k <= end):
                if k.minute % interval == 0:
                    filtered_temperature[k]=float(v)  
                    
        #TODO: double check if assigning dict to OrderedDict always returns the correct order!
        dtm = collections.OrderedDict(sorted(filtered_temperature.items()))
        return dtm
    
    
    def getSingleDayOutdoorTemperatureShortInterval(self, start, end, interval):
        """Get outdoor temperature between specific timeframe"""
        s = start
        e = end
        logging.info("Extracting temperature data between %s and %s for %s mins interval" %(start, end, interval))
                   
        de = (s + timedelta(hours=24))
        
        i=0
        oneday_temp = []
        for k, v in self.temperature.iteritems():
            if (k >= s and k < de):
                if (k.minute == 0 or k.minute == 30):
                    oneday_temp.append(v)      
                    logging.debug("Time [%s]: %s" %(k,v))
                    i = i+1    
        total_i = i
        
#         logging.debug("total_i: %d, len: %d, One day temp: %s" %(total_i, len(oneday_temp), oneday_temp))
                
        ii=0
        temperature = {}
        for k, v in self.temperature.iteritems():
            if (k >= s and k < e):
#                 logging.debug("For time period t=%s" %(k))    
                if (k.minute == 0 or k.minute == 30):
                    curr_t = k
                    next_t = (curr_t + timedelta(minutes=30))
#                     logging.debug("curr_t: %s, next_t: %s" %(curr_t, next_t))
                    t = curr_t
                    
                    curr_rec = float(oneday_temp[ii])
                    if ii < total_i-1:
                        next_rec = float(oneday_temp[ii+1])                    
                    else:
                        next_rec = float(oneday_temp[0])
#                     logging.debug("current temp record [%s], next [%s]" %(curr_rec, next_rec))
                        
                    if interval==1:
                        delta_rec = float(next_rec - curr_rec)/10
                    else:
                        delta_rec = float((next_rec - curr_rec)/float(interval))
                        
                    j = 0
                    while t < next_t:
#                         logging.debug("interpolate at t=%s, +%.3f" %(t, delta_rec * j))
                        temperature[t] = curr_rec + (delta_rec * j)
                        
                        t =  t + timedelta(minutes=int(interval))
                        j = j+1
                
                    ii = ii + 1
                    if ii == total_i: ii=0  
                    
        dtm = collections.OrderedDict(sorted(temperature.items()))
                
        return dtm
        #NOTE: This is only for experiment - END
    