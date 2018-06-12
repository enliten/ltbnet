""""Node object definition for creating virtual nodes(Operator,PMU's,PDC's)"""

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import Intf
from mininet.cli import CLI


class Region():
    def __init__(self,params):
        self.ID = params['ID']              #Identifier
        self.router = params['router']      #Gateway
        self.router_node = None
        self.IP = params['IP']
        self.coords = params['coords']      #Coordinate Location
        self.name = params['name']      #Operator Region Name
        self.region = params['region']
        self.connects = params['connects']
        self.MAC = params['MAC']
        self.switch = None           #Switch Name
        self.node = None               #Node Name
        self.ip_list = []
        self.id_list = []
        self.num_sws = 0
        self.num_pmus = params['num_pmus']
        self.num_pdcs = params['num_pdcs']
        self.nodes = {'PDC' : [], 'PMU' : []}    #Holds PDC and PMU Objects
        # self.set_ip()

    # def set_ip(self):
    #     """Inherits router address from region or PDC, then adds IP"""
    #     ldigs = self.IP.split('.')
    #     self.IP = '.'.join((ldigs[0],ldigs[1],ldigs[2],ldigs[3]))
    #     # print('{} IP address is {}'.format(self.name,self.IP))
    def ip_change(self,ip,oct,num):
        """Changes chosen ip Octet to given num"""
        ldigs = ip.split('.')
        ldigs[oct] = str(num)
        self.IP = '.'.join(ldigs)
