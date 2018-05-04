"""Network Object for storing network configurations and creating a Network Dictionary for
JSON format streaming on the LTB network"""

from region import Region
from node import Node
from minitop_WAN import LTBnet

import os,sys
import logging
logging.basicConfig(level=logging.ERROR)


class NetConfig():
    def __init__(self,name='',configfile='',path=''):

        self.configfile = os.path.join(path,configfile)
        if not os.path.exists(self.configfile):
            logging.error('Path <{}> does not exist.'.format(self.configfile))
            sys.exit(1)

        self.name = name
        self.path = path
        self.regs = self.get_regions()
        self.ConParams = dict()     #Contains Network Configuratio Info, and Regions data
        self.Regions = dict()       #Contains Key to all region information
        self.Coords = dict()        #Coords for each Node in Region
        self.nRegions = 0
        self.Nodes = dict()         #Nodes By region
        self.nNodes = 0
        self.Routers = {reg : {} for reg in self.regs}      #Routers by Region
        self.nRouters = {reg : 0 for reg in self.regs}
        self.PMUS = dict()          #PMUS by Region
        self.nPMUS = {reg : 0 for reg in self.regs}
        self.PDCS = dict()          #PDCS by region
        self.nPDCS = {reg : 0 for reg in self.regs}
        self.Switches = {reg : {} for reg in self.regs}    #Switches by Region
        self.nSwitches = {reg : 0 for reg in self.regs}
        self.Connects = {reg : [] for reg in self.regs}      #Connections by Region
        self.InterConnects = []

    def get_regions(self):
        """Get Region Names first to initialize PMU,PDC,Routers and Switch dicts"""
        regs = ['AESO', 'BCTC', 'BPA', 'VRCC', 'IPCO', 'LRCC', 'WAPA', 'CAIS', 'PGE', 'SCE', \
                  'LADW', 'SDGE', 'APS', 'SRP', 'PNM']
        return regs

    def set_config(self):
        """Creates Network Param File for streaming network config information in JSON format"""
        self.Regions['Total_Regions'] = self.nRegions
        self.Regions['Network_Name'] = self.name
        for reg in self.regs:


            self.Regions[reg] = {'PMUS': self.PMUS[reg],
                                 'PDCS': self.PDCS[reg],
                                 'Routers': self.Routers[reg],
                                 'Switches': self.Switches[reg],
                                 'Connects': self.Connects[reg],
                                 'nPMUS': self.nPMUS[reg],
                                 'nPDCS': self.nPDCS[reg],
                                 'nRouters': self.nRouters[reg],
                                 'nSwitches': self.nSwitches[reg]}
        self.ConParams['InterConnects'] = self.InterConnects
        self.ConParams['Regions'] = self.Regions