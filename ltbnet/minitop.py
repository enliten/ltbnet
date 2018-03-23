

import re
import sys
import logging

from mininet.topo import Topo
from mininet.link import Intf
from mininet.log import setLogLevel, info, error
from mininet.node import OVSSwitch, Controller, RemoteController



class LTBnet(Topo):
    def build(self,opts):
        self.Regions = opts['Regions']
        self.RegionsO = []  #Ordered Regions by chosen direction for switch creation
        self.PDCs = opts['PDCS']
        self.PDCsO = []
        self.PMUs = opts['PMUS']
        self.PMUsO = []
        self.NodeOBJ = {'Regions' : self.Regions , 'PDCS' : self.PDCs, 'PMUS' : self.PMUs}  #Coordinate Ordered Objects
        self.Nodes = {'Regions' : {} , 'PDCS' : {}, 'PMUS' : {}}
        self.Switches = {'Regions': {}, 'PDCS' : {}, 'PMUS': {}} #Ordered Switch connections (W-E or N-S)
        self.switch = []
        self.routers = []
        self.host = []
        self.port = []
        self.link = []


    #Function Initializations
        self.gen_nodes()
        self.coord_sw('Regions','lat')
        self.coord_sw('PMUS', 'lat')
        self.coord_sw('PDCS', 'lat')
        self.gen_reg_con()
        self.gen_pdc_con(self.NodeOBJ['PDCS'])
        self.gen_pmu_con(self.NodeOBJ['PMUS'])
        print self.Switches

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
        # for i in self.NodeOBJ[typen]:
        #     print("Name: {} Coords {} ".format(i.name,i.coords))
        self.NodeOBJ[typen] = sorted(self.NodeOBJ[typen],key=lambda coord: coord.coords[idx])
        for i in self.NodeOBJ[typen]:
            print("Name: {} Coords: {} ".format(i.name, i.coords))

        self.Switches[typen] = {k.name: [] for k in self.NodeOBJ[typen]}  #Ordered Switch connections (W-E or N-S)

    def gen_nodes(self):
        """Adds Regions,PDC and PMU nodes"""
        for reg in self.Regions:
            n = self.addHost(reg.name)
            self.Nodes['Regions'][reg.name]=n
            for i in range(0,reg.num_pdcs):
                npd = self.addHost(reg.name + '_PDC_'+ str(i))
                self.Nodes['PDCS'][reg.name] = npd

            for i in range(0,reg.num_pmus):
                npm = self.addHost(reg.name + '_PMU_'+ str(i))
                self.Nodes['PMUS'][reg.name] = npm

    def gen_reg_con(self):
        #TODO:Openflow cannot have multiple paths to same node

        """Creates Link Connection for given hosts"""
        for h1 in self.Regions:
            sname = 's' + str(len(self.switch))
            self.switch.append(self.addSwitch(sname))
            self.Switches['Regions'][h1.name].append(sname)
            self.addLink(h1.name, sname)

        for i, n in enumerate(self.switch):
            if i == len(self.switch)-1:
                break
            else:
                print('Linking {} to {}'.format(n, self.switch[i + 1]))
                self.addLink(n ,self.switch[i+1])

    def gen_pdc_con(self, hosts):
        # TODO:ADD Distance calculations for links

        """Creates Link Connection for given hosts"""
        for i,h1 in enumerate(hosts):
            # for i in range(0,self.Regions[h1.region].num_pdcs):
            if h1.region in self.Switches['Regions']:
                sname = 's' + str(len(self.switch))
                self.switch.append(self.addSwitch(sname))
                self.Switches['PDCS'][h1.name].append(sname)
                self.addLink(h1.name, sname)
                self.addLink(sname, self.Switches['Regions'][h1.region][-1])
            else:
                logging.warning("<PDC Region Undefined. {} not added>".format(h1.name))


    def gen_pmu_con(self, hosts):
        # TODO:ADD Distance calculations for links. Deal with multiple switches for connection [-1]
        #TODO:Limit Number of PMUS connected to 1 PDC(i.e its switch)

        """Creates Link Connection for given hosts"""
        for i,h1 in enumerate(hosts):
            # for i in range(0,self.Regions[h1.region].num_pmus):
            for pd in h1.RegNode.nodes['PDC']:
                if pd.name in self.Switches['PDCS']:
                    sname = 's' + str(len(self.switch))
                    self.switch.append(self.addSwitch(sname))
                    self.Switches['PMUS'][h1.name].append(sname)
                    self.addLink(h1.name, sname)
                    self.addLink(sname, self.Switches['PDCS'][pd.name][-1])
                else:
                    logging.warning("<PMU Region Undefined. {} not added>".format(h1.name))


    def con_port(self, switches):
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

