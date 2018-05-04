"""Base topology for the Regional operators in a LAN network.  Starting with randomly created network, to
allow for easy transistion from general topology to a defined topology.

Currently contains hardcoded regions,and coordinates as well as fake coordinates for PMU and PDCS.
Once a config file is created, those items can be removed."""

# TODO: Create config file, and import network topology data from PSS/E file. Need to create PMU at each bus.


from random import randint,random
from random import uniform

from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import OVSKernelSwitch,UserSwitch, Controller, RemoteController
from mininet.log import setLogLevel, info, error
from mininet.link import Link,TCLink

from region import Region
from node import Node
from minitop_LAN import LTBnet
from network import NetConfig

import logging
logging.basicConfig(level=logging.ERROR)

# List of nearest cities to operator regions. The coordinate location for region centers is based on this list.
#Alberta,CAN -British Columbia,CAN - Bonneville,WA-Vancouver,WA -Boise,ID- Boulder,CO -Lakewood,CO
#Folsom,CA -Sacramento,CA, Rosemead,CA- Los Angeles,C - San Diego,CA-Glendale,AZ? -Phoenix,AZ, Albequerque,NM
points = ['AESO', 'BCTC', 'BPA', 'VRCC', 'IPCO', 'LRCC' , 'WAPA', 'CAIS', 'PGE', 'SCE', \
          'LADW', 'SDGE', 'APS', 'SRP', 'PNM']

pdcdata = dict()    # key: name, {keys: name,ID,coords,router}
pmudata = dict()    #keys: pdcname,ID,coords,ip,level

regions = {'AESO':['BCTC'], 'BCTC': ['AESO','VRCC'], 'BPA':['VRCC'], 'VRCC':['LRCC','BPA','IPCO','BCTC','CAIS'],
           'IPCO':['VRCC'], 'LRCC':['VRCC','WAPA'] , 'WAPA': ['LRCC'], 'CAIS': ['VRCC','PGE','SCE'],
           'PGE':['CAIS'], 'SCE': ['CAIS','LADW','SDGE','APS'], 'LADW': ['SCE'], 'SDGE': ['SCE'],
           'APS': ['SCE','SRP'], 'SRP': ['APS','PNM'], 'PNM': ['SRP']}
coords ={'AESO':(53.93,116.57) , 'BCTC': (57.72,127.64), 'BPA' : (45.6373,121.97), 'VRCC': (45.63,122.67),
         'IPCO': (43.61,116.21), 'LRCC':(40.015,105.27) , 'WAPA':(39.704,105.081), 'CAIS':(38.678,121.176),
         'PGE': (38.581,121.494), 'SCE': (34.08,118.07), 'LADW': (34.052,118.243), 'SDGE': (32.715,117.161),
         'APS': (33.538,112.186), 'SRP': (33.44,112.074), 'PNM': (35.084,106.65)}
macs = ['7a:43:4f:ca:0d:23', #AESO
        '92:53:a7:1e:98:55', #BCTC
        '7e:79:01:74:7b:f1', #BPA
        '72:a0:ec:58:b4:64', #VRCC
        '6a:3f:cc:21:bb:01', #IPCO
        '16:d7:c3:d2:9c:34', #LRCC
        'b6:5f:39:75:f5:b9', #WAPA
        '52:31:94:6c:12:6c', #CAISO
        'be:dd:b5:a9:5e:30', #PG&E
        '72:5e:30:03:ac:dd', #SCE
        'f6:5c:95:75:da:76', #LADWP
        'aa:a4:86:81:48:1e', #SDGE
        'f6:e7:cd:a9:96:7f', #APS
        '72:83:f2:39:1c:5b', #SRP
        '42:49:42:ac:7d:6e', #PNM
        ]

setLogLevel('info')

# CEPD00655 ethernet ports 1 and 2
# hostports = ['enp4s0f0', 'enp4s0f1']
# switchnames = ['s1', 's2']
# portsw = {1: ('enp4s0f0', 's1'), 2: ('enp4s0f1', 's2')}

# Default line setting configurations
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


