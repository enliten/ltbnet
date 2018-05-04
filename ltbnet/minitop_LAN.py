

import re
import sys
import logging
logging.basicConfig(level=logging.DEBUG)
import pprint

from mininet.topo import Topo
from mininet.link import Intf
from mininet.log import setLogLevel, info, error
from mininet.node import Node
from math import sin, cos, atan2, sqrt

# from mininet.link import Link,TCLink
# from mininet.node import OVSSwitch, Controller, RemoteController,Node

pp = pprint.PrettyPrinter(indent=4)
pi = 3.14159265358973
jpi2 = 1.5707963267948966j
rad2deg = 57.295779513082323
deg2rad = 0.017453292519943
R = 6371000         #Radius of Earth
c = 299792458       #Speed of light
class LinuxRouter( Node ):
    "A Node with IP forwarding enabled."

    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()


class LTBnet(Topo):
    def build(self,opts,config='',lan=True):
        """Builds mininet topology from the config file. Adds network information for routers and
        switches to a config object"""
        #TODO:make the config object do all of the network building, i.e don't use separate LTBnet structures
        self.config = config
        self.Regions = opts['Regions']
        self.RegionsD = {node.name : node for node in self.Regions}
        self.RegionsO = []  #Ordered Regions by chosen direction for switch creation
        self.PDCs = opts['PDCS']
        self.PDCsO = []
        self.PMUs = opts['PMUS']
        self.PMUsO = []
        self.NodeOBJ = {'Regions' : self.Regions , 'PDCS' : self.PDCs, 'PMUS' : self.PMUs}  #Coordinate Ordered Objects
        self.Nodes = {'Regions' : {} , 'PDCS' : {}, 'PMUS' : {}}
        self.Switches = {'Regions': {}, 'PDCS' : {}, 'PMUS': {}} #Ordered Switch connections (W-E or N-S)
        self.Router = {'Connects': []}
        self.switch = []
        # self.routers = []
        self.host = []
        self.port = []
        self.link = []
        self.linkdefault = {'bw': 10, 'delay': '5ms', 'loss': 10,
                           'max_queue_size': 100, 'use_htb': True}

    #Function Initializations
        if lan:
            self.gen_nodes(lan)
        else:
            self.gen_nodes(not(lan))

        self.coord_sw('Regions','lat')
        self.coord_sw('PMUS', 'lat')
        self.coord_sw('PDCS', 'lat')
        self.gen_reg_con()
        self.gen_pdc_con(self.NodeOBJ['PDCS'])
        self.gen_pmu_con(self.NodeOBJ['PMUS'])
        # pp.pprint(self.Switches)

    def haversine_d(self,coords1,coords2):
        """Calculates haversine distance(distance over the earths surface between two points) and delay for line
        coords1 = [lat1,long1]
        coords2 = [lat2,long2]"""
        phi1 = coords1[0]*deg2rad
        phi2 = coords2[0]*deg2rad
        delphi = (coords2[1]-coords1[1])*deg2rad
        dellam = (coords2[0]-coords1[0])*deg2rad

        f = sin(delphi/2.0)*sin(delphi/2.0) + \
            cos(phi1)*cos(phi1) + \
            sin(dellam/2.0)*sin(dellam/2.0)
        g = 2*atan2(sqrt(f),sqrt(1-f))
        d = R*g
        delay = d/c
        ret = {'delay': str(delay)+'ms'}
        return ret

    #Set physical port connections
    #TODO:Add this

    def coord_sw(self,typen,direction):
        """Orders Regions,or Nodes so that switch connections take place
        in a geographically ordered sequence
        Direction is longitudinal or latitudinal : ie, long or lat"""
        if direction not in ('long','lat'):
            logging.error("Must specify long or lat for switch direction")
            return False
        if direction == 'lat':
            idx = 0
        if direction == 'long':
            idx = 1

        self.NodeOBJ[typen] = sorted(self.NodeOBJ[typen],key=lambda coord: coord.coords[idx])
        self.Switches[typen] = {k.name: ([],[]) for k in self.NodeOBJ[typen]}  #Ordered Switch connections (W-E or N-S)

    def gen_nodes(self,lan):
        """Adds Regions,PDC and PMU nodes"""
        rnum = 1
        for reg in self.Regions:
            if lan:
                rname = 'r' + str(rnum)
            #Make fake router with a switch
                self.config.Routers[reg.name][rname] = {'Coords': reg.coords, 'HW_ADDR': 0, 'IP': reg.router}  #TODO:add hw
                self.config.nRouters[reg.name] += 1
                r = self.addSwitch(rname)
                self.switch.append(r)
                reg.router_node = rname
                self.Router[reg.name] = rname
            else:
                rname = 'r' + str(rnum)
                self.config.Routers[reg.name][rname] = {'Coords': reg.coords, 'HW_ADDR': 0,
                                                        'IP': reg.router}  # TODO:add hw
                self.config.nRouters[reg.name] += 1
                r = self.addNode(rname, cls=LinuxRouter, ip=reg.router + '/16')
                reg.router_node = rname
                self.Router[reg.name] = r
                n = self.addHost(reg.name, ip=reg.IP + '/24', mac=reg.MAC, defaultRoute='via ' + reg.router)
                reg.router_node = rname
                self.Router[reg.name] = r

            n = self.addHost(reg.name,ip=reg.IP,mac=reg.MAC)
            reg.node = rname
            rnum = rnum + 1

            self.Nodes['Regions'][reg.name]=n
            for i,pd in enumerate(reg.nodes['PDC']):
                pdname = reg.name + '_PDC_'+ str(i)
                npd = self.addHost(pdname,ip=pd.IP)
                pd.node = (npd,pdname)
                self.Nodes['PDCS'][reg.name] = npd

            for i,pm in enumerate(reg.nodes['PMU']):
                pmname = reg.name + '_PMU_'+ str(i)
                npm = self.addHost(pmname,ip=pm.IP)
                pm.node = npm
                self.Nodes['PMUS'][reg.name] = npm


    def gen_reg_con(self):
        #TODO:Openflow cannot have multiple paths to same node

        """Creates Link Connection for given hosts between routers"""
        sname1 = 's' + str(len(self.switch))
        # sname2 = 's' + str(len(self.switch)+1)
        for h1 in self.Regions:
            sname1 = 's' + str(len(self.switch))
            self.switch.append(self.addSwitch(sname1))
            self.config.nSwitches[h1.name] += 1
            self.config.Switches[h1.name][sname1] = {'Coords': h1.coords, 'HW_ADDR': 0}   #TODO: make switch coords and get HW_ADDR
            h1.switch = sname1
            h1.num_sws = h1.num_sws + 1

            # logging.info('Adding Switch Link to {}'.format(h1.name))
            # self.addLink(h1.name, sname1)
            # logging.info('Adding Switch(..pho Router) Link to {} switch'.format(h1.name))
            # self.addLink(sname1, self.Router[h1.name])
            logging.info('Adding Switch(..pho Router) Link to {} switch'.format(h1.name))
            self.addLink(h1.name, self.Router[h1.name])
            for h2 in h1.connects:
                checkcon1 = h1.name + '_to_' + h2
                checkcon2 = h2 + '_to_' + h1.name
                if checkcon1 not in self.Router['Connects'] and checkcon2 not in self.Router['Connects']:

                    logging.info('Linking routers from {} to {}'.format(h1.name,h2))
                    self.addLink(self.Router[h1.name],self.Router[h2],**self.haversine_d(h1.coords,self.config.Regions[h2]['Coords']))
                    self.config.InterConnects.append([{h1.name:self.Router[h1.name]}, {h2:self.Router[h2]}])
                    # self.config.InterConnects[h2].append([self.Router[h2], self.Router[h1.name]])
                    self.Router['Connects'].append(checkcon1)
                    self.Router['Connects'].append(checkcon1)
                else:
                    logging.info('Routers from {} to {} already connected'.format(h1.name,h2))
            # logging.info('Adding Region {} to switch {}'.format(h1.name,sname1))
            # self.addLink(h1.name, sname1)


    def gen_pdc_con(self, hosts):
        """Connects a PDC to each region"""

        """Creates Link Connection for given hosts"""
        for i,h1 in enumerate(hosts):
            # for i in range(0,self.Regions[h1.region].num_pdcs):
            if h1.region in self.Switches['Regions']:
                sname = 's' + str(len(self.switch))
                sw = self.addSwitch(sname)
                self.switch.append(sw)
                self.config.nSwitches[h1.region] += 1
                self.config.Switches[h1.region][sname] = {'Coords': h1.coords,
                                                         'HW_ADDR': 0}  # TODO: make switch coords and get HW_ADDR
                h1.switch = sname
                self.Switches['PDCS'][h1.name][0].append(sname)
                self.addLink(h1.name, sname,**self.haversine_d(h1.coords,self.config.Regions[h1.region]['Coords']))
                self.config.Connects[h1.region].append([h1.name, sname])    #Add "Router"Connect as r1 even though it is switch
                self.addLink(sname, self.Router[h1.region])
                self.config.Connects[h1.region].append([sname, self.Router[h1.region]])

            else:
                logging.warning("<PDC Region Undefined. {} not added>".format(h1.name))


    def gen_pmu_con(self, hosts):
        """Connects PMU's to the regions PDC"""
        #TODO: Deal with multiple switches for connection
        #TODO:Limit Number of PMUS connected to 1 PDC(i.e its switch)

        """Creates Link Connection for given hosts"""
        for i,h1 in enumerate(hosts):
            # for i in range(0,self.Regions[h1.region].num_pmus):
            for pd in h1.RegNode.nodes['PDC']:
                if pd.name in self.Switches['PDCS']:
                    pds = self.Switches['PDCS'][pd.name][0][-1]
                    self.Switches['PMUS'][h1.name][0].append(pds)
                    h1.switch = pd.switch
                    self.addLink(h1.name, pds,**self.haversine_d(h1.coords,self.config.Regions[h1.region]['Coords']))
                    self.config.Connects[h1.region].append([h1.name, pds])

                else:
                    logging.warning("<PMU Region Undefined. {} not added>".format(h1.name))


    def con_port(self, switches):
        """Creates hardware ethernet port connects defined by host computers desired eth port.
        Connects the hardware port, to a chosen switch which has already been created"""
        for key, value in self.port_to_switch.items():
            p = value[0]
            s = value[1]
            if s in self.switch:
                ind = self.switch.index(s)
                n = switches[ind]

            # self.addLink(h,sw)
            intfName = p
            info('*** Adding hardware interface', intfName, 'to ', \
                 n.name, '\n')
            _intf = Intf(intfName, node=n)

            self.port.append(_intf)

