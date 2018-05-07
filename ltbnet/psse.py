"""PSS/E 32 file parser for ePhasorsim Models"""
import logging
import os
import re
from basetop_LAN import haversine_d


NEVER = 60
CRITICAL = 50
ERROR = 40
WARNING = 30
INFO = 20
DEBUG = 10
ALWAYS = 0
EMPTY = 0
pi = 3.14159265358973
jpi2 = 1.5707963267948966j
rad2deg = 57.295779513082323
deg2rad = 0.017453292519943


def testlines(fid):
    """Check the raw file for frequency base"""
    first = fid.readline()
    first = first.strip().split('/')
    first = first[0].split(',')
    if float(first[5]) == 50.0 or float(first[5]) == 60.0:
        return True
    else:
        return False


def read(file):
    """read PSS/E RAW file v32 format"""

    blocks = ['bus', 'load', 'fshunt', 'gen', 'branch', 'transf', 'area',
              'twotermdc', 'vscdc', 'impedcorr', 'mtdc', 'msline', 'zone',
              'interarea', 'owner', 'facts', 'swshunt', 'gne', 'Q']
    nol = [1, 1, 1, 1, 1, 4, 1,
           0, 0, 0, 0, 0, 1,
           0, 1, 0, 0, 0, 0]
    rawd = re.compile('rawd\d\d')

    retval = True
    version = 0
    b = 0  # current block index
    raw = {}
    for item in blocks:
        raw[item] = []

    data = []
    mdata = []  # multi-line data
    mline = 0  # line counter for multi-line models

    # parse file into raw with to_number conversions
    fid = open(file, 'r')
    for num, line in enumerate(fid.readlines()):
        line = line.strip()
        if num == 0:  # get basemva and frequency
            data = line.split('/')[0]
            data = data.split(',')

            mva = float(data[1])
            freq = float(data[5])
            version = int(data[2])

            if not version:
                version = int(rawd.search(line).group(0).strip('rawd'))
            if version < 32 or version > 33:
                logging.warning('RAW file version is not 32 or 33. Error may occur.')
            continue
        elif num == 1:  # store the case info line
            logging.info(line)
            continue
        elif num == 2:
            continue
        elif num >= 3:
            if line[0:2] == '0 ' or line[0:3] == ' 0 ':  # end of block
                b += 1
                continue
            elif line[0] is 'Q':  # end of file
                break
            data = line.split(',')

        data = [to_number(item) for item in data]
        mdata.append(data)
        mline += 1
        if mline == nol[b]:
            if nol[b] == 1:
                mdata = mdata[0]
            raw[blocks[b]].append(mdata)
            mdata = []
            mline = 0
    fid.close()

    # add device elements params and add to PSAT formatted dictionary
    PMU = {}
    for data in raw['bus']:
        """version 32:
          0,   1,      2,     3,    4,   5,  6,   7,  8,   9,           10
          ID, NAME, BasekV, Type, Area Zone Owner Va, Vm,  latitude     longitude
        """
        idx = data[0]
        ty = data[3]
        angle = data[8]
        try:
            lat = data[9]
        except:
            logging.error('<No Coordinates in .raw file>')

        else:
            param = {
                     'Name': data[1],
                     'AreaNum': data[4],
                     'Region' : "",
                     'Coords': (data[9],data[10])
                     }
        PMU[idx] = param

    return PMU

def knn_reg(PMU,regcoords):
    """Assigns Area to Closest Regions Coordinates"""
    distance = 1000000000000
    tmpreg = ""
    dhold = 0
    for id, info in PMU.items():
        for region in regcoords.keys():
            _, dhold = haversine_d(PMU[id]['Coords'],regcoords[region])
            if dhold < distance:
                distance = dhold
                tmpreg = region
        PMU[id]['Region'] = tmpreg

    return PMU

def to_number(s):
    """Convert a string to a number. If not successful, return the string without blanks"""
    ret = s
    try:
        ret = float(s)
    except ValueError:
        ret = ret.strip('\'').strip()
        return ret

    try:
        ret = int(s)
    except ValueError:
        pass
    return ret