# The next 4 functions are for a psuedo topology and con be removed when a config file is created.
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

def hw_change(addr,sect,num):
    """Changes hw address section 0-5 to num.
    num should be no more than 2 digits"""
    if num < 10:
        ldigs = addr.split(':')
        ldigs[sect] = "0" + str(num)
        newhw = ':'.join(ldigs)
    elif num < 99 and num >= 10:
        ldigs = addr.split(':')
        ldigs[sect] = str(num)
        newhw = ':'.join(ldigs)
    return newhw

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
    config = NetConfig(name='test181',configfile='testconfig.py',path='/home/network_em/mininet/custom/')

    #Starting Router Addresses          #Start testing here,
    ROUTES = '192.168.1.1'
    IDS = 0

    pdcs = 1
    pmus = 2

    #Regions
    gate = 2
    sws = 2 #Number of switches per region  ( Should be specified in Config File)
    #There are no routers in this implementation. Every node is in same subnet
    ips = 2     #IP addresses start at 192.168.1.2, then every node increments as 192.168.1.n (where n is number of nodes + 2
    for i, p in enumerate(points):
        route = ip_change(ROUTES,2,str(gate))
        id = str(gate)
        ip = ip_change(ROUTES,3,ips)
        ips += 1
        params = dict(ID=id,router=route,IP=ip,region=p, name=p,type='OP', coords=list(coords[p]),
                      connects=regions[p],MAC=macs[i],num_pmus=pmus,num_pdcs=pdcs)
        OPS.append(Region(params))
        OPS[-1].num_sws = sws
        config.Regions[p] = {'Coords': list(coords[p]),
                             'HW_ADDR': macs[i],
                             'Gateway': ip}

        config.nRegions = i

        # PDCS
        reg = OPS[-1]
        # print("PDCS")
        tmppd = {}
        for n in range(0,reg.num_pdcs):
            crange = (reg.coords[0]-1,reg.coords[0]+1,reg.coords[1]-1,reg.coords[1]+1)
            name = reg.region + '_PDC_' + str(n)
            params = dict(RegNode=reg,region=reg.name, typen='PDC',name=name,coords=rand_coords(crange))
            PDCS.append(Node(params))
            reg.nodes['PDC'].append(PDCS[-1])
            PDCS[-1].IP = ip_change(ROUTES,3,ips)
            ips += 1
            reg.ip_list.append(PDCS[-1].IP)
            tmppd[name] = {'Coords': list(PDCS[-1].coords), 'HW_ADDR': 0, 'IP': PDCS[-1].IP}
            config.nPDCS[reg.name] += 1
        config.PDCS[reg.name] = tmppd

        #PMUS
        tmppmu = {}
        for n in range(0,reg.num_pmus):
            crange = (reg.coords[0]-1,reg.coords[0]+1,reg.coords[1]-1,reg.coords[1]+1)
            name = reg.region + '_PMU_' + str(n)
            params = dict(RegNode=reg,region=reg.name,typen='PMU', name=name,coords=rand_coords(crange))
            PMUS.append(Node(params))
            reg.nodes['PMU'].append(PMUS[-1])
            PMUS[-1].IP = ip_change(ROUTES,3,ips)
            ips += 1
            reg.ip_list.append(PMUS[-1].IP)
            tmppmu[name] = {'Coords': list(PMUS[-1].coords), 'HW_ADDR': 0, 'IP': PMUS[-1].IP}
            config.nPMUS[reg.name] += 1

        config.PMUS[reg.name] = tmppmu
        gate = gate + reg.num_sws

    opts = dict(Regions = OPS, PDCS = PDCS, PMUS = PMUS)
    topo = LTBnet(opts,config=config,lan=True)
    # c2 = RemoteController('c2', ip='127.0.0.1',port=6633)
    # net = Mininet(topo=topo,controller=c2,link=TCLink,switch=OVSKernelSwitch)
    topo.config.set_config()
    net = Mininet(topo=topo)

    # net = Mininet(topo=topo)

    net.start()

    CLI(net)
    net.stop()