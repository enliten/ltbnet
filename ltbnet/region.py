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


