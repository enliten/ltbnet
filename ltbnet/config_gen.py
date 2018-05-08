"""Config_gen can be used to generate a connection list for given regions.
It can also be used to specify coordinate points and mac addresses for consistency in generating the mininet Network"""



# List of nearest cities to operator regions. The coordinate location for region centers is based on this list.
#Alberta,CAN -British Columbia,CAN - Bonneville,WA-Vancouver,WA -Boise,ID- Boulder,CO -Lakewood,CO
#Folsom,CA -Sacramento,CA, Rosemead,CA- Los Angeles,C - San Diego,CA-Glendale,AZ? -Phoenix,AZ, Albequerque,NM

import csv

points = ['AESO', 'BCTC', 'BPA', 'VRCC', 'IPCO', 'LRCC' , 'WAPA', 'CAIS', 'PGE', 'SCE', \
          'LADW', 'SDGE', 'APS', 'SRP', 'PNM']

pdcdata = dict()    # key: name, {keys: name,ID,coords,router}
pmudata = dict()    #keys: pdcname,ID,coords,ip,level

regions = {'AESO':['BCTC'], 'BCTC': ['AESO','VRCC'], 'BPA':['VRCC'], 'VRCC':['LRCC','BPA','IPCO','BCTC','CAIS'],
           'IPCO':['VRCC'], 'LRCC':['VRCC','WAPA'] , 'WAPA': ['LRCC'], 'CAIS': ['VRCC','PGE','SCE'],
           'PGE':['CAIS'], 'SCE': ['CAIS','LADW','SDGE','APS'], 'LADW': ['SCE'], 'SDGE': ['SCE'],
           'APS': ['SCE','SRP'], 'SRP': ['APS','PNM'], 'PNM': ['SRP']}
coords ={'AESO':(53.93,-116.57) , 'BCTC': (57.72,-127.64), 'BPA' : (45.6373,-121.97), 'VRCC': (45.63,-122.67),
         'IPCO': (43.61,-116.21), 'LRCC':(40.015,-105.27) , 'WAPA':(39.704,-105.081), 'CAIS':(38.678,-121.176),
         'PGE': (38.581,-121.494), 'SCE': (34.08,-118.07), 'LADW': (34.052,-118.243), 'SDGE': (32.715,-117.161),
         'APS': (33.538,-112.186), 'SRP': (33.44,-112.074), 'PNM': (35.084,-106.65)}
macs = {'AESO':'7a:43:4f:ca:0d:23',
        'BCTC':'92:53:a7:1e:98:55',
        'BPA':'7e:79:01:74:7b:f1',
        'VRCC':'72:a0:ec:58:b4:64',
        'IPCO':'6a:3f:cc:21:bb:01',
        'LRCC':'16:d7:c3:d2:9c:34',
        'WAPA':'b6:5f:39:75:f5:b9',
        'CAIS':'52:31:94:6c:12:6c',
        'PGE':'be:dd:b5:a9:5e:30',
        'SCE':'72:5e:30:03:ac:dd',
        'LADW':'f6:5c:95:75:da:76',
        'SDGE':'aa:a4:86:81:48:1e',
        'APS':'f6:e7:cd:a9:96:7f',
        'SRP':'72:83:f2:39:1c:5b',
        'PNM':'42:49:42:ac:7d:6e',
        }
name = ['my_network']
Headers = ['Type','Region','Name','Longitude', 'Latitude', 'Connections','MAC']
with open('config.csv','wb') as fout:
    writer = csv.writer(fout)
    writer.writerow(['Name='+name[0]])
    writer.writerow(Headers)
    for reg in points:
        dat = ['Region',reg,reg,coords[reg][0],coords[reg][1],' '.join(regions[reg]),macs[reg]]
        writer.writerow(dat)