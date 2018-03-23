
"""First Template for creating a 2 host network which consists
of a PMU at eth0 and a PDC at eth1. This is to be used for connecting
CURENT's OPAL-RT hardware target streaming data through a PMU to a virtual
network and physical end layers"""

import re
import sys

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import Intf
from mininet.cli import CLI
from mininet.log import setLogLevel, info, error
from mininet.util import dumpNodeConnections
from mininet.topolib import TreeTopo
from mininet.util import quietRun


class LTBnet(Topo):
    def build(self, n, opts):
        self.hostnames = opts['hostnames']  # A list of host names
        self.hostports = opts['hostports']
        self.host = []
        self.port = []
        self.switchnames = opts['switchnames']  # A list of host names
        self.switch = []
        self.link = []
        self.port_to_switch = opts['port_to_switch']  # Dict of (port,switch) connections
        self.linkset = opts['link_config']  # A Dict of Dict of link configs
        # Topo.__init__(self)
        # Add switches
        for s in self.switchnames:
            self.switch.append(self.addSwitch(s))
        # Add hosts
        for h in self.hostnames:
            self.host.append(self.addHost(h, cpu=.25 / n))

        # Set link configurations for each link
        for key, value in self.linkset.items():
            config = value['setting']
            l1 = value['l1']
            l2 = value['l2']
            self.addLink(l1, l2)

    # Set physical port connections
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

