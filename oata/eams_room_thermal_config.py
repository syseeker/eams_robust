
import logging
from datetime import datetime

class RoomThermalCfg:
    def __init__(self, room_config, timeslot):
        self.Z = room_config
        self.TS = timeslot
                        
        self.C = {}
        self.Rij = {}
        self.Rik = {}
        self.Ril = {}
        self.Rio = {}
        self.Rif = {}
        self.Ric = {}
        
        self.Rimj = {}
        self.Rimk = {}
        self.Riml = {}
        self.Rimo = {}
        self.Rimf = {}
        self.Rimc = {}
        
        self.Rji = {}
        self.Rki = {}
        self.Rli = {}
        self.Roi = {}
        self.Rfi = {}
        self.Rci = {}
        
        self.Rwij = {}
        self.Rwik = {}
        self.Rwil = {}
        self.Rwio = {}
                
        self.Cij = {}
        self.Cik = {}
        self.Cil = {}
        self.Cio = {}
        self.Cif = {}
        self.Cic = {}
        
        self.Cji = {}
        self.Cki = {}
        self.Cli = {}
        self.Coi = {}
        self.Cfi = {}
        self.Cci = {}
        
        self.RoomSolarGain = {}
        self.RoomDim = {}
        
        self._populateRoomDimension()
        self._populateRoomThermalProperties()
        self._populateRoomSolarGain()
#         self._populateRoomSolarGainSingleDay()
                
    def _populateRoomDimension(self):
        for _, v in self.Z.iteritems(): # for each zone            
            for rk, rv in v.iteritems():  # for each room
                self.RoomDim[rk] = [int(rv['Width']), int(rv['Length']), int(rv['Height'])]
                
    #TODO: populate all data in room_config. Now only two!!
    def _populateRoomThermalProperties(self):
        for _, v in self.Z.iteritems(): # for each zone            
            for rk, rv in v.iteritems():  # for each room
                #=========================================
                # Given zone i is adjacent to zone j
                # CR - R(i)
                # R1 - R(i, j)
                # R2 - Rmid(i,j)
                # R3 - R(j, i)
                # C1 - C(i, j)
                # C2 - C(j, i)                
                #=========================================
                self.C[rk] = rv['CR']
                self.Rij[rk] = rv['Wall1']['R1']
                self.Rik[rk] = rv['Wall2']['R1']
                self.Ril[rk] = rv['Wall3']['R1']
                self.Rio[rk] = rv['Wall4']['R1']
                self.Rif[rk] = rv['Floor']['R1']
                self.Ric[rk] = rv['Ceiling']['R1']
                
                self.Rimj[rk] = rv['Wall1']['R2']
                self.Rimk[rk] = rv['Wall2']['R2']
                self.Riml[rk] = rv['Wall3']['R2']
                self.Rimo[rk] = rv['Wall4']['R2']
                self.Rimf[rk] = rv['Floor']['R2']
                self.Rimc[rk] = rv['Ceiling']['R2']
                
                self.Rji[rk] = rv['Wall1']['R3']
                self.Rki[rk] = rv['Wall2']['R3']
                self.Rli[rk] = rv['Wall3']['R3']
                self.Roi[rk] = rv['Wall4']['R3']
                self.Rfi[rk] = rv['Floor']['R3']
                self.Rci[rk] = rv['Ceiling']['R3']
                
                self.Rwij[rk] = rv['Wall1']['RW']
                self.Rwik[rk] = rv['Wall2']['RW']
                self.Rwil[rk] = rv['Wall3']['RW']
                self.Rwio[rk] = rv['Wall4']['RW']
                
                self.Cij[rk] = rv['Wall1']['C1']
                self.Cik[rk] = rv['Wall2']['C1']
                self.Cil[rk] = rv['Wall3']['C1']
                self.Cio[rk] = rv['Wall4']['C1']
                self.Cif[rk] = rv['Floor']['C1']
                self.Cic[rk] = rv['Ceiling']['C1']
                
                self.Cji[rk] = rv['Wall1']['C2']
                self.Cki[rk] = rv['Wall2']['C2']
                self.Cli[rk] = rv['Wall3']['C2']
                self.Coi[rk] = rv['Wall4']['C2']
                self.Cfi[rk] = rv['Floor']['C2']
                self.Cci[rk] = rv['Ceiling']['C2']
        
    def _loadRoomSolarGain(self, fname):        
        data_file = open(fname, 'r')
        data = ''.join(data_file.readlines())
        data_file.close()
         
        lines = data.split('\n')
        solar_gain = {}        
        for i in xrange(len(lines)-1):
            parts = lines[i].split(',')  
            k = datetime.strptime(parts[0], "%Y-%m-%d %H:%M")         
            solar_gain[k] = float(parts[1])
        return solar_gain  
         
    def _populateRoomSolarGain(self):
        for _, v in self.Z.iteritems(): # for each zone            
            for rk, rv in v.iteritems():  # for each room                
                qs = self._loadRoomSolarGain(rv.get('Solar'))
                self.RoomSolarGain[rk] = []
                for _, tv in self.TS.iteritems():
                    # [a,b,c,d,e] --> solar gain for Wall1/2/3/4 & Floor. Currently assume wall 1 contains the solar gain (for simplicity)
                    self.RoomSolarGain[rk].append([qs.get(tv),0,0,0,0])
                    # [a,b,c,d,e] --> solar gain for Wall1/2/3/4 & Floor. Currently assume floor contains the solar gain (for simplicity)                               
