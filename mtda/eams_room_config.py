import logging
import collections
from eams_error import EAMS_Error 
from validate import Validator, ValidateError
from configobj import ConfigObj, ConfigObjError, flatten_errors

class RoomConfig:    
    def __init__(self):
        """Initialization"""
        self.err = EAMS_Error()
        self.rooms = {}
        self.zones = {}
        self.zonelist = {}
        self.roomlist = []
        self.roomcapa = []
        self.room_neighbours = []
    
    def _getRoomAdjacentWalls(self, room):
        """Get adjacent room of a given room's ID"""           
        aw = []    
        aw.append(room['Wall1']['AdjRoom'])
        aw.append(room['Wall2']['AdjRoom'])
        aw.append(room['Wall3']['AdjRoom'])
        aw.append(room['Wall4']['AdjRoom'])      
        return aw
        
    def _validateAdjacentWallConfig(self, rooms):
        """Validate consistency of adjacent wall(s) configurations in ROOM_CONFIG """
        logging.info("Validating adjacent walls configuration...")        
        awls = {}
        for k, v in rooms.iteritems():
            awls[k] = self._getRoomAdjacentWalls(v)
            logging.debug("Room [%s]'s adjacent rooms [%s]" %(k, ','.join(awls[k])))
        logging.debug("Rooms' adjacent wall's: %s" %awls)
    
        for k, v in awls.iteritems(): 
            nls = v        #    get awls{'k'} neighbors
            # Check duplicate adjacent wall
            dls = collections.Counter(nls)
            if len([j for j in dls if j!='Outdoor' and dls[j]>1]) != 0:
                logging.error("Duplicate adjacent wall for the room[%s]: %s. HALT." %(k, dls))
                return self.err.eams_config_room_duplicate_wall_err()
            
            # Check if neighbor rooms has also set room{'k'}'s wall as adjacent wall.
            for j in range(len(nls)):
                nnls = awls.get(nls[j])
                if nnls is not None and k not in nnls:              
                    logging.error("[%s] is not adjacent to [%s]. HALT." %(k, nls[j]))
                    return self.err.eams_config_room_invalid_wall_err()
            
        logging.info("Adjacent wall configurations, result: True.")    
        return 0
    
    def loadRoomConfig(self, rfile):
        """Load room configuration from ROOM_CONFIG"""
        self.ROOM_CONFIG = rfile
        logging.info("Loading room configuration from %s" %self.ROOM_CONFIG)
        ret = 0
        
        try:
            if self.ROOM_CONFIG == "":
                raise IOError("ROOM_CONFIG is not configured. Error.")
            
            rooms = ConfigObj(self.ROOM_CONFIG, file_error=True)
            logging.debug("Room properties: %s" %rooms)
            logging.debug("Total number of room: %d [%s]" %(len(rooms), ', '.join(rooms.keys())))
           
            ret = self._validateAdjacentWallConfig(rooms)      
            if ret < 0: 
                raise ValidateError()
            
            self.rooms = rooms
            
        except (ConfigObjError, IOError), e:        
            logging.critical('%s' % (e))
            ret = self.err.eams_config_room_err()
        except (ValidateError), e:        
            logging.critical("%s validation error. %d" %(self.ROOM_CONFIG, ret))
            
        return ret
        
    def populateRoomByZone(self):
        logging.info("Populate rooms into zone")        
#         logging.debug(self.CR)        
        try:
            zr = {}
            zone = {}
            for k, v in self.rooms.iteritems():
                z = zr.get(v['ZoneID'])            
                if z is None:
                    zr[v['ZoneID']] = [k]
                    zone[v['ZoneID']] = {k:v}
                else:
                    z.append(k)        
                    zone[v['ZoneID']].update({k:v})
            logging.debug("Room by zone: %s" %zr)
            logging.debug("Room Info by zone: %s" %zone)        
            self.zonelist = zr # contain Room Name for rooms in each zone
            self.zones = zone  # contain full room information for rooms in each zone
            
            self._populateRoomList()
            self._populateRoomCapa()
            self._populateRoomNeighbourList()
        except (UnboundLocalError), e:
            logging.error('%s' % (e))
            
    def _populateRoomCapa(self):
        logging.info("Populate room capacity")
        try:
            for i in xrange(len(self.roomlist)):
                self.roomcapa.append(self.rooms.get(self.roomlist[i])['MaxCapa'])
        except(UnboundLocalError), e:
            logging.error('%s' % (e))
            
    def _populateRoomList(self):
        logging.info("Populate a list of rooms from all zones")
        for _,v in self.zonelist.iteritems():
            for i in range(len(v)):
                self.roomlist.append(v[i])                
        logging.debug("List of rooms: %s" %self.roomlist)

    def _populateRoomNeighbourList(self):
        logging.info("Populate a list of room neighbours")
        
        nls = []
        ridx = -1
        for _, v in self.rooms.iteritems():
            nls = self._getRoomAdjacentWalls(v)
            logging.debug(nls)
            self.room_neighbours.append([])
            ridx = ridx + 1
            for n in xrange(len(nls)):
                if nls[n] == 'Outdoor':
                    self.room_neighbours[ridx].append(1000)
                elif nls[n] in self.roomlist:
                    self.room_neighbours[ridx].append(self.roomlist.index(nls[n]))                    
                else:
                    self.room_neighbours[ridx].append(-1)
#         logging.debug("Neighbor List:%s" %self.room_neighbours)
            
        
    def getRoomsInfoByZone(self, zone_key):     
        if self.zones is None:
            logging.error("Empty zone. Call populateRoomByZone() first.")
            return None   
        if zone_key == "All":
            return self.zones
        else:
            return self.zones.get(zone_key)
        
    def getZoneList(self):
        return self.zonelist
        
    def getRoomList(self):
        return self.roomlist
    
    def getRoomCapaList(self):
        return self.roomcapa
    
    def getRoomNeighboursList(self):
        return self.room_neighbours
    