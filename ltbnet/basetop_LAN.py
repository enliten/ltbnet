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
import psse
import logging
import sys
from math import sin, cos, atan2, sqrt

logging.basicConfig(level=logging.ERROR)

pi = 3.14159265358973
jpi2 = 1.5707963267948966j
rad2deg = 57.295779513082323
deg2rad = 0.017453292519943
R = 6371000         #Radius of Earth
c = 299792458       #Speed of light


# setLogLevel('info')

# CEPD00655 ethernet ports 1 and 2
# hostports = ['enp4s0f0', 'enp4s0f1']
# switchnames = ['s1', 's2']
# portsw = {1: ('enp4s0f0', 's1'), 2: ('enp4s0f1', 's2')}


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


if __name__ == '__main__':
    OPS = []
    PDCS = []
    PMUS = []

    #Starting Router Addresses          #Start testing here,
    ROUTES = '192.168.1.1'
    IDS = 0


    pdcs = 1
    pmus = 0
    #Get PMU Data from config file, add data from RAW file and append to new file if need be
    config = NetConfig(name='test181',configfile='config.csv',raw='Curent02_final_ConstZCoords.raw',path='/home/network_em/PycharmProjects/ltbnet/ltbnet/')



    #Regions
    gate = 2
    sws = 2 #Number of switches per region  ( Should be specified in Config File)
    #There are no routers in this implementation. Every node is in same subnet
    ips = 2     #IP addresses start at 192.168.1.2, then every node increments as 192.168.1.n (where n is number of nodes + 2
    for i, reg in enumerate(config.regs):
        route = ip_change(ROUTES,2,str(gate))
        id = str(gate)
        ip = ip_change(ROUTES,3,ips)
        ips += 1

        params = dict(ID=id,router=route,IP=ip,region=reg, name=reg,type='OP', coords=config.Coords[reg],
                      connects=config.Connects[reg],MAC=config.Macs[reg],num_pmus=pmus,num_pdcs=pdcs)
        OPS.append(Region(params))
        OPS[-1].num_sws = sws
        config.Regions[reg].update({'Gateway': ip})

        # PDCS
        reg = OPS[-1]
        # print("PDCS")
        tmppd = {}
        for n in range(0,reg.num_pdcs):
            #TODO: ADD PDCS To config file. Currently adding 1 for each region.Not defined in config file
            # crange = (reg.coords[0]-1,reg.coords[0]+1,reg.coords[1]-1,reg.coords[1]+1)
            name = reg.region + 'PDC' + str(n)
            params = dict(RegNode=reg,region=reg.name, typen='PDC',name=name,coords=config.Coords[reg.name])
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
        if reg.name not in config.PMUS.keys():
            continue
        else:
            for pmu in config.PMUS[reg.name]:
                params = dict(RegNode=reg,region=reg.name,typen='PMU', name=pmu,coords=config.PMUS[reg.name][pmu]['Coords'])
                PMUS.append(Node(params))
                reg.nodes['PMU'].append(PMUS[-1])
                PMUS[-1].IP = ip_change(ROUTES,3,ips)
                ips += 1
                reg.ip_list.append(PMUS[-1].IP)
                config.PMUS[reg.name][pmu].update({'IP': PMUS[-1].IP})
                config.nPMUS[reg.name] += 1

        # config.PMUS[reg.name] = tmppmu
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