#                     self.RoomSolarGain[rk].append([qs.get(tv),0,0,0,qs.get(tv)]) 
                           
    def _populateRoomSolarGainSingleDay(self):
        for _, v in self.Z.iteritems(): # for each zone            
            for rk, rv in v.iteritems():  # for each room                
                qs = self._loadRoomSolarGain(rv.get('Solar'))
                self.RoomSolarGain[rk] = []
                tmp_solar = []
                for _, tv in self.TS.iteritems():    
                    # debug
                    if ((tv >= datetime.strptime("2012-01-07 00:00", "%Y-%m-%d %H:%M")) and
                        (tv < datetime.strptime("2012-01-08 00:00", "%Y-%m-%d %H:%M"))):
                        tmp_solar.append(qs.get(tv))
                    
                i = 0    
                for _, tv in self.TS.iteritems():
                    self.RoomSolarGain[rk].append([tmp_solar[i],0,0,0,0])
                    i += 1
                    if i == len(tmp_solar): i=0
        
                    
                    
                          
#     =====================================================================
            
    def getRoomC(self, rname):
        return float(self.C.get(rname))
    
    def getRoomRij(self, rname):
        return float(self.Rij.get(rname))    
    def getRoomRik(self, rname):
        return float(self.Rik.get(rname))    
    def getRoomRil(self, rname):
        return float(self.Ril.get(rname))    
    def getRoomRio(self, rname):
        return float(self.Rio.get(rname))    
    def getRoomRif(self, rname):
        return float(self.Rif.get(rname))    
    def getRoomRic(self, rname):
        return float(self.Ric.get(rname))    
    
    def getRoomRimj(self, rname):
        return float(self.Rimj.get(rname))    
    def getRoomRimk(self, rname):
        return float(self.Rimk.get(rname))   
    def getRoomRiml(self, rname):
        return float(self.Riml.get(rname))   
    def getRoomRimo(self, rname):
        return float(self.Rimo.get(rname))   
    def getRoomRimf(self, rname):
        return float(self.Rimf.get(rname))   
    def getRoomRimc(self, rname):
        return float(self.Rimc.get(rname))   
    
    def getRoomRji(self, rname):
        return float(self.Rji.get(rname))         
    def getRoomRki(self, rname):
        return float(self.Rki.get(rname))
    def getRoomRli(self, rname):
        return float(self.Rli.get(rname))
    def getRoomRoi(self, rname):
        return float(self.Roi.get(rname))
    def getRoomRfi(self, rname):
        return float(self.Rfi.get(rname))
    def getRoomRci(self, rname):
        return float(self.Rci.get(rname))
    
    def getRoomRwij(self, rname):
        return float(self.Rwij.get(rname))        
    def getRoomRwik(self, rname):
        return float(self.Rwik.get(rname))
    def getRoomRwil(self, rname):
        return float(self.Rwil.get(rname))
    def getRoomRwio(self, rname):
        return float(self.Rwio.get(rname))

    def getRoomCij(self, rname):
        return float(self.Cij.get(rname))    
    def getRoomCik(self, rname):
        return float(self.Cik.get(rname))    
    def getRoomCil(self, rname):
        return float(self.Cil.get(rname))    
    def getRoomCio(self, rname):
        return float(self.Cio.get(rname))    
    def getRoomCif(self, rname):
        return float(self.Cif.get(rname))    
    def getRoomCic(self, rname):
        return float(self.Cic.get(rname))    
    
    def getRoomCji(self, rname):
        return float(self.Cji.get(rname))         
    def getRoomCki(self, rname):
        return float(self.Cki.get(rname))
    def getRoomCli(self, rname):
        return float(self.Cli.get(rname))
    def getRoomCoi(self, rname):
        return float(self.Coi.get(rname))
    def getRoomCfi(self, rname):
        return float(self.Cfi.get(rname))
    def getRoomCci(self, rname):
        return float(self.Cci.get(rname))      
            
    def getRoomDim(self, rname):
        return self.RoomDim.get(rname)
    
    def getRoomSolarGainByTime(self, slot, rname, wall):
#         print self.RoomSolarGain.get(rname)[slot]
        return float(self.RoomSolarGain.get(rname)[slot][wall])
#         logging.debug("Room 0 slot 0 Qs =  %s" %(EAMS.getRoomSolarGain(0,0)))
    
    
    