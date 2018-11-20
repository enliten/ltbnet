"""
tinyPDC will connect to pmu_ip:pmu_port and send request
for header message, configuration and eventually
to start sending measurements.
"""

from synchrophasor.pdc import Pdc
from synchrophasor.frame import DataFrame
from multiprocessing import Process, Pipe, Queue
import time

import logging
from andes_addon.dime import Dime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')

fh = logging.FileHandler('/var/log/minipdc.log')
fh.setFormatter(formatter)
logger.addHandler(fh)

dimec = Dime('ISLANDING', 'tcp://192.168.1.200:5000')

try:
    dimec.exit()
except:
    pass

dimec.start()

iplist = []
iplist.append('192.168.1.1')
iplist.append('192.168.1.19')
iplist.append('192.168.1.34')
iplist.append('192.168.1.55')
iplist.append('192.168.1.73')
iplist.append('192.168.1.91')
iplist.append('192.168.1.109')
iplist.append('192.168.1.127')
iplist.append('192.168.1.145')
iplist.append('192.168.1.163')
npmu = len(iplist)

# ISLANDING event line trips
event = {'id': [143, 146, 135],
         'name': ['Line', 'Line', 'Line'],
         'time': [-1, -1, -1],
         'duration': [0, 0, 0],
         'action': [0, 0, 0]
         }

islanding_delay = 7

if __name__ == "__main__":
    pdc = dict()
    header = dict()
    config = dict()
    freq = dict()

    # while True:
    #     dimec.send_var('sim', 'Event', event)


    for idx, item in enumerate(iplist):
        pmu_idx = int(iplist[idx].split('.')[3])

        pdc[idx] = Pdc(pdc_id=pmu_idx,
                       pmu_ip=iplist[idx],
                       pmu_port=1410)

        pdc[idx].logger.setLevel("INFO")

    for idx, item in pdc.items():  # each item is a PDC

        item.run()   # Connect to PMU

        header[idx] = item.get_header()
        config[idx] = item.get_config()

    for idx, item in pdc.items():  # each item is a PDC
        item.start()  # Request to start sending measurements

    # create result queues

    result_queue = [Queue() for x in range(npmu)]

    # start data acquisition processes
    result_dict = {}
    time_detect = 0
    detected = False
    islanded = False

    print('PDC-based system separation control geared up')

    while True:
        # retrieve all measurements from the PDCs
        for idx, item in pdc.items():
            item.get_msg(result_queue[idx])

        # for each PDC, retrieve the frequency
        for idx, item in enumerate(result_queue):
            result_dict[idx] = item.get()
            if result_dict[idx] is None:
                freq[idx] = 60  # TODO: fix
                continue

            measurements = result_dict[idx].get_measurements()

            if isinstance(measurements, dict):
                freq[idx] = (measurements['measurements'][0]['frequency']-60) * 1000
            else:
                print('Unknown measurement type {}, continue'.format(type(measurements)))
                continue

        # detect frequency deviation

        if (not detected) and (not islanded):

            freq_diff = (max(freq.values())-min(freq.values()))
            print('Frequency difference = {}'.format(freq_diff))

            if freq_diff >= 0.4:
                # record the *initial* time when frequency divergence is detected
                detected = True
                time_detect = time.time()
                print('--> Frequency divergence detected. Islanding will happen in {}'.format(islanding_delay))

        # impose a delay before islanding by comparing time() and time_detect
        elif detected and (not islanded):
            if (time.time() - time_detect >= islanding_delay):
                dimec.send_var('sim', 'Event', event)
                print('--> Islanding initiated!!!')
                islanded = True
