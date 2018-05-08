"""Network Object for storing network configurations and creating a Network Dictionary for
JSON format streaming on the LTB network"""

from region import Region
from node import Node
from minitop_WAN import LTBnet
import psse


import os,sys
import logging
import csv
logging.basicConfig(level=logging.ERROR)


class NetConfig():
    def __init__(self,name='',configfile='',raw='',path=''):

        self.configfile = os.path.join(path,configfile)
        if not os.path.exists(self.configfile):
            logging.error('Path <{}> does not exist.'.format(self.configfile))
            sys.exit(1)
        self.raw = raw
        self.name = name
        self.path = path
        self.Regions = dict()       #Contains Key to all region information
        self.RegCoords = dict()
        self.Coords = dict()        #Coords for each Node in Region
        self.Macs = dict()
        self.regs = self.get_regs()
        self.ConParams = dict()     #Contains Network Configuration Info, and Regions data
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
        self.PMUpsse = {reg: [] for reg in self.Regions.keys()}
        #Initialization Functions
        # self.get_raw()
        self.get_config_file()


    def set_config(self):
        """Creates Network Param File for streaming network config information in JSON format"""
        self.Regions['Total_Regions'] = self.nRegions
        self.Regions['Network_Name'] = self.name
        for reg in self.regs:

            if reg not in self.PMUS.keys():
                logging.warning("No Region PMUS in {}".format(reg))
                self.Regions[reg] = {
                                     'PDCS': self.PDCS[reg],
                                     'Routers': self.Routers[reg],
                                     'Switches': self.Switches[reg],
                                     'Connects': self.Connects[reg],
                                     'nPMUS': self.nPMUS[reg],
                                     'nPDCS': self.nPDCS[reg],
                                     'nRouters': self.nRouters[reg],
                                     'nSwitches': self.nSwitches[reg]}
            else:
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

    def get_regs(self):
        """Initialize Dictionary with region Names"""
        regions = []
        with open(self.configfile,'r') as fin:
            read = csv.reader(fin)
            for row in read:
                if row[0] == 'Region':
                    regions.append(row[1])
                    reg = row[1]
                    self.RegCoords[reg] = [float(row[3]), float(row[4])]

        return regions

    def get_config_file(self):
        """Gets Network Data and initialization data from a config file"""
        #TODO:Create and Parse Config File for region Data
        with open(self.configfile,'r') as fin:
            read = csv.reader(fin)
            for row in read:
                if row[0] == 'Region':
                    reg = row[1]
                    coords = [float(row[3]), float(row[4])]
                    self.Coords[reg] = coords
                    self.Connects[reg] = row[5].split(' ')
                    mac = row[6]
                    self.Macs[reg] = mac
                    self.Regions[reg] = {'Coords': coords, 'HW_ADDR': mac}
                if row[0] == 'PMU':
                    reg = row[1]
                    name = row[2]
                    coords = [float(row[3]), float(row[4])]
                    self.Coords[name] = coords
                    mac = row[6]
                    if reg in self.PMUS.keys():
                        self.PMUS[reg].update({name: {'Coords': coords,'HW_ADDR':mac}})
                    else:
                        self.PMUS[reg] = {name: {'Coords': coords,'HW_ADDR':mac}}




    def get_raw(self):
        """Adds Raw PMU data if specified"""

        if os.path.exists(self.path + '/' + self.raw):
            pmudata = psse.read(self.raw)
            pmudata = psse.knn_reg(pmudata, self.RegCoords)
            with open('config.csv', 'a') as fout:
                writer = csv.writer(fout)
                for id in pmudata.keys():
                    dat = ['PMU',pmudata[id]['Region'],pmudata[id]['Name'],pmudata[id]['Coords'][0],pmudata[id]['Coords'][1],'EMPTY','EMPTY']
                    writer.writerow(dat)

        else:
            logging.warning("<No Raw file {} found in path {}. Raw data not added>".format(self.raw,self.path))
