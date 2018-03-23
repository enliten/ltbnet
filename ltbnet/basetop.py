"""Base topology for the Regional operators in the network.  Starting with randomly created network, to
allow for easy transistion from general topology to a defined topology"""


from random import randint,random
from random import uniform

from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import OVSSwitch, Controller, RemoteController
from mininet.log import setLogLevel, info, error

from region import Region
from node import Node
from minitop import LTBnet

import logging
logging.basicConfig(level=logging.ERROR)
points = ['AESO', 'BCTC', 'BPA', 'VRCC', 'IPCO', 'LRCC' , 'WAPA', 'CAIS', 'PGE', 'SCE', \
          'LADW', 'SDGE', 'APS', 'SRP', 'PNM']
# points = ['AESO', 'BCTC', 'BPA', 'VRCC']
coords = {n: () for n in points}
regions = {n: [] for n in points}
pdcdata = dict()    # key: name, {keys: name,ID,coords,router}
pmudata = dict()    #keys: pdcname,ID,coords,ip,level

setLogLevel('info')
# hostports = ['enp4s0f0', 'enp4s0f1']
# switchnames = ['s1', 's2']
# portsw = {1: ('enp4s0f0', 's1'), 2: ('enp4s0f1', 's2')}
linkset = {1: {'setting': {'bw': 10, 'delay': '5ms', 'loss': 10,
                           'max_queue_size': 100, 'use_htb': True},
               'l1': 'hPMU', 'l2': 's1'},
           2: {'setting': {'bw': 10, 'delay': '5ms', 'loss': 10,
                           'max_queue_size': 100, 'use_htb': True},
               'l1': 'hPDC', 'l2': 's2'},
           3: {'setting': {'bw': 10, 'delay': '5ms', 'loss': 10,
                           'max_queue_size': 100, 'use_htb': True},
               'l1': 's1', 'l2': 's2'}}
# opts = {'hostnames': hostnames, 'hostports': hostports, 'switchnames': switchnames, \
#         'link_config': linkset, 'port_to_switch': portsw}
def add_connect(node, connects):
    for c in connects:
        if c != node and (c not in regions[node]) :
            regions[node].append(c)
        else:
            logging.warning("Cannot connect point with itself")

def ip_change(ip,oct,num):
    """Changes chosen ip Octet to given num"""
    ldigs = ip.split('.')
    ldigs[oct] = str(num)
    newip = '.'.join(ldigs)
    return newip

def rand_coords(crange):
    ll = crange[0]
    lh = crange[1]
    lol = crange[2]
    loh = crange[3]
    long = uniform(lol,loh)
    lat = uniform(ll,lh)
    coord = (round(lat,3),round(long,3))
    return coord

if __name__ == '__main__':
    OPS = []
    PDCS = []
    PMUS = []
    #Generate random network topology
    for p in points:
        connects = []
        for i in range(1,randint(1,4)):
            connects.append(points[randint(1, len(points) - 1)])
            add_connect(p,connects)
    #Generate random Coordinates
    for p in points:
        long = uniform(115,118)
        lat = uniform(30,47)
        coord = (round(lat,3),round(long,3))
        coords[p] = coord

    #Starting Router Addresses          #Start testing here,
    ROUTES = '192.168.0.0'
    IDS = 0

    pdcs = 1
    pmus = 2

    #Regions
    for i, p in enumerate(points):
        route = ip_change(ROUTES,2,str(i))
        id = str(i)
        ip = ip_change(route,3,i)
        params = dict(ID=id,router=route,IP=ip,region=p, name=p,type='OP', coords=coords[p],
                      connects=regions[p],num_pmus=pmus,num_pdcs=pdcs)
        OPS.append(Region(params))

    #PDCS
    for i, p in enumerate(OPS):
        for n in range(0,p.num_pdcs):
            crange = (p.coords[0]-1,p.coords[0]+1,p.coords[1]-1,p.coords[1]+1)
            name = p.region + '_PDC_' + str(n)
            params = dict(RegNode=p,region=p.name, typen='PDC',name=name,coords=rand_coords(crange))
            PDCS.append(Node(params))
            p.nodes['PDC'].append(PDCS[-1])
            p.ip_list.append(PDCS[-1].IP)

    #PMUS
    for i, p in enumerate(OPS):
        for n in range(0,p.num_pmus):
            crange = (p.coords[0]-1,p.coords[0]+1,p.coords[1]-1,p.coords[1]+1)
            name = p.region + '_PMU_' + str(n)
            params = dict(RegNode=p,region=p.name,typen='PMU', name=name,coords=rand_coords(crange))
            PMUS.append(Node(params))
            p.nodes['PMU'].append(PMUS[-1])
            p.ip_list.append(PMUS[-1].IP)

    # for i in OPS:
    #     print('{} {} {} {} {} {}'.format(i.ID,i.router,i.IP,i.region,i.type,i.coords))
    # for key, val in regions.items():
    #     print('Region: {} ,  Connects {}'.format(key,val))
    opts = dict(Regions = OPS, PDCS = PDCS, PMUS = PMUS)
    topo = LTBnet(opts)
    # c2 = RemoteController('c2', ip='127.0.0.1', port=6633)
    # net = Mininet(topo=topo,controller=c2)
    net = Mininet(topo=topo)
    net.start()
    CLI(net)
    net.stop()